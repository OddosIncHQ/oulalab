# models/bo_backfill_service.py
from datetime import timedelta
from odoo import fields, models


class BoBackfillService(models.AbstractModel):
    _name = 'bo.backfill.service'
    _description = 'Servicio de sincronización histórica BO -> Odoo'

    def _find_matching_order(self, bo_order):
        """
        Busca el pedido en Odoo por prioridad:
        1. Referencia exacta (bo_order_ref o client_order_ref).
        2. Cliente (email o VAT) + ventana de fecha (±1 día) + al menos 1 SKU en común.
        Retorna: (sale.order | False, motivo_error | False)
        """
        SaleOrder = self.env['sale.order'].sudo()
        bo_ref = (bo_order.get('order_ref') or '').strip()

        # Prioridad 1: Match directo por código de pedido BO
        if bo_ref:
            direct = SaleOrder.search([
                '|',
                ('bo_order_ref', '=', bo_ref),
                ('client_order_ref', '=', bo_ref),
            ], limit=2)
            if len(direct) == 1:
                return direct, False
            if len(direct) > 1:
                return False, f'Múltiples pedidos en Odoo coinciden con referencia {bo_ref}.'

        # Prioridad 2: Match compuesto (Cliente + Fecha ±1 día + SKUs en común)
        partner_domain = []
        if bo_order.get('customer_email'):
            partner_domain = [('email', '=ilike', bo_order['customer_email'].strip())]
        elif bo_order.get('customer_vat'):
            partner_domain = [('vat', '=', bo_order['customer_vat'].strip())]

        if not partner_domain or not bo_order.get('order_date'):
            return False, 'Falta cliente o fecha para búsqueda compuesta.'

        partners = self.env['res.partner'].sudo().search(partner_domain)
        if not partners:
            return False, 'Cliente no encontrado en Odoo.'

        order_dt = fields.Datetime.to_datetime(bo_order['order_date'])
        candidates = SaleOrder.search([
            ('partner_id', 'in', partners.ids),
            ('date_order', '>=', order_dt - timedelta(days=1)),
            ('date_order', '<=', order_dt + timedelta(days=1)),
            ('state', '!=', 'cancel'),
        ])

        bo_skus = {
            (line.get('sku') or '').strip()
            for line in bo_order.get('lines', [])
            if line.get('sku')
        }

        matched = candidates.filtered(
            lambda o: bool(
                bo_skus.intersection(
                    set(o.order_line.mapped('product_id.default_code'))
                )
            )
        )

        if len(matched) == 1:
            return matched, False
        if len(matched) > 1:
            return False, f'Ambigüedad: {len(matched)} pedidos candidatos para el cliente en esa fecha.'
        return False, 'Sin coincidencias en Odoo.'

    def sync_historical_orders(self, bo_orders, overwrite=False, dry_run=False, batch_size=50):
        """
        Formato esperado de cada elemento en `bo_orders`:
        {
            'order_ref': 'XXXXXX',
            'rental_id': '98765',
            'customer_email': 'cliente@correo.cl',
            'customer_vat': '12345678-9',
            'order_date': '2026-05-10 14:00:00',
            'lines': [
                {'sku': 'SHT-BYL-MAD-RUCHANG-M-00005', 'garment_id': 'G-101', 'line_id': 'L-501'},
            ],
        }
        """
        summary = {'synced': 0, 'partial': 0, 'unmatched': 0, 'errors': []}

        for idx, bo_order in enumerate(bo_orders, start=1):
            order, error = self._find_matching_order(bo_order)
            if not order:
                summary['unmatched'] += 1
                summary['errors'].append({
                    'bo_ref': bo_order.get('order_ref'),
                    'reason': error,
                })
                continue

            # 1. Preparar actualización de cabecera (sin tocar líneas ni estados)
            header_vals = {}
            if overwrite or not order.bo_order_ref:
                header_vals['bo_order_ref'] = bo_order.get('order_ref')
            if overwrite or not order.bo_rental_id:
                header_vals['bo_rental_id'] = bo_order.get('rental_id')
            if overwrite or not order.client_order_ref:
                header_vals['client_order_ref'] = bo_order.get('order_ref')

            # 2. Cruce de líneas por SKU (default_code)
            bo_lines_by_sku = {
                (l.get('sku') or '').strip(): l
                for l in bo_order.get('lines', [])
                if l.get('sku')
            }

            only_in_odoo = []
            matched_skus = set()

            # Filtrar solo líneas de productos físicos (ignorar secciones, notas o envíos)
            garment_lines = order.order_line.filtered(
                lambda l: not l.display_type and l.product_id.type == 'consu' or l.product_id.is_storable
            )

            for line in garment_lines:
                sku = (line.product_id.default_code or '').strip()
                bo_line = bo_lines_by_sku.get(sku)

                if bo_line:
                    matched_skus.add(sku)
                    line_vals = {'is_manual_odoo_line': False}
                    if overwrite or not line.bo_rental_line_id:
                        line_vals['bo_rental_line_id'] = bo_line.get('line_id')
                    if overwrite or not line.bo_garment_id:
                        line_vals['bo_garment_id'] = bo_line.get('garment_id')

                    if not dry_run:
                        line.sudo().write(line_vals)
                        # Completar también el ID BO en la ficha del producto si estaba vacío
                        if bo_line.get('garment_id') and (overwrite or not line.product_id.product_tmpl_id.bo_garment_id):
                            line.product_id.product_tmpl_id.sudo().write({
                                'bo_garment_id': bo_line['garment_id']
                            })
                else:
                    # Prenda existe en Odoo (ej. agregada manualmente), pero no en BO
                    only_in_odoo.append(sku or line.product_id.display_name)
                    if not dry_run:
                        line.sudo().write({'is_manual_odoo_line': True})

            only_in_bo = list(set(bo_lines_by_sku.keys()) - matched_skus)
            is_partial = bool(only_in_odoo or only_in_bo)

            header_vals.update({
                'bo_sync_status': 'partial' if is_partial else 'synced',
                'bo_last_sync': fields.Datetime.now(),
            })

            if not dry_run:
                order.sudo().write(header_vals)
                if is_partial:
                    msg = (
                        f"<b>Sincronización histórica BO ({bo_order.get('order_ref')}) con diferencias:</b><br/>"
                        f"• Prendas solo en Odoo (marcadas como manuales): {', '.join(only_in_odoo) or 'Ninguna'}<br/>"
                        f"• Prendas solo en BO (no agregadas a Odoo): {', '.join(only_in_bo) or 'Ninguna'}"
                    )
                    order.message_post(body=msg)

            summary['partial' if is_partial else 'synced'] += 1

            # Commit por lotes para evitar bloqueos y timeouts en cargas grandes
            if not dry_run and idx % batch_size == 0:
                self.env.cr.commit()

        return summary
