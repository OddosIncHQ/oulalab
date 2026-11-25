from odoo import api, fields, models
from .res_partner import parse_bo_iso_datetime, is_valid_phone


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_bo_last_sync_at = fields.Datetime(string='Última Sincronización BO', readonly=True, copy=False)

    @api.model
    def _filter_existing_fields(self, vals):
        return {k: v for k, v in vals.items() if k in self._fields}

    @api.model
    def _get_or_create_tags(self, tag_names):
        Tag = self.env['crm.tag']
        tag_ids = []
        for raw_name in tag_names:
            name = (raw_name or '').strip()
            if not name:
                continue
            tag = Tag.search([('name', '=ilike', name)], limit=1)
            if not tag:
                tag = Tag.create({'name': name})
            tag_ids.append(tag.id)
        return tag_ids

    @api.model
    def _get_or_create_utm_source(self, source_name):
        name = (source_name or '').strip()
        if not name:
            return False
        Source = self.env['utm.source']
        src = Source.search([('name', '=ilike', name)], limit=1)
        if not src:
            src = Source.create({'name': name})
        return src.id

    @api.model
    def upsert_from_bo_lead(self, row, auto_create_partner=False, dry_run=False):
        name_raw = (row.get('Nombre') or '').strip()
        email = (row.get('Email') or '').strip().lower()
        phone_raw = (row.get('Teléfono') or '').strip()
        bo_commune = (row.get('Comuna') or '').strip()
        origin_raw = (row.get('Origen') or '').strip()
        status_raw = (row.get('Estado') or 'new').strip()
        created_at_str = (row.get('Fecha de alta') or '').strip()

        if not email and not name_raw:
            return 'skipped', self.browse(), 'Fila de lead sin email ni nombre.'

        commune_info = self.env['oulalab.bo.commune.map'].resolve_commune(bo_commune)
        stage = self.env['oulalab.bo.stage.map'].resolve_stage(
            status_raw, in_coverage=commune_info['in_coverage']
        )
        dt_alta, _ = parse_bo_iso_datetime(created_at_str)
        chile = self.env.ref('base.cl', raise_if_not_found=False)

        Partner = self.env['res.partner']
        partner = Partner._find_bo_partner(email=email, phone=phone_raw, name=name_raw)
        if not partner and auto_create_partner and not dry_run:
            partner = Partner.create({
                'name': name_raw or email,
                'email': email or False,
                'phone': phone_raw if is_valid_phone(phone_raw) else False,
                'city': commune_info['city'],
                'country_id': chile.id if chile else False,
                'company_type': 'person',
            })

        lead = self.browse()
        if email:
            lead = self.search(
                ['|', ('email_normalized', '=', email), ('email_from', '=ilike', email)],
                order='id desc',
                limit=1,
            )
        if not lead and partner:
            lead = self.search([('partner_id', '=', partner.id)], order='id desc', limit=1)

        tag_ids = self._get_or_create_tags([origin_raw, status_raw]) if not dry_run else []
        source_id = self._get_or_create_utm_source(origin_raw) if not dry_run else False

        vals = {
            'contact_name': name_raw or False,
            'email_from': email or False,
            'city': commune_info['city'],
            'x_studio_tipo_de_lead': origin_raw or 'BackOffice',
            'x_studio_fecha_ultima_actualizacion_1': fields.Date.context_today(self),
            'x_bo_last_sync_at': fields.Datetime.now(),
        }
        if is_valid_phone(phone_raw):
            vals['phone'] = phone_raw
        if partner:
            vals['partner_id'] = partner.id
        if commune_info['state_id']:
            vals['state_id'] = commune_info['state_id']
        if dt_alta:
            vals['x_studio_fecha_de_contacto'] = dt_alta.date()
        if source_id:
            vals['source_id'] = source_id
        if tag_ids:
            vals['tag_ids'] = [(4, tid) for tid in tag_ids]

        if lead:
            if stage and lead.stage_id.name in (False, 'Prospectos', 'Nuevo', 'New'):
                vals['stage_id'] = stage.id
            filtered_vals = self._filter_existing_fields(vals)
            if not dry_run:
                lead.write(filtered_vals)
            return 'updated', lead, f"Lead actualizado ({email or name_raw})"

        create_vals = {
            'name': name_raw or email,
            'type': 'opportunity',
            'country_id': chile.id if chile else False,
            'stage_id': stage.id if stage else False,
            **vals,
        }
        filtered_vals = self._filter_existing_fields(create_vals)
        if not dry_run:
            lead = self.create(filtered_vals)
        return 'created', lead, f"Lead creado ({email or name_raw})"
