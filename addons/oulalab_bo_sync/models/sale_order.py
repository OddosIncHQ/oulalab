from datetime import datetime, timedelta
import re
from odoo import api, fields, models
from .res_partner import parse_bo_iso_datetime


SPANISH_MONTHS = {
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
}


def _pick(row, candidates):
    lower_map = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
    for cand in candidates:
        val = lower_map.get(cand.lower())
        if val is not None and str(val).strip() != '':
            return str(val).strip()
    return ''


def _parse_mp_date(raw_str, reference_dt=None):
    if not raw_str:
        return False
    s = str(raw_str).strip().lower()
    m = re.match(r'^(\d{1,2})\s+([a-z]{3})\s+(\d{1,2}):(\d{2})', s)
    if not m:
        return False
    day = int(m.group(1))
    mon = SPANISH_MONTHS.get(m.group(2))
    hour = int(m.group(3))
    minute = int(m.group(4))
    if not mon:
        return False
    ref = reference_dt or datetime.utcnow()
    year = ref.year
    try:
        dt = datetime(year, mon, day, hour, minute)
        if dt > ref + timedelta(days=7):
            dt = datetime(year - 1, mon, day, hour, minute)
        return dt
    except ValueError:
        return False


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_bo_sync_status = fields.Char(string='Estado BO', readonly=True, copy=False)
    x_bo_return_order_id = fields.Char(string='ID Orden Devolución BO', index=True, copy=False, readonly=True)
    x_bo_return_status = fields.Char(string='Estado Devolución BO', copy=False, readonly=True)
    x_bo_order_code = fields.Char(string='Código Pedido BO', index=True, copy=False, readonly=True)
    x_bo_rental_id = fields.Char(string='ID Alquiler BO', index=True, copy=False, readonly=True)

    @api.model
    def _filter_existing_fields(self, vals):
        return {k: v for k, v in vals.items() if k in self._fields}

    @api.model
    def _get_fallback_rental_product(self):
        Product = self.env['product.product']
        prod = Product.search([('name', '=ilike', 'Cupo de Prenda Arriendo BO')], limit=1)
        if not prod:
            prod = Product.search([('rent_ok', '=', True)], limit=1)
        if not prod:
            prod = Product.create({
                'name': 'Cupo de Prenda Arriendo BO',
                'type': 'service',
                'sale_ok': True,
                'rent_ok': True,
                'list_price': 0.0,
            })
        return prod

    def _trigger_physical_stock_reservation(self):
        for order in self:
            pickings = order.picking_ids.filtered(lambda p: p.state in ('draft', 'confirmed', 'waiting', 'assigned'))
            if pickings:
                pickings.action_assign()

    @api.model
    def _find_oulaplan_contract(self, bo_sub_id=None, partner=None, mp_op_id=None, mp_ext_ref=None):
        base_dom = [('name', '=ilike', 'OULAPLAN-%')]
        if bo_sub_id:
            sub = self.search(
                base_dom + ['|', ('x_bo_order_code', '=', bo_sub_id), ('x_studio_bo_order_code', '=', bo_sub_id)],
                order='id desc',
                limit=1,
            )
            if sub:
                return sub

        if mp_op_id and 'x_studio_numero_operacion_mercado_pago' in self._fields:
            sub = self.search(
                base_dom + [('x_studio_numero_operacion_mercado_pago', '=', str(mp_op_id).strip())],
                order='id desc',
                limit=1,
            )
            if sub:
                return sub

        if mp_ext_ref and 'x_studio_referencia_externa_mercado_pago' in self._fields:
            sub = self.search(
                base_dom + [('x_studio_referencia_externa_mercado_pago', 'ilike', str(mp_ext_ref).strip())],
                order='id desc',
                limit=1,
            )
            if sub:
                return sub

        if partner:
            sub = self.search(
                base_dom + [
                    ('partner_id', '=', partner.id),
                    ('subscription_state', 'in', ('3_progress', '4_paused', '2_renewal')),
                ],
                order='id desc',
                limit=1,
            )
            if sub:
                return sub
            sub = self.search(
                base_dom + [
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'sale'),
                ],
                order='id desc',
                limit=1,
            )
            if sub:
                return sub

        return self.browse()

    def _resolve_rental_order_name(self, active_sub=None, channel='subscription'):
        SeqModel = self.env['oulalab.bo.rental.sequence']
        if active_sub and active_sub.order_line:
            prod = active_sub.order_line[0].product_id
            pmap = self.env['oulalab.bo.plan.map'].search([('product_id', '=', prod.id)], limit=1)
            if pmap and pmap.rental_sequence_id and pmap.rental_sequence_id.ir_sequence_id:
                return pmap.rental_sequence_id.ir_sequence_id.next_by_id()
        return SeqModel.get_next_order_name(channel=channel)

    # -------------------------------------------------------------------------
    # 1. SUSCRIPCIONES (subscriptions-*.csv -> 1 Contrato OULAPLAN por cliente/plan)
    # -------------------------------------------------------------------------
    @api.model
    def upsert_from_bo_subscription(self, row, dry_run=False):
        bo_sub_id = _pick(row, ['ID'])
        client_name = _pick(row, ['Cliente', 'Nombre'])
        email = _pick(row, ['Email', 'Correo']).lower()
        plan_code = _pick(row, ['Plan de arriendo', 'Plan'])
        status_raw = _pick(row, ['Estado']).lower() or 'active'
        start_str = _pick(row, ['Inicio'])
        next_inv_str = _pick(row, ['Expiración'])

        if not client_name and not email and not bo_sub_id:
            return 'skipped', self.browse(), 'Fila de suscripción sin Cliente ni ID.'

        Partner = self.env['res.partner']
        partner = Partner._find_bo_partner(email=email, name=client_name)
        if not partner and not dry_run:
            chile = self.env.ref('base.cl', raise_if_not_found=False)
            partner = Partner.create({
                'name': client_name or email,
                'email': email or False,
                'company_type': 'person',
                'is_oulalab_member': True,
                'country_id': chile.id if chile else False,
            })

        plan_map = self.env['oulalab.bo.plan.map'].with_context(active_test=False).search(
            [('bo_plan_code', '=ilike', plan_code)], limit=1
        ) if plan_code else self.env['oulalab.bo.plan.map'].browse()

        product = plan_map.product_id if plan_map else self.env['product.product'].search(
            [('recurring_invoice', '=', True)], limit=1
        )
        if not product:
            return 'error', self.browse(), (
                f"No hay producto recurrente configurado para el plan '{plan_code}'. "
                "Importe primero plans-*.csv."
            )

        start_dt, _ = parse_bo_iso_datetime(start_str)
        next_dt, _ = parse_bo_iso_datetime(next_inv_str)

        existing = self._find_oulaplan_contract(bo_sub_id=bo_sub_id, partner=partner)

        is_cancelled = status_raw in ('cancelled', 'canceled', 'churned')
        is_paused = status_raw in ('paused',)

        if partner and not dry_run:
            p_vals = {
                'is_oulalab_member': not is_cancelled,
                'x_studio_bo_active': not is_cancelled,
            }
            if plan_map and plan_map.garment_limit:
                p_vals['x_studio_tope_de_prendas'] = plan_map.garment_limit
            partner.write(Partner._filter_existing_fields(p_vals))

        vals = {
            'x_bo_sync_status': status_raw,
            'x_bo_order_code': bo_sub_id,
        }
        if bo_sub_id and 'x_studio_bo_order_code' in self._fields:
            vals['x_studio_bo_order_code'] = bo_sub_id
        if plan_map and plan_map.subscription_plan_id and 'plan_id' in self._fields:
            vals['plan_id'] = plan_map.subscription_plan_id.id
        if next_dt and 'next_invoice_date' in self._fields:
            vals['next_invoice_date'] = next_dt.date()

        if existing:
            if not existing.start_date and start_dt and 'start_date' in self._fields:
                vals['start_date'] = start_dt.date()
            plan_changed_msg = ''
            if not dry_run:
                existing.write(self._filter_existing_fields(vals))
                # Si el cliente cambió de plan en el BO (ej. Básico -> Premium), actualizar la línea del contrato OULAPLAN-*
                if product and existing.order_line:
                    sub_line = existing.order_line[0]
                    if sub_line.product_id != product:
                        old_plan_name = sub_line.product_id.display_name
                        line_update = {'product_id': product.id}
                        if plan_map and plan_map.monthly_price > 0:
                            line_update['price_unit'] = round(plan_map.monthly_price / 1.19, 2)
                        sub_line.write(line_update)
                        plan_changed_msg = f" | Cambio de plan: {old_plan_name} -> {product.display_name}"
                        existing.message_post(
                            body=f"<b>Cambio de Plan desde BO:</b> {old_plan_name} → <b>{product.display_name}</b> (Tope prendas: {plan_map.garment_limit if plan_map else 'N/A'})"
                        )

                if is_cancelled and 'subscription_state' in existing._fields:
                    existing.subscription_state = '6_churn'
                    existing.message_post(body="<b>Suscripción Cancelada desde BO.</b>")
                elif is_paused and 'subscription_state' in existing._fields:
                    existing.subscription_state = '4_paused'
                    existing.message_post(body="<b>Suscripción Pausada desde BO.</b>")
                elif status_raw in ('active', 'trial') and 'subscription_state' in existing._fields and existing.subscription_state in ('4_paused', '6_churn', '1_draft'):
                    existing.subscription_state = '3_progress'
                    existing.message_post(body=f"<b>Suscripción Activada desde BO ({status_raw}).</b>")
            return 'updated', existing, (
                f"Contrato {existing.name} consolidado ({client_name} | Plan: {plan_code} | Estado: {status_raw} | Próx. factura: {next_dt.date() if next_dt else 'N/A'}{plan_changed_msg})"
            )

        line_vals = {
            'product_id': product.id,
            'product_uom_qty': 1.0,
        }
        if plan_map and plan_map.monthly_price > 0:
            line_vals['price_unit'] = plan_map.monthly_price

        create_vals = {
            'partner_id': partner.id,
            'is_subscription': True,
            'order_line': [(0, 0, line_vals)],
            **vals,
        }
        if start_dt and 'start_date' in self._fields:
            create_vals['start_date'] = start_dt.date()
        if not dry_run:
            existing = self.create(self._filter_existing_fields(create_vals))
            if existing.state in ('draft', 'sent') and not is_cancelled:
                existing.action_confirm()
            if is_cancelled and 'subscription_state' in existing._fields:
                existing.subscription_state = '6_churn'
            elif is_paused and 'subscription_state' in existing._fields:
                existing.subscription_state = '4_paused'
        return 'created', existing, f"Nuevo contrato creado ({existing.name if existing else 'OULAPLAN'} - {client_name})"

    # -------------------------------------------------------------------------
    # 2. PAGOS BO (payments-*.csv -> Concilia sobre el contrato OULAPLAN único)
    # -------------------------------------------------------------------------
    @api.model
    def upsert_from_bo_payment(self, row, dry_run=False):
        pay_id = _pick(row, ['ID'])
        status_raw = _pick(row, ['Estado']).lower()
        client_name = _pick(row, ['Cliente'])
        plan_code = _pick(row, ['Plan de arriendo', 'Plan'])
        amount_raw = _pick(row, ['Monto (CLP)', 'Monto'])
        method_raw = _pick(row, ['Método'])
        ref_raw = _pick(row, ['Referencia'])
        paid_at_str = _pick(row, ['Fecha de pago'])

        if not pay_id and not ref_raw:
            return 'skipped', self.browse(), 'Fila de pago sin ID ni Referencia.'

        try:
            amount_clp = float(amount_raw)
        except ValueError:
            amount_clp = 0.0

        sub_uuid = ''
        mp_op_id = ''
        m_checkout = re.match(r'^checkout:([0-9a-fA-F-]{36}):', ref_raw)
        if m_checkout:
            sub_uuid = m_checkout.group(1)
        m_mp = re.match(r'^mp-recurring:[^:]+:(\d+)$', ref_raw)
        if m_mp:
            mp_op_id = m_mp.group(1)

        Partner = self.env['res.partner']
        partner = Partner._find_bo_partner(name=client_name) if client_name else Partner.browse()
        sub = self._find_oulaplan_contract(
            bo_sub_id=sub_uuid,
            partner=partner,
            mp_op_id=mp_op_id,
            mp_ext_ref=ref_raw,
        )

        if not sub:
            return 'skipped', self.browse(), (
                f"No se encontró contrato OULAPLAN para pago {pay_id} ({client_name} / ref: {ref_raw})."
            )

        vals = {}
        if ref_raw and 'x_studio_referencia_externa_mercado_pago' in self._fields:
            vals['x_studio_referencia_externa_mercado_pago'] = ref_raw
        if mp_op_id and 'x_studio_numero_operacion_mercado_pago' in self._fields:
            vals['x_studio_numero_operacion_mercado_pago'] = mp_op_id

        if not dry_run:
            if vals:
                sub.write(self._filter_existing_fields(vals))
            if status_raw == 'paid' and amount_clp > 0 and sub.order_line:
                first_line = sub.order_line[0]
                if first_line.price_unit == 0.0:
                    first_line.write({'price_unit': round(amount_clp / 1.19, 2)})
                if plan_code:
                    pmap = self.env['oulalab.bo.plan.map'].search([('bo_plan_code', '=ilike', plan_code)], limit=1)
                    if pmap and pmap.monthly_price == 0.0:
                        pmap.write({'monthly_price': amount_clp})

            sub.message_post(
                body=(
                    f"<b>Cobro Mensual BO ({pay_id})</b><br/>"
                    f"Estado: <b>{status_raw}</b> | Monto Bruto: <b>{amount_clp:,.0f} CLP</b> | "
                    f"Método: {method_raw} | Ref: <code>{ref_raw}</code> | Fecha pago: {paid_at_str or 'Pendiente'}"
                )
            )
        return 'updated', sub, f"Pago BO ({status_raw} - {amount_clp:,.0f} CLP) consolidado en {sub.name}"

    # -------------------------------------------------------------------------
    # 3. CONCILIACIÓN VENTAS MERCADO PAGO (Ventas_MercadoPago_*.xlsx / .csv)
    # -------------------------------------------------------------------------
    @api.model
    def upsert_from_mercadopago_sale(self, row, dry_run=False):
        op_num = _pick(row, ['Número de operación'])
        buy_date_str = _pick(row, ['Fecha de la compra'])
        mp_status = _pick(row, ['Estado'])
        status_desc = _pick(row, ['Descripción del estado'])
        gross_raw = _pick(row, ['Cobro'])
        fee_raw = _pick(row, ['Cargos e impuestos'])
        refund_raw = _pick(row, ['Anulaciones y reembolsos'])
        net_raw = _pick(row, ['Total a recibir'])
        tool_raw = _pick(row, ['Herramienta de cobro'])
        pay_method = _pick(row, ['Medio de pago'])
        pay_method_desc = _pick(row, ['Descripción del medio de pago'])
        item_desc = _pick(row, ['Descripción del ítem'])
        ext_ref = _pick(row, ['Referencia externa'])

        if not op_num and not ext_ref:
            return 'skipped', self.browse(), 'Fila de Mercado Pago sin Número de operación ni Referencia externa.'

        def _f(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return 0.0

        gross_amt = _f(gross_raw)
        fee_amt = _f(fee_raw)
        refund_amt = _f(refund_raw)
        net_amt = _f(net_raw)

        target_order = self._find_oulaplan_contract(
            bo_sub_id=ext_ref,
            mp_op_id=op_num,
            mp_ext_ref=ext_ref,
        )
        if not target_order and ext_ref:
            target_order = self.search(
                ['|', ('name', '=ilike', ext_ref), ('client_order_ref', 'ilike', ext_ref)],
                order='id desc',
                limit=1,
            )
            if not target_order and '-' in ext_ref:
                base_ref = re.sub(r'-\d+$', '', ext_ref)
                target_order = self.search([('name', '=ilike', base_ref)], order='id desc', limit=1)

        if not target_order:
            return 'skipped', self.browse(), (
                f"Op MP {op_num} ({mp_status} | {item_desc} | Ref={ext_ref or 'N/A'}) sin contrato/orden enlazada."
            )

        vals = {}
        if op_num and 'x_studio_numero_operacion_mercado_pago' in self._fields:
            vals['x_studio_numero_operacion_mercado_pago'] = str(op_num).strip()
        if ext_ref and 'x_studio_referencia_externa_mercado_pago' in self._fields and not target_order.x_studio_referencia_externa_mercado_pago:
            vals['x_studio_referencia_externa_mercado_pago'] = ext_ref

        status_lower = mp_status.lower()
        is_approved = status_lower == 'aprobado'
        is_refunded = status_lower == 'reembolsado'
        is_rejected = status_lower in ('rechazado', 'cobro anulado')

        badge_color = '#198754' if is_approved else ('#fd7e14' if is_refunded else '#dc3545')
        body_html = (
            f"<div style='border-left: 4px solid {badge_color}; padding-left: 10px;'>"
            f"<b>Conciliación Mercado Pago — Op. #{op_num}</b><br/>"
            f"Estado MP: <b style='color:{badge_color};'>{mp_status}</b> ({status_desc})<br/>"
            f"Fecha compra: {buy_date_str} | Herramienta: {tool_raw} | Medio: {pay_method} ({pay_method_desc})<br/>"
            f"Cobro Bruto: <b>${gross_amt:,.0f} CLP</b> | Comisión MP: <b>${fee_amt:,.0f} CLP</b> | "
            f"Reembolsos: <b>${refund_amt:,.0f} CLP</b> | Neto a recibir: <b>${net_amt:,.0f} CLP</b><br/>"
            f"Ítem: {item_desc} | Ref. Externa: <code>{ext_ref or 'N/A'}</code>"
            f"</div>"
        )

        if not dry_run:
            if vals:
                target_order.write(self._filter_existing_fields(vals))
            if is_rejected and 'payment_exception' in target_order._fields:
                target_order.payment_exception = True
            elif is_approved and 'payment_exception' in target_order._fields:
                target_order.payment_exception = False
            target_order.message_post(body=body_html)

        return 'updated', target_order, (
            f"Op MP {op_num} [{mp_status}] -> {target_order.name} "
            f"(Bruto: ${gross_amt:,.0f} | Comisión: ${fee_amt:,.0f} | Neto: ${net_amt:,.0f})"
        )

    # -------------------------------------------------------------------------
    # 4. ÓRDENES DE ALQUILER (rentals-*.csv -> Secuencias parametrizables RO / STKOUT)
    # -------------------------------------------------------------------------
    @api.model
    def upsert_from_bo_rental(self, row, dry_run=False):
        bo_rental_id = _pick(row, ['ID'])
        email = _pick(row, ['Email']).lower()
        qty_raw = _pick(row, ['Prendas']) or '1'
        start_str = _pick(row, ['Fecha del arriendo'])
        return_str = _pick(row, ['Devolución estimada'])
        status_raw = _pick(row, ['Estado']).lower() or 'active'

        if not bo_rental_id and not email:
            return 'skipped', self.browse(), 'Fila de alquiler sin ID ni Email.'

        Partner = self.env['res.partner']
        partner = Partner._find_bo_partner(email=email)
        if not partner and not dry_run:
            partner = Partner.create({
                'name': email,
                'email': email,
                'company_type': 'person',
            })

        start_dt, _ = parse_bo_iso_datetime(start_str)
        return_dt, _ = parse_bo_iso_datetime(return_str)
        cfg = self.env['oulalab.bo.stock.config'].get_active_config()
        is_btl_rental = 'btl' in (bo_rental_id or '').lower()
        if start_dt and not return_dt:
            default_days = (cfg.btl_reservation_days or 3) if is_btl_rental else (cfg.sub_default_duration_days or 15)
            return_dt = start_dt + timedelta(days=default_days)
        try:
            qty = float(qty_raw)
        except ValueError:
            qty = 1.0

        SeqModel = self.env['oulalab.bo.rental.sequence']
        rental_base_dom = SeqModel.build_rental_order_domain()

        existing = self.search(
            rental_base_dom + ['|', ('x_bo_rental_id', '=', bo_rental_id), ('x_studio_bo_rental_id', '=', bo_rental_id)],
            limit=1,
        ) if bo_rental_id else self.browse()

        active_sub = self.browse() if is_btl_rental else self._find_oulaplan_contract(partner=partner)

        prev_ro = self.search(
            rental_base_dom + [
                ('partner_id', '=', partner.id),
                ('state', '!=', 'cancel'),
                ('id', '!=', existing.id or 0),
                ('name', 'not ilike', 'BTL-%'),
            ],
            order='rental_start_date desc, id desc',
            limit=1,
        ) if (partner and not is_btl_rental) else self.browse()

        ciclo = 'BLT' if is_btl_rental else ('Swap' if prev_ro else 'Orden Inicial')

        vals = {
            'x_bo_sync_status': status_raw,
            'x_bo_rental_id': bo_rental_id,
        }
        if bo_rental_id and 'x_studio_bo_rental_id' in self._fields:
            vals['x_studio_bo_rental_id'] = bo_rental_id
        if start_dt and 'rental_start_date' in self._fields:
            vals['rental_start_date'] = start_dt
        if start_dt and 'x_studio_bo_rental_order_date' in self._fields:
            vals['x_studio_bo_rental_order_date'] = start_dt.date()
        if return_dt and 'rental_return_date' in self._fields:
            vals['rental_return_date'] = return_dt
        if active_sub and 'x_studio_suscripcion_id' in self._fields:
            vals['x_studio_suscripcion_id'] = active_sub.id
        if prev_ro and 'x_studio_orden_anterior' in self._fields:
            vals['x_studio_orden_anterior'] = prev_ro.id
        if 'x_studio_ciclo' in self._fields:
            vals['x_studio_ciclo'] = ciclo

        if existing:
            if not dry_run:
                existing.write(self._filter_existing_fields(vals))
                if status_raw in ('cancelled', 'canceled') and existing.state != 'cancel':
                    existing._action_cancel()
                elif status_raw == 'returned' and 'rental_status' in existing._fields:
                    existing.rental_status = 'returned'
            return 'updated', existing, (
                f"Orden {existing.name} actualizada ({email} | Contrato: {active_sub.name if active_sub else 'N/A'} | {ciclo})"
            )

        fallback_prod = self._get_fallback_rental_product()
        line_vals = {
            'product_id': fallback_prod.id,
            'name': f"Arriendo BO ({int(qty)} prendas)",
            'product_uom_qty': qty,
            'price_unit': 0.0,
        }
        if 'is_rental' in self.env['sale.order.line']._fields:
            line_vals['is_rental'] = True

        create_vals = {
            'partner_id': partner.id,
            'is_rental_order': True,
            'order_line': [(0, 0, line_vals)],
            **vals,
        }
        if not dry_run:
            seq_channel = 'btl' if is_btl_rental else 'subscription'
            custom_name = self._resolve_rental_order_name(active_sub=active_sub, channel=seq_channel)
            if custom_name:
                create_vals['name'] = custom_name
            elif is_btl_rental:
                fallback_seq = self.env['ir.sequence'].next_by_code('sale.order') or ''
                if fallback_seq:
                    create_vals['name'] = f"BTL-RO-{fallback_seq}"
            existing = self.create(self._filter_existing_fields(create_vals))
            if status_raw in ('active', 'overdue', 'returned') and existing.state in ('draft', 'sent'):
                existing.action_confirm()
            if status_raw == 'returned' and 'rental_status' in existing._fields:
                existing.rental_status = 'returned'
        return 'created', existing, (
            f"Orden {existing.name if existing else 'Alquiler'} creada ({email} | Contrato: {active_sub.name if active_sub else 'N/A'} | {ciclo})"
        )

    # -------------------------------------------------------------------------
    # 5. DETALLE DE PEDIDOS / ÍTEMS (orders-*.csv -> Líneas unitarias en RO / STKOUT)
    # -------------------------------------------------------------------------
    @api.model
    def upsert_from_bo_order(self, row, dry_run=False):
        order_code = _pick(row, ['Código del pedido'])
        internal_id = _pick(row, ['ID interno'])
        email = _pick(row, ['Email del cliente']).lower()
        client_name = _pick(row, ['Nombre del cliente'])
        status_raw = _pick(row, ['Estado']).lower()
        pay_status = _pick(row, ['Estado de pago']).lower()
        fulfill_status = _pick(row, ['Estado de despacho']).lower()
        channel = _pick(row, ['Canal'])
        created_str = _pick(row, ['Fecha de creación'])

        skus_raw = _pick(row, ['SKUs de ítems'])
        names_raw = _pick(row, ['Nombres de ítems'])
        prices_raw = _pick(row, ['Precio unitario por ítem (CLP)'])

        if not order_code and not internal_id:
            return 'skipped', self.browse(), 'Fila de pedido sin Código ni ID interno.'

        Partner = self.env['res.partner']
        partner = Partner._find_bo_partner(email=email, name=client_name)
        if not partner and not dry_run:
            partner = Partner.create({
                'name': client_name or email,
                'email': email or False,
                'company_type': 'person',
            })

        created_dt, _ = parse_bo_iso_datetime(created_str)
        SeqModel = self.env['oulalab.bo.rental.sequence']
        rental_base_dom = SeqModel.build_rental_order_domain()

        existing = self.search(
            ['|', ('x_bo_order_code', '=', order_code), ('x_studio_bo_order_code', '=', order_code)], limit=1
        ) if order_code else self.browse()

        if not existing and partner and created_dt:
            win_start = created_dt - timedelta(minutes=5)
            win_end = created_dt + timedelta(minutes=5)
            existing = self.search(
                rental_base_dom + [
                    ('partner_id', '=', partner.id),
                    ('rental_start_date', '>=', win_start),
                    ('rental_start_date', '<=', win_end),
                ],
                order='id desc',
                limit=1,
            )

        skus = [s.strip() for s in skus_raw.split(';')] if skus_raw else []
        names = [n.strip() for n in names_raw.split(';')] if names_raw else []
        prices = [p.strip() for p in prices_raw.split(';')] if prices_raw else []

        item_count = max(len(skus), len(names))
        ProductTmpl = self.env['product.template']
        fallback_prod = self._get_fallback_rental_product()

        preferred_ids = set(existing.order_line.mapped('product_id').ids) if existing else set()
        used_in_order = set()
        new_lines = []
        selection_notes = []

        for i in range(item_count):
            sku_tok = skus[i] if i < len(skus) else ''
            item_name = names[i] if i < len(names) else sku_tok
            qty = 1.0
            try:
                raw_price = float(prices[i]) if i < len(prices) and prices[i] else 0.0
            except ValueError:
                raw_price = 0.0

            avail_preferred = preferred_ids - used_in_order
            prod, is_avail, sel_msg = ProductTmpl._select_available_unit_for_bo_sku(
                bo_sku=sku_tok,
                garment_name=item_name,
                qty_needed=qty,
                preferred_product_ids=avail_preferred,
            )
            if prod and prod.id in used_in_order:
                prod, is_avail, sel_msg = ProductTmpl._select_available_unit_for_bo_sku(
                    bo_sku=sku_tok,
                    garment_name=item_name,
                    qty_needed=qty,
                    preferred_product_ids=None,
                )

            if not prod:
                prod = fallback_prod
            else:
                used_in_order.add(prod.id)
            selection_notes.append(sel_msg)

            is_btl_item = '-btl-' in sku_tok.lower() or 'btl' in channel.lower()
            effective_price = (raw_price or prod.list_price or 0.0) if is_btl_item else 0.0
            line_dict = {
                'product_id': prod.id,
                'name': f"[{prod.default_code}] {item_name}" if prod.default_code and prod != fallback_prod else (item_name or prod.display_name),
                'product_uom_qty': qty,
                'price_unit': effective_price,
            }
            if 'is_rental' in self.env['sale.order.line']._fields:
                line_dict['is_rental'] = True
            new_lines.append((0, 0, line_dict))

        is_btl_order = any('-btl-' in s.lower() for s in skus) or 'btl' in channel.lower()
        active_sub = self.browse() if is_btl_order else self._find_oulaplan_contract(partner=partner)
        vals = {
            'x_bo_sync_status': f"{status_raw}|{pay_status}|{fulfill_status}",
            'x_bo_order_code': order_code,
        }
        if is_btl_order and 'x_studio_ciclo' in self._fields:
            vals['x_studio_ciclo'] = 'BLT'
        if order_code and 'x_studio_bo_order_code' in self._fields:
            vals['x_studio_bo_order_code'] = order_code
        if active_sub and 'x_studio_suscripcion_id' in self._fields and not (existing and existing.x_studio_suscripcion_id):
            vals['x_studio_suscripcion_id'] = active_sub.id
        if channel:
            vals['client_order_ref'] = f"{order_code} ({channel})" if order_code else channel

        if existing:
            if not dry_run:
                if new_lines and len(existing.order_line) == 1 and existing.order_line[0].product_id == fallback_prod:
                    if existing.state == 'sale':
                        existing.action_draft()
                    existing.order_line.unlink()
                    vals['order_line'] = new_lines
                    existing.write(self._filter_existing_fields(vals))
                    if status_raw != 'cancelled':
                        existing.action_confirm()
                        existing._trigger_physical_stock_reservation()
                else:
                    existing.write(self._filter_existing_fields(vals))
                    if existing.state == 'sale' and status_raw != 'cancelled':
                        existing._trigger_physical_stock_reservation()
                if is_btl_order and pay_status == 'paid' and existing.state == 'sale' and existing.invoice_status == 'to invoice':
                    try:
                        existing._create_invoices()
                    except Exception:
                        pass
            return 'updated', existing, f"Pedido {order_code} -> {existing.name}: {' | '.join(selection_notes)}"

        create_vals = {
            'partner_id': partner.id,
            'is_rental_order': True,
            'order_line': new_lines or [(0, 0, {'product_id': fallback_prod.id, 'product_uom_qty': 1.0})],
            **vals,
        }
        if created_dt:
            create_vals['date_order'] = created_dt
            if 'rental_start_date' in self._fields:
                create_vals['rental_start_date'] = created_dt
            if 'rental_return_date' in self._fields:
                cfg = self.env['oulalab.bo.stock.config'].get_active_config()
                default_days = (cfg.btl_reservation_days or 3) if is_btl_order else (cfg.sub_default_duration_days or 15)
                create_vals['rental_return_date'] = created_dt + timedelta(days=default_days)
        if not dry_run:
            seq_channel = 'btl' if is_btl_order else 'subscription'
            custom_name = self._resolve_rental_order_name(active_sub=active_sub, channel=seq_channel)
            if custom_name:
                create_vals['name'] = custom_name
            elif is_btl_order:
                fallback_seq = self.env['ir.sequence'].next_by_code('sale.order') or ''
                if fallback_seq:
                    create_vals['name'] = f"BTL-RO-{fallback_seq}"
            existing = self.create(self._filter_existing_fields(create_vals))
            if status_raw in ('confirmed', 'fulfilled', 'pending') and status_raw != 'cancelled' and existing.state in ('draft', 'sent'):
                existing.action_confirm()
                existing._trigger_physical_stock_reservation()
            if is_btl_order and pay_status == 'paid' and existing.state == 'sale' and existing.invoice_status == 'to invoice':
                try:
                    existing._create_invoices()
                except Exception:
                    pass
        comp_alerts = self.env['oulalab.bo.cycle.family.rule'].evaluate_order_composition(names)
        if comp_alerts and existing and not dry_run:
            existing.message_post(body="<br/>".join(f"⚠️ <b>{a}</b>" for a in comp_alerts))
        alert_suffix = f" | {' ; '.join(comp_alerts)}" if comp_alerts else ""
        return 'created', existing, f"Pedido {order_code} creado: {' | '.join(selection_notes)}{alert_suffix}"

    # -------------------------------------------------------------------------
    # 6. RESERVAS DE INVENTARIO (inventory-reservations-*.csv)
    # -------------------------------------------------------------------------
    @api.model
    def upsert_from_bo_inventory_reservation(self, row, dry_run=False):
        res_code = _pick(row, ['Código de reserva'])
        sku = _pick(row, ['SKU'])
        garment_name = _pick(row, ['Prenda'])
        origin_type = _pick(row, ['Origen de la reserva']).lower()
        order_code = _pick(row, ['Código del pedido'])
        rental_uuid = _pick(row, ['Arriendo asociado'])
        rental_state = _pick(row, ['Estado del arriendo']).lower()
        return_code = _pick(row, ['Código de devolución'])
        return_state = _pick(row, ['Estado de devolución']).lower()

        if origin_type == 'manual' or (not rental_uuid and not order_code):
            return 'skipped', self.browse(), f"Reserva manual sin pedido/arriendo asociado ({res_code} - {sku})."

        SeqModel = self.env['oulalab.bo.rental.sequence']
        rental_base_dom = SeqModel.build_rental_order_domain()

        order = self.search(
            rental_base_dom + ['|', ('x_bo_rental_id', '=', rental_uuid), ('x_studio_bo_rental_id', '=', rental_uuid)],
            limit=1,
        ) if rental_uuid else self.browse()

        if not order and order_code:
            order = self.search(['|', ('x_bo_order_code', '=', order_code), ('x_studio_bo_order_code', '=', order_code)], limit=1)

        if not order:
            return 'skipped', self.browse(), (
                f"No se encontró orden de alquiler para reserva {res_code} (arriendo={rental_uuid}, pedido={order_code})."
            )

        vals = {}
        if order_code and 'x_bo_order_code' in self._fields and not order.x_bo_order_code:
            vals['x_bo_order_code'] = order_code
        if order_code and 'x_studio_bo_order_code' in self._fields and not order.x_studio_bo_order_code:
            vals['x_studio_bo_order_code'] = order_code
        if return_code:
            vals['x_bo_return_order_id'] = return_code
        if return_state:
            vals['x_bo_return_status'] = return_state
        if rental_state:
            vals['x_bo_sync_status'] = rental_state

        qty = 1.0
        ProductTmpl = self.env['product.template']
        preferred_ids = set(order.order_line.mapped('product_id').ids)
        prod, is_avail, sel_msg = ProductTmpl._select_available_unit_for_bo_sku(
            bo_sku=sku,
            garment_name=garment_name,
            qty_needed=qty,
            preferred_product_ids=preferred_ids,
        )
        fallback_prod = self._get_fallback_rental_product()

        if not dry_run:
            if vals:
                order.write(self._filter_existing_fields(vals))
            if return_state in ('received', 'inspected') and 'rental_status' in order._fields:
                order.rental_status = 'returned'

            if prod:
                has_fallback = len(order.order_line) == 1 and order.order_line[0].product_id == fallback_prod
                already_has_prod = bool(order.order_line.filtered(lambda l: l.product_id == prod))
                if has_fallback or not already_has_prod:
                    was_sale = order.state == 'sale'
                    if was_sale:
                        order.action_draft()
                    if has_fallback:
                        order.order_line.unlink()
                    line_dict = {
                        'order_id': order.id,
                        'product_id': prod.id,
                        'name': f"[{prod.default_code}] {garment_name or prod.name}" if prod.default_code else (garment_name or prod.display_name),
                        'product_uom_qty': qty,
                        'price_unit': 0.0,
                    }
                    if 'is_rental' in self.env['sale.order.line']._fields:
                        line_dict['is_rental'] = True
                    self.env['sale.order.line'].create(line_dict)
                    if (was_sale or rental_state in ('active', 'overdue')) and rental_state != 'cancelled':
                        if order.state in ('draft', 'sent'):
                            order.action_confirm()
                        if rental_state not in ('returned',) and return_state not in ('received', 'inspected'):
                            order._trigger_physical_stock_reservation()
                elif order.state == 'sale' and rental_state in ('active', 'overdue') and return_state not in ('received', 'inspected'):
                    order._trigger_physical_stock_reservation()

        return 'updated', order, (
            f"Reserva {res_code} -> {order.name} | {sel_msg} | Dev={return_state or 'N/A'}"
        )

    # -------------------------------------------------------------------------
    # 7. ÓRDENES DE DEVOLUCIÓN (return-orders-*.csv)
    # -------------------------------------------------------------------------
    @api.model
    def upsert_from_bo_return_order(self, row, dry_run=False):
        ret_id = _pick(row, ['ID'])
        rental_uuid = _pick(row, ['Arriendo'])
        email = _pick(row, ['Email']).lower()
        status_raw = _pick(row, ['Activo', 'Estado']).lower()

        if not rental_uuid and not ret_id:
            return 'skipped', self.browse(), 'Fila de devolución sin ID ni Arriendo.'

        SeqModel = self.env['oulalab.bo.rental.sequence']
        rental_base_dom = SeqModel.build_rental_order_domain()

        order = self.search(
            rental_base_dom + ['|', ('x_bo_rental_id', '=', rental_uuid), ('x_studio_bo_rental_id', '=', rental_uuid)],
            limit=1,
        ) if rental_uuid else self.browse()

        if not order:
            return 'skipped', self.browse(), (
                f"No se encontró orden de alquiler con ID {rental_uuid} ({email})."
            )

        vals = {
            'x_bo_return_order_id': ret_id,
            'x_bo_return_status': status_raw,
        }
        if not dry_run:
            order.write(vals)
            if status_raw in ('received', 'inspected') and 'rental_status' in order._fields:
                order.rental_status = 'returned'
            order.message_post(
                body=f"<b>Devolución BO ({ret_id})</b>: estado actualizado a <b>{status_raw}</b>."
            )
        return 'updated', order, f"Devolución ({status_raw}) vinculada a {order.name}"


    # -------------------------------------------------------------------------
    # 8. WEBHOOK EN TIEMPO REAL MERCADO PAGO (API GET /v1/payments/{payment_id})
    # -------------------------------------------------------------------------
    @api.model
    def process_mercadopago_webhook_payment(self, payment_id):
        import json
        import urllib.error
        import urllib.request

        pay_id_str = str(payment_id or '').strip()
        if not pay_id_str:
            return 'skipped', self.browse(), 'Webhook Mercado Pago sin payment_id.'

        cfg = self.env['oulalab.bo.outbound.config'].get_any_config()
        access_token = (cfg.mp_access_token or '').strip()
        if not access_token:
            return 'error', self.browse(), (
                f"Se recibió notificación de Mercado Pago (payment_id={pay_id_str}), "
                "pero falta configurar el 'Mercado Pago Access Token' en OulaLab BO Sync > Configuración > Webhook Saliente & MP."
            )

        url = f"https://api.mercadopago.com/v1/payments/{pay_id_str}"
        req = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            method='GET',
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                mp_data = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode('utf-8', errors='replace')[:400]
            return 'error', self.browse(), f"Error HTTP {http_err.code} consultando Mercado Pago API: {err_body}"
        except Exception as exc:
            return 'error', self.browse(), f"Error conectando con Mercado Pago API: {exc}"

        status_map = {
            'approved': 'Aprobado',
            'rejected': 'Rechazado',
            'cancelled': 'Cobro anulado',
            'refunded': 'Reembolsado',
            'charged_back': 'Reembolsado',
            'in_process': 'Pendiente',
            'pending': 'Pendiente',
        }
        raw_status = (mp_data.get('status') or '').lower()
        mapped_status = status_map.get(raw_status, raw_status.title())

        tx_amount = float(mp_data.get('transaction_amount') or 0.0)
        tx_details = mp_data.get('transaction_details') or {}
        net_received = float(tx_details.get('net_received_amount') or 0.0)
        fee_details = mp_data.get('fee_details') or []
        total_fees = -sum(float(f.get('amount') or 0.0) for f in fee_details)
        refunded_amt = float(mp_data.get('transaction_amount_refunded') or 0.0)
        ext_ref = (mp_data.get('external_reference') or '').strip()
        payer_email = ((mp_data.get('payer') or {}).get('email') or '').strip().lower()
        desc = (mp_data.get('description') or '').strip()
        pay_method = (mp_data.get('payment_type_id') or '').strip()
        pay_method_id = (mp_data.get('payment_method_id') or '').strip()
        date_approved = (mp_data.get('date_approved') or mp_data.get('date_created') or '').strip()

        # Si external_reference no viene en el pago pero sí payer.email, intentar encontrar el OULAPLAN del cliente
        if not ext_ref and payer_email:
            partner = self.env['res.partner']._find_bo_partner(email=payer_email)
            if partner:
                sub = self._find_oulaplan_contract(partner=partner)
                if sub:
                    ext_ref = sub.x_studio_bo_order_code or sub.name

        normalized_row = {
            'Número de operación': pay_id_str,
            'Fecha de la compra': date_approved,
            'Estado': mapped_status,
            'Descripción del estado': mp_data.get('status_detail') or raw_status,
            'Cobro': tx_amount,
            'Cargos e impuestos': total_fees,
            'Anulaciones y reembolsos': refunded_amt,
            'Total a recibir': net_received if net_received else (tx_amount + total_fees),
            'Herramienta de cobro': 'Webhook API MP',
            'Medio de pago': pay_method,
            'Descripción del medio de pago': pay_method_id,
            'Descripción del ítem': desc,
            'Referencia externa': ext_ref,
        }
        return self.upsert_from_mercadopago_sale(normalized_row, dry_run=False)
