import json
import re
from odoo import api, fields, models
from odoo.exceptions import UserError


ENTITY_SELECTION = [
    ('plans', 'Planes BO (oulalab.bo.plan.map)'),
    ('categories', 'Categorías (product.category)'),
    ('brands', 'Marcas (res.partner / product.tag)'),
    ('collections', 'Colecciones (product.tag)'),
    ('colors', 'Colores (product.tag)'),
    ('occasions', 'Ocasiones (product.tag)'),
    ('garments', 'Prendas Maestras (product.template)'),
    ('inventory', 'Inventario / Variantes SKU (product.template)'),
    ('customers', 'Clientes (res.partner)'),
    ('leads', 'Leads (crm.lead)'),
    ('appointments', 'Citas Showroom (calendar.event)'),
    ('subscriptions', 'Suscripciones -> Contrato OULAPLAN (sale.order)'),
    ('payments', 'Pagos BO -> Contrato OULAPLAN (sale.order)'),
    ('mercadopago_sales', 'Ventas Mercado Pago -> Conciliación OULAPLAN (sale.order)'),
    ('rentals', 'Órdenes de Alquiler -> RO/STKOUT/BTL (sale.order)'),
    ('orders', 'Detalle Pedidos / Ítems -> RO/STKOUT/BTL (sale.order)'),
    ('inventory_reservations', 'Reservas Inventario -> RO/STKOUT/BTL (sale.order)'),
    ('return_orders', 'Órdenes de Devolución -> RO/STKOUT/BTL (sale.order)'),
    ('webhook_event', 'Evento Webhook BO'),
]


class OulalabBoStagingBatch(models.Model):
    _name = 'oulalab.bo.staging.batch'
    _description = 'Lote de Revisión Previa de Datos BO antes de Registrar en Odoo'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Referencia Lote', required=True, readonly=True, default='Nuevo')
    source_type = fields.Selection(
        [
            ('csv_upload', 'Importación Archivo CSV / XLSX'),
            ('webhook', 'Webhook Tiempo Real BO'),
        ],
        string='Canal de Entrada',
        default='csv_upload',
        readonly=True,
    )
    file_name = fields.Char(string='Origen / Archivo', readonly=True)
    entity_type = fields.Selection(ENTITY_SELECTION, string='Entidad BO', required=True, readonly=True)
    auto_create_partner_from_lead = fields.Boolean(string='Auto-crear Contacto desde Lead', readonly=True)
    only_update_existing = fields.Boolean(
        string='Solo Actualizar Existentes (Sin Crear Nuevos)',
        help='Si está activo, toda fila cuya acción proyectada sea Crear Nuevo será omitida/descartada automáticamente.',
    )
    state = fields.Selection(
        [
            ('pending_review', 'Pendiente de Revisión'),
            ('partially_applied', 'Aplicado Parcialmente'),
            ('applied', 'Aplicado en Odoo'),
            ('discarded', 'Descartado'),
        ],
        string='Estado del Lote',
        default='pending_review',
        readonly=True,
    )
    total_lines = fields.Integer(string='Total Registros', compute='_compute_counters', store=True)
    ok_lines_count = fields.Integer(string='Válidos (OK)', compute='_compute_counters', store=True)
    warning_lines_count = fields.Integer(string='Con Incongruencias / Alertas', compute='_compute_counters', store=True)
    error_lines_count = fields.Integer(string='Bloqueantes / Error', compute='_compute_counters', store=True)
    approved_pending_count = fields.Integer(string='Aprobados por Aplicar', compute='_compute_counters', store=True)
    applied_lines_count = fields.Integer(string='Aplicados en Odoo', compute='_compute_counters', store=True)

    line_ids = fields.One2many('oulalab.bo.staging.line', 'batch_id', string='Registros a Revisar')
    notes = fields.Text(string='Resumen de Validación', readonly=True)
    sync_log_id = fields.Many2one('oulalab.bo.sync.log', string='Log de Aplicación', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Nuevo':
                vals['name'] = f"BO-REV-{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return super().create(vals_list)

    @api.depends('line_ids.validation_status', 'line_ids.review_decision')
    def _compute_counters(self):
        for batch in self:
            lines = batch.line_ids
            batch.total_lines = len(lines)
            batch.ok_lines_count = len(lines.filtered(lambda l: l.validation_status == 'ok'))
            batch.warning_lines_count = len(lines.filtered(lambda l: l.validation_status == 'warning'))
            batch.error_lines_count = len(lines.filtered(lambda l: l.validation_status == 'error'))
            batch.approved_pending_count = len(lines.filtered(lambda l: l.review_decision == 'approved'))
            batch.applied_lines_count = len(lines.filtered(lambda l: l.review_decision == 'applied'))

    def action_approve_all_valid(self):
        for batch in self:
            to_approve = batch.line_ids.filtered(
                lambda l: l.review_decision == 'pending' and l.validation_status in ('ok', 'warning') and l.projected_action in ('created', 'updated')
            )
            to_approve.write({'review_decision': 'approved'})

    def action_approve_only_clean_ok(self):
        for batch in self:
            to_approve = batch.line_ids.filtered(
                lambda l: l.review_decision == 'pending' and l.validation_status == 'ok' and l.projected_action in ('created', 'updated')
            )
            to_approve.write({'review_decision': 'approved'})

    def action_discard_warnings(self):
        for batch in self:
            to_discard = batch.line_ids.filtered(
                lambda l: l.review_decision in ('pending', 'approved') and l.validation_status in ('warning', 'error')
            )
            to_discard.write({'review_decision': 'discarded'})

    def action_discard_batch(self):
        for batch in self:
            batch.line_ids.filtered(lambda l: l.review_decision != 'applied').write({'review_decision': 'discarded'})
            batch.state = 'discarded'

    def action_revalidate_batch(self):
        for batch in self:
            for line in batch.line_ids.filtered(lambda l: l.review_decision != 'applied'):
                line._run_precheck_validation()

    def action_apply_approved_lines(self):
        self.ensure_one()
        approved = self.line_ids.filtered(lambda l: l.review_decision == 'approved')
        if not approved:
            raise UserError('No hay líneas marcadas como "Aprobado" para registrar en Odoo.')

        created = updated = skipped = errors = 0
        log_lines = []

        for line in approved:
            row = json.loads(line.raw_payload_json or '{}')
            eff_type = line.effective_entity_type or self.entity_type
            try:
                with self.env.cr.savepoint():
                    if self.only_update_existing:
                        dry_act, dry_rec, dry_msg = line._execute_upsert_for_entity(
                            eff_type,
                            row,
                            auto_create_partner=False,
                            dry_run=True,
                        )
                        if dry_act == 'created' or not dry_rec:
                            action = 'skipped'
                            rec = self.env['sale.order'].browse()
                            msg = f"Omitido por modo 'Solo actualizar existentes': {dry_msg}"
                        else:
                            action, rec, msg = line._execute_upsert_for_entity(
                                eff_type,
                                row,
                                auto_create_partner=False,
                                dry_run=False,
                            )
                    else:
                        action, rec, msg = line._execute_upsert_for_entity(
                            eff_type,
                            row,
                            auto_create_partner=self.auto_create_partner_from_lead,
                            dry_run=False,
                        )
                if action == 'created':
                    created += 1
                elif action == 'updated':
                    updated += 1
                elif action == 'error':
                    errors += 1
                else:
                    skipped += 1

                line.write({
                    'review_decision': 'applied' if action in ('created', 'updated', 'skipped') else 'pending',
                    'applied_res_model': line.target_res_model,
                    'applied_res_id': rec.id if rec else 0,
                    'apply_result_message': msg,
                })
                log_lines.append((0, 0, {
                    'row_number': line.row_number,
                    'external_key': line.external_key,
                    'action': action,
                    'res_model': line.target_res_model,
                    'res_id': rec.id if rec else 0,
                    'message': msg,
                }))
            except Exception as exc:
                errors += 1
                line.write({
                    'validation_status': 'error',
                    'apply_result_message': str(exc),
                })
                log_lines.append((0, 0, {
                    'row_number': line.row_number,
                    'external_key': line.external_key,
                    'action': 'error',
                    'res_model': line.target_res_model,
                    'res_id': 0,
                    'message': str(exc),
                }))

        log_state = 'done' if errors == 0 else ('partial' if (created + updated) > 0 else 'failed')
        log = self.env['oulalab.bo.sync.log'].create({
            'file_name': f"{self.name} ({self.file_name or self.entity_type})",
            'entity_type': self.entity_type,
            'is_dry_run': False,
            'state': log_state,
            'total_rows': len(approved),
            'created_count': created,
            'updated_count': updated,
            'skipped_count': skipped,
            'error_count': errors,
            'line_ids': log_lines,
            'notes': f"Aplicado desde bandeja de revisión {self.name}.",
        })

        remaining = self.line_ids.filtered(lambda l: l.review_decision in ('pending', 'approved'))
        self.write({
            'sync_log_id': log.id,
            'state': 'applied' if not remaining else 'partially_applied',
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Resultado de Aplicación en Odoo',
            'res_model': 'oulalab.bo.sync.log',
            'res_id': log.id,
            'view_mode': 'form',
            'target': 'current',
        }


class OulalabBoStagingLine(models.Model):
    _name = 'oulalab.bo.staging.line'
    _description = 'Línea de Revisión Previa y Validación de Incongruencias BO'
    _order = 'row_number asc, id asc'

    batch_id = fields.Many2one('oulalab.bo.staging.batch', string='Lote', required=True, ondelete='cascade')
    row_number = fields.Integer(string='Fila', readonly=True)
    effective_entity_type = fields.Char(string='Subtipo Entidad', readonly=True)
    external_key = fields.Char(string='Clave / SKU / Email / Op', readonly=True)
    target_res_model = fields.Char(string='Modelo Destino', readonly=True)
    existing_res_id = fields.Integer(string='ID Existente Odoo', readonly=True)
    existing_record_ref = fields.Char(string='Registro Actual en Odoo', readonly=True)

    projected_action = fields.Selection(
        [
            ('created', 'Crear Nuevo'),
            ('updated', 'Actualizar Existente'),
            ('skipped', 'Omitir'),
            ('error', 'Error'),
        ],
        string='Acción Proyectada',
        readonly=True,
    )
    validation_status = fields.Selection(
        [
            ('ok', 'Válido (OK)'),
            ('warning', 'Incongruencia / Alerta'),
            ('error', 'Bloqueante / Error'),
        ],
        string='Validación',
        default='ok',
        readonly=True,
    )
    review_decision = fields.Selection(
        [
            ('pending', 'Pendiente Revisión'),
            ('approved', 'Aprobado'),
            ('discarded', 'Descartado'),
            ('applied', 'Aplicado en Odoo'),
        ],
        string='Decisión',
        default='pending',
    )
    changes_summary = fields.Text(string='Cambios Detectados (BO -> Odoo)', readonly=True)
    inconsistencies_text = fields.Text(string='Validaciones e Incongruencias', readonly=True)
    raw_payload_json = fields.Text(string='Datos Crudos BO (JSON)', readonly=True)

    applied_res_model = fields.Char(string='Modelo Aplicado', readonly=True)
    applied_res_id = fields.Integer(string='ID Aplicado', readonly=True)
    apply_result_message = fields.Char(string='Resultado Aplicación', readonly=True)

    def action_approve_line(self):
        for rec in self:
            if rec.review_decision != 'applied':
                rec.review_decision = 'approved'

    def action_discard_line(self):
        for rec in self:
            if rec.review_decision != 'applied':
                rec.review_decision = 'discarded'

    def _execute_upsert_for_entity(self, resolved_type, row, auto_create_partner=False, dry_run=True):
        env = self.with_context(skip_bo_outbound=True).env
        if resolved_type == 'plans':
            return env['oulalab.bo.plan.map'].upsert_from_bo_plan(row, dry_run=dry_run)
        elif resolved_type == 'categories':
            return env['product.category'].upsert_from_bo_category(row, dry_run=dry_run)
        elif resolved_type == 'brands':
            return env['res.partner'].upsert_from_bo_brand(row, dry_run=dry_run)
        elif resolved_type == 'collections':
            return env['product.tag'].upsert_from_bo_collection(row, dry_run=dry_run)
        elif resolved_type == 'colors':
            return env['product.tag'].upsert_from_bo_color(row, dry_run=dry_run)
        elif resolved_type == 'occasions':
            return env['product.tag'].upsert_from_bo_occasion(row, dry_run=dry_run)
        elif resolved_type == 'garments':
            return env['product.template'].upsert_from_bo_garment(row, dry_run=dry_run)
        elif resolved_type == 'inventory':
            return env['product.template'].upsert_from_bo_inventory(row, dry_run=dry_run)
        elif resolved_type == 'customers':
            return env['res.partner'].upsert_from_bo_customer(row, dry_run=dry_run)
        elif resolved_type == 'leads':
            return env['crm.lead'].upsert_from_bo_lead(
                row, auto_create_partner=auto_create_partner, dry_run=dry_run
            )
        elif resolved_type == 'appointments':
            return env['calendar.event'].upsert_from_bo_appointment(row, dry_run=dry_run)
        elif resolved_type == 'subscriptions':
            return env['sale.order'].upsert_from_bo_subscription(row, dry_run=dry_run)
        elif resolved_type == 'payments':
            return env['sale.order'].upsert_from_bo_payment(row, dry_run=dry_run)
        elif resolved_type == 'mercadopago_sales':
            return env['sale.order'].upsert_from_mercadopago_sale(row, dry_run=dry_run)
        elif resolved_type == 'rentals':
            return env['sale.order'].upsert_from_bo_rental(row, dry_run=dry_run)
        elif resolved_type == 'orders':
            return env['sale.order'].upsert_from_bo_order(row, dry_run=dry_run)
        elif resolved_type == 'inventory_reservations':
            return env['sale.order'].upsert_from_bo_inventory_reservation(row, dry_run=dry_run)
        elif resolved_type == 'return_orders':
            return env['sale.order'].upsert_from_bo_return_order(row, dry_run=dry_run)
        raise UserError(f'Tipo de entidad no soportado: {resolved_type}')

    def _detect_business_inconsistencies(self, resolved_type, row, action, rec, dry_msg):
        warnings = []
        blockers = []
        diffs = []

        if action == 'error':
            blockers.append(dry_msg)
            return blockers, warnings, diffs

        if action == 'skipped':
            warnings.append(f"Omitido: {dry_msg}")
            return blockers, warnings, diffs

        if resolved_type == 'inventory':
            sku = (row.get('SKU') or '').strip()
            garment_name = (row.get('Prenda') or '').strip()
            op_status = (row.get('Estado operativo') or '').strip()
            try:
                bo_stock = int(float(str(row.get('Stock') or 0)))
                bo_avail = int(float(str(row.get('Disponible') or 0)))
            except ValueError:
                bo_stock = bo_avail = 0

            units = self.env['product.template']._get_candidate_units_for_bo_sku(bo_sku=sku, garment_name=garment_name)
            odoo_unit_count = len(units)
            stock_cfg = self.env['oulalab.bo.stock.config'].get_active_config()
            avail_locs = stock_cfg.get_available_locations_tree()
            Quant = self.env['stock.quant']
            odoo_avail = int(round(sum(
                max(0.0, q.quantity - q.reserved_quantity)
                for q in Quant.search([('product_id', 'in', units.ids), ('location_id', 'in', avail_locs.ids)])
            )))

            diffs.append(f"Unidades físicas en Odoo: {odoo_unit_count} | Stock BO: {bo_stock}")
            diffs.append(f"Disponible en Racks/BTL Odoo: {odoo_avail} | Disponible BO: {bo_avail}")

            if bo_avail > bo_stock:
                blockers.append(f"Incongruencia en BO: Disponible ({bo_avail}) mayor que Stock total ({bo_stock}).")
            if odoo_unit_count == 0:
                warnings.append(f"SKU '{sku}' no existe en Odoo: se creará ficha nueva desde cero.")
            elif bo_stock != odoo_unit_count:
                warnings.append(
                    f"Diferencia de flota física: BO reporta {bo_stock} unidad(es), Odoo tiene {odoo_unit_count} registro(s) serializado(s)."
                )
            if bo_avail != odoo_avail:
                warnings.append(
                    f"Diferencia de disponibilidad: BO reporta {bo_avail} disponible(s), Odoo tiene {odoo_avail} en ubicaciones activas."
                )
            if op_status.lower() in ('retirado', 'baja', 'inactivo') and odoo_avail > 0:
                warnings.append(
                    f"Prenda marcada '{op_status}' en BO pero aún figura con {odoo_avail} unidad(es) disponible(s) en Racks Odoo."
                )

        elif resolved_type == 'subscriptions':
            email = (row.get('Email') or row.get('Correo') or '').strip().lower()
            plan_code = (row.get('Plan de arriendo') or row.get('Plan') or '').strip()
            status_raw = (row.get('Estado') or '').strip().lower()
            plan_map = self.env['oulalab.bo.plan.map'].search([('bo_plan_code', '=ilike', plan_code)], limit=1) if plan_code else False
            if not plan_map:
                blockers.append(f"Plan '{plan_code}' no está mapeado en OulaLab BO Sync > Planes y Productos.")
            if rec:
                cur_prod = rec.order_line[:1].product_id.display_name if rec.order_line else 'Sin línea'
                cur_state = rec.subscription_state if 'subscription_state' in rec._fields else rec.state
                diffs.append(f"Contrato {rec.name}: Plan actual='{cur_prod}' -> Nuevo='{plan_map.product_id.display_name if plan_map else plan_code}'")
                diffs.append(f"Estado actual='{cur_state}' -> Estado BO='{status_raw}'")
                if plan_map and rec.order_line and rec.order_line[0].product_id != plan_map.product_id:
                    warnings.append(f"Cambio de plan detectado para {email}: {cur_prod} -> {plan_map.product_id.display_name}.")
                if status_raw in ('cancelled', 'canceled', 'churned') and cur_state != '6_churn':
                    warnings.append(f"Cancelación de suscripción activa ({rec.name}).")
            else:
                diffs.append(f"Se creará nuevo contrato OULAPLAN-* para {email} con plan '{plan_code}'.")

        elif resolved_type in ('orders', 'rentals'):
            from datetime import timedelta
            from .res_partner import parse_bo_iso_datetime

            email = (row.get('Email del cliente') or row.get('Email') or '').strip().lower()
            skus_raw = (row.get('SKUs de ítems') or '').strip()
            names_raw = (row.get('Nombres de ítems') or '').strip()
            channel = (row.get('Canal') or '').strip()
            created_str = (row.get('Fecha de creación') or row.get('Fecha del arriendo') or '').strip()
            skus = [s.strip() for s in skus_raw.split(';') if s.strip()]
            names = [n.strip() for n in names_raw.split(';') if n.strip()]
            is_btl = any('-btl-' in s.lower() for s in skus) or 'btl' in channel.lower()

            resolved_prods = []
            premium_in_order = 0
            for idx_s, sku_tok in enumerate(skus):
                g_name = names[idx_s] if idx_s < len(names) else ''
                prod, is_avail, sel_msg = self.env['product.template']._select_available_unit_for_bo_sku(
                    bo_sku=sku_tok, garment_name=g_name
                )
                if not prod:
                    warnings.append(f"SKU '{sku_tok}' sin ficha física en Odoo (usará cupo genérico).")
                else:
                    resolved_prods.append(prod)
                    is_prem = bool(prod.product_tmpl_id.x_studio_es_premium) if 'x_studio_es_premium' in prod.product_tmpl_id._fields else False
                    if is_prem:
                        premium_in_order += 1
                    if not is_avail:
                        warnings.append(f"SKU '{sku_tok}' sin stock disponible en Racks/BTL ({sel_msg}).")
                    else:
                        diffs.append(
                            f"SKU {sku_tok} -> Unidad física {prod.default_code} (Barcode: {prod.barcode or 'N/A'}"
                            f"{' | CORONITA' if is_prem else ''})"
                        )

            if is_btl:
                diffs.append("Canal Book The Look (BTL-RO-*): Orden puntual con precio de alquiler e invoice individual (sin requerir suscripción OULAPLAN-*).")

            partner = self.env['res.partner']._find_bo_partner(email=email)
            if not partner:
                warnings.append(f"Cliente '{email}' no existe aún en res.partner (se creará automáticamente).")
            elif not is_btl:
                active_sub = self.env['sale.order']._find_oulaplan_contract(partner=partner)
                if not active_sub:
                    warnings.append(f"Cliente '{email}' no tiene contrato OULAPLAN-* activo en Odoo para respaldar este arriendo.")
                else:
                    sub_prod = active_sub.order_line[:1].product_id
                    pmap = self.env['oulalab.bo.plan.map'].search([('product_id', '=', sub_prod.id)], limit=1) if sub_prod else False
                    qty_req = len(skus) or int(float(row.get('Prendas') or 0))

                    # Validar cuota por entrega (itemsPerRental) vs mensual (itemsPerMonth)
                    per_rental_limit = (pmap.items_per_rental if pmap and pmap.items_per_rental else 0) or (
                        (pmap.garment_limit // 2) if (pmap and pmap.garment_limit and pmap.swaps_allowed) else (
                            partner.x_studio_tope_de_prendas if 'x_studio_tope_de_prendas' in partner._fields else 0
                        )
                    )
                    max_with_addon = per_rental_limit + (1 if (pmap and pmap.addon_extra_garment_enabled) else 0)
                    if per_rental_limit and qty_req > max_with_addon:
                        warnings.append(
                            f"Exceso de cuota por entrega: pedido trae {qty_req} prendas, máximo permitido en plan '{pmap.bo_plan_code if pmap else active_sub.name}' es {per_rental_limit} (o {max_with_addon} con prenda extra)."
                        )
                    elif per_rental_limit and qty_req == per_rental_limit + 1 and pmap and pmap.addon_extra_garment_enabled:
                        diffs.append(
                            f"Add-on detectado: +1 prenda extra entre swaps (+${pmap.addon_extra_garment_price:,.0f} CLP)."
                        )

                    # Validar cuota de prendas con coronita (Es Premium) por entrega y por mes
                    prem_per_rental = (pmap.max_premium_per_rental if pmap and pmap.max_premium_per_rental else (pmap.max_premium if pmap else 0))
                    if prem_per_rental and premium_in_order > prem_per_rental:
                        warnings.append(
                            f"Exceso de prendas con coronita en la entrega: {premium_in_order} seleccionadas vs máximo {prem_per_rental} por entrega."
                        )

                    # Validar ventana de Swap y devolución completa de selección anterior
                    SeqModel = self.env['oulalab.bo.rental.sequence']
                    rental_dom = SeqModel.build_rental_order_domain([
                        ('partner_id', '=', partner.id),
                        ('state', '!=', 'cancel'),
                    ])
                    open_rentals = self.env['sale.order'].search(rental_dom)
                    unreturned = open_rentals.filtered(
                        lambda o: ('rental_status' in o._fields and o.rental_status == 'pickup')
                        and (o.x_bo_return_status not in ('received', 'inspected'))
                    )
                    if unreturned:
                        warnings.append(
                            f"Swap con prendas previas sin devolver: orden(es) {', '.join(unreturned.mapped('name'))} aún figuran activas/sin recepción."
                        )

                    order_dt, _ = parse_bo_iso_datetime(created_str)
                    if order_dt and active_sub.start_date and open_rentals and pmap and pmap.swap_window_start_day and pmap.swap_window_end_day:
                        days_elapsed = (order_dt.date() - active_sub.start_date).days % (pmap.duration_days or 30)
                        if not (pmap.swap_window_start_day <= days_elapsed <= pmap.swap_window_end_day):
                            warnings.append(
                                f"Swap fuera de ventana del plan ({pmap.bo_plan_code}): día {days_elapsed} del bloque (ventana permitida: día {pmap.swap_window_start_day} al {pmap.swap_window_end_day})."
                            )

            if names:
                comp_alerts = self.env['oulalab.bo.cycle.family.rule'].evaluate_order_composition(names)
                warnings.extend(comp_alerts)

        elif resolved_type == 'leads':
            bo_commune = (row.get('Comuna') or '').strip()
            c_info = self.env['oulalab.bo.commune.map'].resolve_commune(bo_commune)
            if not c_info['in_coverage']:
                warnings.append(f"Lead fuera de zona de cobertura ({bo_commune} -> etapa 'Fuera de Zona').")
            diffs.append(dry_msg)

        elif resolved_type in ('payments', 'mercadopago_sales'):
            mp_status = (row.get('Estado') or '').strip().lower()
            if mp_status in ('rechazado', 'reembolsado', 'cobro anulado', 'failed', 'refunded'):
                warnings.append(f"Transacción con estado financiero '{row.get('Estado')}': marcará alerta en contrato.")
            diffs.append(dry_msg)

        else:
            diffs.append(dry_msg)

        if 'Sin stock disponible' in dry_msg or 'No se encontró' in dry_msg:
            if dry_msg not in warnings:
                warnings.append(dry_msg)

        return blockers, warnings, diffs

    def _run_precheck_validation(self):
        for line in self:
            row = json.loads(line.raw_payload_json or '{}')
            eff_type = line.effective_entity_type or line.batch_id.entity_type
            try:
                with self.env.cr.savepoint():
                    only_upd = line.batch_id.only_update_existing
                    action, rec, dry_msg = line._execute_upsert_for_entity(
                        eff_type,
                        row,
                        auto_create_partner=(False if only_upd else line.batch_id.auto_create_partner_from_lead),
                        dry_run=True,
                    )
                if line.batch_id.only_update_existing and (action == 'created' or not rec):
                    action = 'skipped'
                    dry_msg = f"Omitido (Modo Solo Actualizar Existentes en Odoo): {dry_msg}"
                    blockers, warnings, diffs = [], [dry_msg], [dry_msg]
                else:
                    blockers, warnings, diffs = line._detect_business_inconsistencies(
                        eff_type, row, action, rec, dry_msg
                    )
            except Exception as exc:
                action = 'error'
                rec = False
                dry_msg = str(exc)
                blockers = [str(exc)]
                warnings = []
                diffs = []

            if blockers:
                v_status = 'error'
                decision = 'discarded'
            elif warnings:
                v_status = 'warning'
                decision = 'pending'
            elif action == 'skipped':
                v_status = 'ok'
                decision = 'discarded'
            else:
                v_status = 'ok'
                decision = 'approved'

            all_notes = []
            for b in blockers:
                all_notes.append(f"[ERROR] {b}")
            for w in warnings:
                all_notes.append(f"[ALERTA] {w}")
            if not all_notes:
                all_notes.append("Sin incongruencias detectadas.")

            line.write({
                'existing_res_id': rec.id if rec else 0,
                'existing_record_ref': rec.display_name if rec else 'Nuevo registro',
                'projected_action': action,
                'validation_status': v_status,
                'review_decision': decision,
                'changes_summary': "\n".join(diffs) if diffs else dry_msg,
                'inconsistencies_text': "\n".join(all_notes),
            })
