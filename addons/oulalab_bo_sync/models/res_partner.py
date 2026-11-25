from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re
import unicodedata
from odoo import api, fields, models


DUMMY_PHONES = {'00000000', '56900000000', '900000000'}


def normalize_text(value):
    if not value:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(value))
    ascii_str = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', ascii_str).strip().lower()


def parse_bo_iso_datetime(dt_str):
    if not dt_str:
        return False, 0
    raw = str(dt_str).strip()
    if not raw:
        return False, 0
    try:
        iso_val = raw.replace('Z', '+00:00')
        dt_aware = datetime.fromisoformat(iso_val)
        if dt_aware.tzinfo is None:
            dt_aware = dt_aware.replace(tzinfo=timezone.utc)
        dt_utc_naive = dt_aware.astimezone(timezone.utc).replace(tzinfo=None)
        dt_santiago = dt_aware.astimezone(ZoneInfo('America/Santiago'))
        return dt_utc_naive, dt_santiago.hour
    except ValueError:
        return False, 0


def is_valid_phone(phone_str):
    if not phone_str:
        return False
    digits = re.sub(r'\D', '', str(phone_str))
    if len(digits) < 8:
        return False
    return digits not in DUMMY_PHONES and digits[-8:] != '00000000'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_bo_last_sync_at = fields.Datetime(string='Última Sincronización BO', readonly=True, copy=False)
    x_bo_brand_uuid = fields.Char(string='UUID Marca BO', index=True, copy=False)
    x_bo_brand_slug = fields.Char(string='Slug Marca BO', copy=False)

    @api.model
    def _find_bo_partner(self, email=None, phone=None, name=None):
        email_clean = (email or '').strip().lower()
        if email_clean:
            partner = self.search(
                ['|', ('email_normalized', '=', email_clean), ('email', '=ilike', email_clean)],
                limit=1,
            )
            if partner:
                return partner
            if 'x_studio_bo_client_email' in self._fields:
                partner = self.search([('x_studio_bo_client_email', '=ilike', email_clean)], limit=1)
                if partner:
                    return partner

        if is_valid_phone(phone):
            digits = re.sub(r'\D', '', str(phone))[-8:]
            partner = self.search([('phone', 'ilike', digits)], limit=1)
            if partner:
                return partner

        name_clean = (name or '').strip()
        if name_clean:
            partner = self.search([('name', '=ilike', name_clean)], limit=1)
            if partner:
                return partner
            target_norm = normalize_text(name_clean)
            tokens = [t for t in target_norm.split(' ') if len(t) >= 2]
            if tokens:
                candidates = self.search([('name', 'ilike', tokens[0]), ('is_company', '=', False)], limit=40)
                for cand in candidates:
                    cand_norm = normalize_text(cand.name)
                    if cand_norm == target_norm or all(tok in cand_norm.split(' ') for tok in tokens):
                        return cand
                if 'x_studio_bo_client_name' in self._fields:
                    bo_cands = self.search([('x_studio_bo_client_name', 'ilike', tokens[0])], limit=40)
                    for cand in bo_cands:
                        bo_full = normalize_text(f"{cand.x_studio_bo_client_name or ''} {cand.x_studio_bo_client_last_name or ''}")
                        if bo_full == target_norm:
                            return cand
        return self.browse()

    @api.model
    def _filter_existing_fields(self, vals):
        return {k: v for k, v in vals.items() if k in self._fields}

    @api.model
    def upsert_from_bo_brand(self, row, dry_run=False):
        brand_uuid = (row.get('Id') or row.get('ID') or '').strip()
        name = (row.get('Nombre') or '').strip()
        slug = (row.get('Slug') or '').strip()
        desc = (row.get('Descripción') or '').strip()

        if not name:
            return 'skipped', self.browse(), 'Fila de marca sin Nombre.'

        domain = [('name', '=ilike', name)]
        if brand_uuid:
            domain = ['|', ('x_bo_brand_uuid', '=', brand_uuid)] + domain
        partner = self.search(domain, limit=1)

        Tag = self.env['product.tag']
        if not dry_run and not Tag.search([('name', '=ilike', name)], limit=1):
            Tag.create({'name': name})

        vals = {
            'name': name,
            'company_type': 'company',
            'is_company': True,
            'supplier_rank': 1,
            'x_bo_brand_slug': slug or False,
            'x_bo_last_sync_at': fields.Datetime.now(),
        }
        if brand_uuid:
            vals['x_bo_brand_uuid'] = brand_uuid
        if desc:
            vals['comment'] = desc

        if partner:
            if not dry_run:
                partner.write(self._filter_existing_fields(vals))
            return 'updated', partner, f"Marca actualizada ({name})"

        if not dry_run:
            partner = self.create(self._filter_existing_fields(vals))
        return 'created', partner, f"Marca creada ({name})"

    @api.model
    def upsert_from_bo_customer(self, row, dry_run=False):
        first_name = (row.get('Nombre') or '').strip()
        last_name = (row.get('Apellido') or '').strip()
        email = (row.get('Email') or '').strip().lower()
        phone_raw = (row.get('Teléfono') or '').strip()
        bo_commune = (row.get('Comuna') or '').strip()
        app_address = (row.get('Dirección app') or '').strip()
        active_raw = str(row.get('Activo', '')).strip().lower()
        bo_active = active_raw in ('true', '1', 'si', 'sí', 'yes', 'activo')
        created_at_str = (row.get('Fecha de alta') or '').strip()

        if not email and not first_name and not last_name:
            return 'skipped', self.browse(), 'Fila sin email ni nombre.'

        full_name = f"{first_name} {last_name}".strip()
        if full_name and full_name == full_name.lower():
            full_name = full_name.title()
        if not full_name:
            full_name = email

        commune_info = self.env['oulalab.bo.commune.map'].resolve_commune(bo_commune)
        dt_alta, hora_alta = parse_bo_iso_datetime(created_at_str)
        chile = self.env.ref('base.cl', raise_if_not_found=False)

        partner = self._find_bo_partner(email=email, phone=phone_raw, name=full_name)

        vals = {
            'is_oulalab_member': True,
            'x_studio_bo_active': bo_active,
            'x_studio_bo_client_email': email or False,
            'x_studio_bo_client_name': first_name or False,
            'x_studio_bo_client_last_name': last_name or False,
            'x_studio_bo_client_mobile': phone_raw or False,
            'x_studio_client_comuna_id': bo_commune or False,
            'x_bo_last_sync_at': fields.Datetime.now(),
        }
        if dt_alta:
            vals['x_studio_fecha_y_hora_de_alta'] = dt_alta
            vals['x_studio_hora_de_alta'] = hora_alta
        if commune_info['city']:
            vals['city'] = commune_info['city']
        if commune_info['state_id']:
            vals['state_id'] = commune_info['state_id']
        if app_address:
            vals['street'] = app_address

        if partner:
            if email and not partner.email:
                vals['email'] = email
            if is_valid_phone(phone_raw) and not is_valid_phone(partner.phone):
                vals['phone'] = phone_raw
            if not partner.country_id and chile:
                vals['country_id'] = chile.id
            filtered_vals = self._filter_existing_fields(vals)
            if not dry_run:
                partner.write(filtered_vals)
            return 'updated', partner, f"Cliente actualizado ({email or full_name})"

        create_vals = {
            'name': full_name,
            'company_type': 'person',
            'is_company': False,
            'customer_rank': 1,
            'email': email or False,
            'phone': phone_raw if is_valid_phone(phone_raw) else False,
            'country_id': chile.id if chile else False,
            'lang': 'es_CL',
            'tz': 'America/Santiago',
            **vals,
        }
        filtered_vals = self._filter_existing_fields(create_vals)
        if not dry_run:
            partner = self.create(filtered_vals)
        return 'created', partner, f"Cliente creado ({email or full_name})"
