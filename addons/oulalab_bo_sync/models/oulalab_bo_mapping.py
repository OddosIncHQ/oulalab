from odoo import api, fields, models


class OulalabBoRentalSequence(models.Model):
    _name = 'oulalab.bo.rental.sequence'
    _description = 'Secuencias Parametrizables de Órdenes de Alquiler Asociadas a Suscripción'
    _order = 'sequence asc, id asc'

    sequence = fields.Integer(string='Prioridad', default=10)
    name = fields.Char(string='Descripción', required=True, help='Ej: Órdenes de Alquiler (RO) o Salidas STKOUT')
    prefix = fields.Char(
        string='Prefijo de Referencia',
        required=True,
        index=True,
        help='Prefijo de sale.order.name que identifica órdenes de alquiler (ej. RO-, STKOUT, STKOUT-).',
    )
    ir_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia Odoo (ir.sequence)',
        help='Opcional: Si se selecciona, al crear una nueva orden de alquiler con esta regla se numerará usando esta secuencia.',
    )
    channel_scope = fields.Selection(
        [
            ('all', 'Todos los Arriendos Asociados a Suscripción'),
            ('subscription', 'Suscripción Recurrente (OULAPLAN)'),
            ('btl', 'Book the Look / Puntual'),
        ],
        string='Ámbito / Canal',
        default='all',
        required=True,
    )
    is_default_creation = fields.Boolean(
        string='Usar al Crear Nuevas Órdenes',
        default=False,
        help='Marca esta secuencia como la predeterminada para generar el número de pedido al crear nuevos arriendos desde el BO.',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('prefix_uniq', 'unique(prefix)', 'El prefijo de secuencia de alquiler debe ser único.'),
    ]

    @api.model
    def get_configured_prefixes(self):
        records = self.search([('active', '=', True)])
        prefixes = [r.prefix.strip() for r in records if r.prefix and r.prefix.strip()]
        return prefixes or ['RO-', 'STKOUT', 'BTL-RO-']

    @api.model
    def build_rental_order_domain(self, extra_domain=None):
        prefixes = self.get_configured_prefixes()
        or_terms = [('is_rental_order', '=', True)]
        for pref in prefixes:
            pattern = pref if pref.endswith('%') else f'{pref}%'
            or_terms.append(('name', '=ilike', pattern))

        if len(or_terms) == 1:
            base_dom = or_terms
        else:
            base_dom = ['|'] * (len(or_terms) - 1) + or_terms

        if extra_domain:
            return base_dom + list(extra_domain)
        return base_dom

    @api.model
    def get_next_order_name(self, channel='subscription'):
        candidates = self.search([
            ('active', '=', True),
            ('is_default_creation', '=', True),
            ('channel_scope', 'in', (channel, 'all')),
        ], order='sequence asc, id asc')
        if not candidates:
            candidates = self.search([
                ('active', '=', True),
                ('ir_sequence_id', '!=', False),
                ('channel_scope', 'in', (channel, 'all')),
            ], order='sequence asc, id asc')

        for rule in candidates:
            if rule.ir_sequence_id:
                return rule.ir_sequence_id.next_by_id()
        return False


class OulalabBoStockConfig(models.Model):
    _name = 'oulalab.bo.stock.config'
    _description = 'Configuración de Ubicaciones de Stock Disponible OulaLab BO'

    name = fields.Char(string='Nombre Configuración', required=True, default='Configuración Inventario OulaLab BO')
    available_location_ids = fields.Many2many(
        'stock.location',
        'oulalab_bo_avail_loc_rel',
        'config_id',
        'location_id',
        string='Ubicaciones de Stock Disponible (para Reserva y in_stock)',
        domain="[('usage', '=', 'internal')]",
    )
    available_location_barcodes = fields.Char(
        string='Códigos de Barras Ubicaciones Disponibles (Fallback)',
        default='STKTCLLTN-LADEHESA,STKTCN-CLTCHS,STKBTL,STKBTL-CLTCHS,BTLPACKING',
    )
    active_fleet_location_ids = fields.Many2many(
        'stock.location',
        'oulalab_bo_fleet_loc_rel',
        'config_id',
        'location_id',
        string='Ubicaciones de Flota Activa (para cálculo de stocked en BO)',
        domain="[('usage', '=', 'internal')]",
    )
    active_fleet_location_barcodes = fields.Char(
        string='Códigos de Barras Flota Activa (Fallback)',
        default='STKTCLLTN-LADEHESA,STKTCN-CLTCHS,STKBTL,STKBTL-CLTCHS,BTLPACKING,RENTALS,RENTTCN,RENTBTL,STKCLTCHS,OPRLCTN,QA01BD001,OUTSSCL,5ASECTRAPENSES,REPAIR,STKDH-PCKNG,PACKBD001,PICKSALEPREPARE,TRANSITPICKUP,REPAIRZONE,SANBD001',
    )
    # Parámetros operativos Book The Look (BTL) desde BO
    btl_reservation_days = fields.Integer(string='BTL: Duración Reserva (días)', default=3)
    btl_prep_days = fields.Integer(string='BTL: Días Preparación Previos', default=6)
    btl_buffer_days = fields.Integer(string='BTL: Buffer Lavandería (días)', default=2)
    btl_checkout_hold_sec = fields.Integer(string='BTL: Hold de Checkout (segundos)', default=300)
    btl_min_advance_days = fields.Integer(string='BTL: Anticipación Mínima (días)', default=0)
    btl_max_advance_days = fields.Integer(string='BTL: Anticipación Máxima (días)', default=45)
    btl_late_fee_daily = fields.Float(string='BTL: Multa Diaria por Atraso (CLP)', default=30000.0)
    btl_extension_fee_daily = fields.Float(string='BTL: Cargo Diario por Extensión (CLP)', default=30000.0)
    btl_delivery_window = fields.Char(string='BTL: Ventana de Entrega')
    btl_return_cutoff_time = fields.Char(string='BTL: Horario Límite de Devolución')

    # Políticas de Arriendo Suscripción (rental-service defaults desde BO)
    sub_default_duration_days = fields.Integer(
        string='Suscripción: Duración por Defecto (días)',
        default=15,
        help='Duración estándar de cada ciclo de arriendo en suscripción (15 días por defecto en rental-service).',
    )
    sub_post_expiry_grace_days = fields.Integer(
        string='Suscripción: Gracia Post-Vencimiento (días)',
        default=7,
        help='Días de gracia posteriores a la fecha de devolución estimada antes de marcar atraso.',
    )
    sub_max_duration_days = fields.Integer(
        string='Suscripción: Duración Máxima (días)',
        default=90,
        help='Tope máximo permitido de permanencia de una prenda en arriendo.',
    )
    cycle_family_rule_ids = fields.One2many(
        'oulalab.bo.cycle.family.rule',
        'config_id',
        string='Reglas de Composición del Ciclo por Familia',
    )
    active = fields.Boolean(default=True)

    @api.model
    def get_active_config(self):
        cfg = self.search([('active', '=', True)], limit=1)
        if not cfg:
            cfg = self.create({'name': 'Configuración Inventario OulaLab BO'})
        cfg._ensure_default_locations()
        return cfg

    def _ensure_default_locations(self):
        Location = self.env['stock.location']
        for rec in self:
            if not rec.available_location_ids and rec.available_location_barcodes:
                codes = [c.strip() for c in rec.available_location_barcodes.split(',') if c.strip()]
                locs = Location.search([('barcode', 'in', codes), ('usage', '=', 'internal')])
                if not locs:
                    locs = Location.search([
                        '|', '|',
                        ('complete_name', 'ilike', 'TCN Garments/Racks'),
                        ('complete_name', 'ilike', 'Garmets BTL'),
                        ('complete_name', 'ilike', 'TCN Accesorios'),
                    ])
                if locs:
                    rec.available_location_ids = [(6, 0, locs.ids)]

            if not rec.active_fleet_location_ids and rec.active_fleet_location_barcodes:
                codes = [c.strip() for c in rec.active_fleet_location_barcodes.split(',') if c.strip()]
                locs = Location.search([('barcode', 'in', codes), ('usage', '=', 'internal')])
                if locs:
                    rec.active_fleet_location_ids = [(6, 0, locs.ids)]

    def get_available_locations_tree(self):
        self.ensure_one()
        self._ensure_default_locations()
        if not self.available_location_ids:
            return self.env['stock.location'].search([('usage', '=', 'internal')])
        return self.env['stock.location'].search([('id', 'child_of', self.available_location_ids.ids)])

    def get_fleet_locations_tree(self):
        self.ensure_one()
        self._ensure_default_locations()
        if not self.active_fleet_location_ids:
            return self.get_available_locations_tree()
        return self.env['stock.location'].search([('id', 'child_of', self.active_fleet_location_ids.ids)])


class OulalabBoCommuneMap(models.Model):
    _name = 'oulalab.bo.commune.map'
    _description = 'Mapeo de Comunas BackOffice OulaLab'
    _order = 'bo_code'

    bo_code = fields.Char(string='Código Comuna BO', required=True, index=True, help='Ej: com-vitacura')
    city_name = fields.Char(string='Ciudad / Comuna Odoo', required=True, help='Ej: Vitacura')
    state_id = fields.Many2one('res.country.state', string='Región', domain="[('country_id.code', '=', 'CL')]")
    in_coverage = fields.Boolean(string='Dentro de Zona de Cobertura', default=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('bo_code_uniq', 'unique(bo_code)', 'El código de comuna BO debe ser único.'),
    ]

    @api.model
    def resolve_commune(self, bo_code):
        if not bo_code:
            return {'city': False, 'state_id': False, 'in_coverage': True}
        code_clean = bo_code.strip().lower()
        mapping = self.search([('bo_code', '=ilike', code_clean)], limit=1)
        if mapping:
            return {
                'city': mapping.city_name,
                'state_id': mapping.state_id.id if mapping.state_id else False,
                'in_coverage': mapping.in_coverage,
            }
        human_name = code_clean.removeprefix('com-').replace('-', ' ').title()
        return {'city': human_name, 'state_id': False, 'in_coverage': True}


class OulalabBoStageMap(models.Model):
    _name = 'oulalab.bo.stage.map'
    _description = 'Mapeo de Estados Lead BO a Etapas CRM'
    _order = 'bo_status'

    bo_status = fields.Char(string='Estado BO', required=True, index=True)
    odoo_stage_id = fields.Many2one('crm.stage', string='Etapa CRM Odoo')
    odoo_stage_name = fields.Char(string='Nombre Etapa CRM (Fallback)')
    out_of_zone_stage_id = fields.Many2one('crm.stage', string='Etapa Fuera de Zona')
    out_of_zone_stage_name = fields.Char(string='Nombre Etapa Fuera de Zona (Fallback)', default='Fuera de Zona')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('bo_status_uniq', 'unique(bo_status)', 'El estado de lead BO debe ser único.'),
    ]

    @api.model
    def resolve_stage(self, bo_status, in_coverage=True):
        Stage = self.env['crm.stage']
        status_clean = (bo_status or 'new').strip().lower()
        mapping = self.search([('bo_status', '=ilike', status_clean)], limit=1)

        if not in_coverage:
            if mapping and mapping.out_of_zone_stage_id:
                return mapping.out_of_zone_stage_id
            stage_name = (mapping.out_of_zone_stage_name if mapping else False) or 'Fuera de Zona'
            ooz_stage = Stage.search([('name', '=ilike', stage_name)], limit=1)
            if ooz_stage:
                return ooz_stage

        if mapping:
            if mapping.odoo_stage_id:
                return mapping.odoo_stage_id
            if mapping.odoo_stage_name:
                stage = Stage.search([('name', '=ilike', mapping.odoo_stage_name)], limit=1)
                if stage:
                    return stage

        return Stage.search([('name', '=ilike', 'Prospectos')], limit=1)


class OulalabBoShowroomMap(models.Model):
    _name = 'oulalab.bo.showroom.map'
    _description = 'Mapeo de Showrooms BO a Tipos de Cita Odoo'
    _order = 'name'

    name = fields.Char(string='Nombre Showroom BO', required=True)
    bo_showroom_uuid = fields.Char(string='UUID Showroom BO', required=True, index=True)
    appointment_type_id = fields.Many2one('appointment.type', string='Tipo de Cita Odoo')
    responsible_user_id = fields.Many2one('res.users', string='Responsable por Defecto')
    default_duration = fields.Float(string='Duración (Horas)', default=0.5)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('bo_showroom_uuid_uniq', 'unique(bo_showroom_uuid)', 'El UUID del Showroom BO debe ser único.'),
    ]

    @api.model
    def resolve_showroom(self, showroom_uuid):
        uuid_clean = (showroom_uuid or '').strip().lower()
        mapping = self.search([('bo_showroom_uuid', '=ilike', uuid_clean)], limit=1)
        appt_type = mapping.appointment_type_id if mapping else False
        if not appt_type and uuid_clean:
            appt_type = self.env['appointment.type'].search(
                [('x_bo_showroom_uuid', '=ilike', uuid_clean)], limit=1
            )
        if not appt_type:
            appt_type = self.env['appointment.type'].search(
                [('name', 'ilike', 'Showroom')], limit=1
            )
        user = (
            (mapping.responsible_user_id if mapping else False)
            or (appt_type.staff_user_ids[:1] if appt_type and appt_type.staff_user_ids else False)
            or self.env.user
        )
        duration = (
            (appt_type.appointment_duration if appt_type and appt_type.appointment_duration else 0.0)
            or (mapping.default_duration if mapping else 0.5)
            or 0.5
        )
        return {
            'mapping': mapping,
            'appointment_type': appt_type,
            'user': user,
            'duration': duration,
        }


class OulalabBoPlanMap(models.Model):
    _name = 'oulalab.bo.plan.map'
    _description = 'Mapeo de Planes de Suscripción y Productos BO'
    _order = 'sequence, bo_plan_code'

    sequence = fields.Integer(string='Orden', default=10)
    bo_plan_uuid = fields.Char(string='ID UUID Plan BO', index=True)
    bo_plan_code = fields.Char(string='Nombre / Código Plan BO', required=True, index=True)
    plan_type = fields.Selection(
        [
            ('subscription_recurring', 'Suscripción Recurrente'),
            ('one_shot_bundle', 'Pack Único (One-Shot Bundle)'),
            ('one_shot_calendar', 'Arriendo Puntual / Book the Look'),
        ],
        string='Tipo Plan BO',
        default='subscription_recurring',
    )
    duration_days = fields.Integer(string='Duración (días)', default=30)
    product_id = fields.Many2one(
        'product.product',
        string='Producto Suscripción / Alquiler',
        required=True,
    )
    subscription_plan_id = fields.Many2one(
        'sale.subscription.plan',
        string='Plan Recurrente Odoo',
    )
    rental_sequence_id = fields.Many2one(
        'oulalab.bo.rental.sequence',
        string='Secuencia Órdenes Alquiler',
        help='Secuencia específica para los arriendos generados bajo este plan (ej. RO-, STKOUT).',
    )
    garment_limit = fields.Integer(string='Máx. Prendas / Mes (itemsPerMonth)', default=0)
    items_per_rental = fields.Integer(
        string='Prendas por Entrega (itemsPerRental)',
        default=0,
        help='Cantidad de prendas simultáneas permitidas en cada entrega/orden (ej. 2 en Básico: 2 iniciales + 2 en swap).',
    )
    swaps_allowed = fields.Integer(string='Cambios (Swaps / Mes)', default=0)
    max_premium = fields.Integer(string='Máx. Prendas Premium / Mes', default=0)
    max_premium_per_rental = fields.Integer(
        string='Máx. Premium por Entrega',
        default=0,
        help='Tope de prendas con coronita (Es Premium) permitidas en una sola entrega.',
    )
    swap_window_start_day = fields.Integer(string='Inicio Ventana Swap (Día)', default=5)
    swap_window_end_day = fields.Integer(string='Fin Ventana Swap (Día)', default=20)
    addon_extra_garment_enabled = fields.Boolean(string='Permite Prenda Extra entre Swaps', default=True)
    addon_extra_garment_price = fields.Float(string='Precio Prenda Extra (CLP)', default=20000.0)
    addon_extra_allow_premium = fields.Boolean(string='Prenda Extra Permite Coronita', default=True)
    profile_key = fields.Char(string='Profile Key BO', index=True)
    policy_json = fields.Text(
        string='Política del Plan (JSON v1 BO)',
        help='Pega aquí el JSON v1 de política del plan desde el BackOffice; los límites se extraen automáticamente.',
    )
    monthly_price = fields.Float(string='Precio Referencia (CLP)', default=0.0)
    weekly_balance = fields.Float(string='Balance Semanal Plan', default=0.0)
    active = fields.Boolean(default=True)

    @api.onchange('policy_json')
    def _onchange_policy_json(self):
        for rec in self:
            parsed = rec._parse_policy_json_vals(rec.policy_json)
            if parsed:
                rec.update(parsed)

    @api.model
    def _parse_policy_json_vals(self, raw_json):
        import json
        if not raw_json or not str(raw_json).strip():
            return {}
        try:
            data = json.loads(raw_json)
        except Exception:
            return {}
        if not isinstance(data, dict):
            return {}

        vals = {}
        quotas = data.get('quotas') or {}
        if 'itemsPerMonth' in quotas:
            vals['garment_limit'] = int(quotas['itemsPerMonth'] or 0)
        if 'itemsPerRental' in quotas:
            vals['items_per_rental'] = int(quotas['itemsPerRental'] or 0)
        if 'exchangesPerMonth' in quotas:
            vals['swaps_allowed'] = int(quotas['exchangesPerMonth'] or 0)

        swap = data.get('swap') or {}
        if 'windowStartDayOfBlock' in swap:
            vals['swap_window_start_day'] = int(swap['windowStartDayOfBlock'] or 0)
        if 'windowEndDayOfBlock' in swap:
            vals['swap_window_end_day'] = int(swap['windowEndDayOfBlock'] or 0)
        if 'subscriptionPeriodDays' in swap:
            vals['duration_days'] = int(swap['subscriptionPeriodDays'] or 30)

        prem = data.get('premium') or {}
        if 'maxPremiumItemsPerMonth' in prem:
            vals['max_premium'] = int(prem['maxPremiumItemsPerMonth'] or 0)
        if 'maxPremiumItemsPerRental' in prem:
            vals['max_premium_per_rental'] = int(prem['maxPremiumItemsPerRental'] or 0)

        if data.get('profileKey'):
            vals['profile_key'] = str(data['profileKey'])

        addons = data.get('addOns') or []
        for ad in addons:
            if isinstance(ad, dict) and ad.get('id') == 'extra_garment_between_swaps':
                vals['addon_extra_garment_enabled'] = bool(ad.get('enabled', True))
                vals['addon_extra_garment_price'] = float(ad.get('priceClp') or 20000.0)
                vals['addon_extra_allow_premium'] = bool(ad.get('allowPremiumGarment', True))
                break
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('policy_json'):
                parsed = self._parse_policy_json_vals(vals['policy_json'])
                for k, v in parsed.items():
                    vals.setdefault(k, v)
        return super().create(vals_list)

    def write(self, vals):
        if 'policy_json' in vals and vals['policy_json']:
            parsed = self._parse_policy_json_vals(vals['policy_json'])
            merged = dict(parsed)
            merged.update(vals)
            return super().write(merged)
        return super().write(vals)

    @api.model
    def upsert_from_bo_plan(self, row, dry_run=False):
        bo_uuid = (row.get('ID') or '').strip()
        name = (row.get('Nombre') or '').strip()
        plan_type = (row.get('Tipo') or 'subscription_recurring').strip()
        state_raw = (row.get('Estado') or 'active').strip().lower()

        if not name:
            return 'skipped', self.browse(), 'Fila de plan sin Nombre.'

        def _to_int(val):
            try:
                return int(float(str(val).strip()))
            except (ValueError, TypeError):
                return 0

        def _to_float(val):
            try:
                return float(str(val).strip())
            except (ValueError, TypeError):
                return 0.0

        seq = _to_int(row.get('Orden')) or 10
        duration = _to_int(row.get('Duración (días)')) or 30
        max_garments = _to_int(row.get('Máx. prendas'))
        swaps = _to_int(row.get('Cambios'))
        max_prem = _to_int(row.get('Máx. premium'))
        price = _to_float(row.get('Precio/mes'))
        is_active = state_raw == 'active'

        existing = self.with_context(active_test=False).search(
            ['|', ('bo_plan_uuid', '=', bo_uuid), ('bo_plan_code', '=ilike', name)],
            limit=1,
        ) if bo_uuid else self.with_context(active_test=False).search(
            [('bo_plan_code', '=ilike', name)], limit=1
        )

        Product = self.env['product.product']
        is_recurring = plan_type == 'subscription_recurring'
        prod = existing.product_id if existing else Product.search(
            ['|', ('name', '=ilike', name), ('name', '=ilike', f'Plan {name}')], limit=1
        )
        if not prod and not dry_run:
            prod_vals = {
                'name': f'Plan {name}' if is_recurring else name,
                'type': 'service',
                'sale_ok': True,
                'recurring_invoice': is_recurring,
                'rent_ok': not is_recurring,
                'list_price': price,
            }
            prod = Product.create(prod_vals)

        SubPlan = self.env['sale.subscription.plan']
        sub_plan = SubPlan.search([('name', 'ilike', 'Mensual')], limit=1) if is_recurring else SubPlan.browse()

        vals = {
            'sequence': seq,
            'bo_plan_code': name,
            'plan_type': plan_type if plan_type in ('subscription_recurring', 'one_shot_bundle', 'one_shot_calendar') else 'subscription_recurring',
            'duration_days': duration,
            'garment_limit': max_garments,
            'swaps_allowed': swaps,
            'max_premium': max_prem,
            'active': is_active,
        }
        raw_policy = (row.get('Política del plan') or row.get('policy_json') or row.get('Política') or '').strip()
        if raw_policy:
            vals['policy_json'] = raw_policy
            vals.update(self._parse_policy_json_vals(raw_policy))
        if bo_uuid:
            vals['bo_plan_uuid'] = bo_uuid
        if price > 0:
            vals['monthly_price'] = price
        if prod:
            vals['product_id'] = prod.id
        if sub_plan and not (existing and existing.subscription_plan_id):
            vals['subscription_plan_id'] = sub_plan.id

        if existing:
            if not dry_run:
                existing.with_context(active_test=False).write(vals)
            return 'updated', existing, f"Plan actualizado ({name} - {max_garments} prendas)"

        if not dry_run:
            existing = self.create(vals)
        return 'created', existing, f"Plan creado ({name} - {max_garments} prendas)"


class OulalabBoCycleFamilyRule(models.Model):
    _name = 'oulalab.bo.cycle.family.rule'
    _description = 'Tope de Prendas por Familia en un Ciclo de Arriendo BO'
    _order = 'sequence asc, id asc'

    sequence = fields.Integer(default=10)
    config_id = fields.Many2one(
        'oulalab.bo.stock.config',
        string='Configuración',
        ondelete='cascade',
        default=lambda self: self.env['oulalab.bo.stock.config'].search([], limit=1),
    )
    name = fields.Char(string='Familia de Prenda', required=True, help='Ej: chaquetas o abrigos')
    keywords = fields.Char(
        string='Palabras que la Identifican (separadas por coma)',
        required=True,
        help='Ej: chaqueta, chaquetas, abrigo, abrigos, campera, parka, tapado, trench, jacket, jackets, coat, coats, outerwear',
    )
    max_per_cycle = fields.Integer(string='Máx. por Ciclo', default=2, required=True)
    active = fields.Boolean(default=True)

    @api.model
    def evaluate_order_composition(self, item_names):
        """
        Evalúa una lista de nombres de prendas de un pedido/ciclo contra las reglas activas
        de composición del ciclo (ej. máx. 2 chaquetas o abrigos por ciclo).
        Retorna una lista de alertas en caso de exceder el tope.
        """
        rules = self.search([('active', '=', True)])
        alerts = []
        names_lower = [(n or '').lower() for n in item_names if n]
        for rule in rules:
            kw_list = [k.strip().lower() for k in (rule.keywords or '').split(',') if k.strip()]
            if not kw_list or rule.max_per_cycle <= 0:
                continue
            matched = [
                n for n in names_lower
                if any(kw in n for kw in kw_list)
            ]
            if len(matched) > rule.max_per_cycle:
                alerts.append(
                    f"Alerta Composición Ciclo [{rule.name}]: {len(matched)} prendas exceden el máximo de {rule.max_per_cycle} por ciclo."
                )
        return alerts
