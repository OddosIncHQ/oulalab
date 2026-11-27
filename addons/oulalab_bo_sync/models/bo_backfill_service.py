import re
from datetime import datetime, timedelta
from odoo import fields, models

UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


class BoBackfillService(models.AbstractModel):
    _name = 'bo.backfill.service'
    _description = 'Servicio de sincronización histórica BO -> Odoo'

    def _parse_iso_utc(self, iso_str):
        """Convierte '2026-11-26T18:12:32.375Z' a datetime naive UTC para Odoo."""
        if not iso_str:
            return False
        clean = str(iso_str).strip().replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean)
        return dt.replace(tzinfo=None)

    def _sku_matches_odoo(self, bo_sku, odoo_line, bo_name=''):
        """
        Compara un ítem del BO contra una línea de Odoo:
        1. Si el BO trae UUID: compara contra bo_garment_id del producto.
        2. Si el BO trae SKU base: compara exacto o por prefijo 'BO_SKU-' (ej. -00003).
        3. Fallback por nombre parcial si el BO trajo UUID y aún no existe bo_garment_id.
        """
        bo_sku = (bo_sku or '').strip()
        product = odoo_line.product_id
        odoo_code = (product.default_code or '').strip()

        if bo_sku:
            if UUID_RE.match(bo_sku):
                if (product.product_tmpl_id.bo_garment_id or '').strip().lower() == bo_sku.lower():
                    return True
            elif odoo_code == bo_sku or odoo_code.startswith(f'{bo_sku}-'):
                return True

        if bo_name and len(bo_name.strip()) >= 5:
            clean_bo = bo_name.strip().lower()
            clean_odoo = (product.name or '').strip().lower()
            if clean_bo in clean_odoo or clean_odoo in clean_bo:
                return True

        return False

    def _find_matching_order(self, bo_order, date_window_days=7):
        SaleOrder = self.env['sale.order'].sudo()
        bo_ref = (bo_order.get('order_ref') or '').strip()
        bo_internal_id = (bo_order.get('internal_id') or '').strip()

        # Prioridad 1: Match directo por Código del pedido o ID interno
        domain = []
        if bo_ref:
            domain = ['|', ('bo_order_ref', '=', bo_ref), ('client_order_ref', '=', bo_ref)]
        if bo_internal_id:
            domain = (
                ['|', ('bo_internal_id', '=', bo_internal_id)] + domain
                if domain
                else [('bo_internal_id', '=', bo_internal_id)]
            )

        if domain:
            direct = SaleOrder.search(domain, limit=2)
            if len(direct) == 1:
                return direct, False
            if len(direct) > 1:
                return False, f'Múltiples pedidos en Odoo coinciden con {bo_ref}.'

        # Prioridad 2: Email cliente + Solo Órdenes de Alquiler + Ventana de fechas
        email = (bo_order.get('customer_email') or '').strip()
        order_dt = self._parse_iso_utc(bo_order.get('order_date'))
        if not email or not order_dt:
            return False, 'Falta email o fecha válida para búsqueda compuesta.'

        partners = self.env['res.partner'].sudo().search([('email', '=ilike', email)])
        if not partners:
            return False, f'Cliente con email {email} no encontrado en Odoo.'

        candidates = SaleOrder.search([
            ('partner_id', 'in', partners.ids),
            ('is_rental_order', '=', True),
            ('date_order', '>=', order_dt - timedelta(days=date_window_days)),
            ('date_order', '<=', order_dt + timedelta(days=date_window_days)),
            ('state', '!=', 'cancel'),
        ])

        if not candidates:
            return False, f'Sin órdenes de alquiler del cliente en ventana de ±{date_window_days} días.'

        bo_lines = bo_order.get('lines', [])
        matched = candidates.filtered(
            lambda o: any(
                self._sku_matches_odoo(bl.get('sku'), ol, bl.get('name', ''))
                for bl in bo_lines
                for ol in o.order_line
                if not ol.display_type and ol.product_id.is_storable
            )
        )

        # Si hay varios candidatos con coincidencia de prendas, priorizar sin bo_order_ref y luego el más cercano
        if len(matched) > 1:
            unsynced = matched.filtered(lambda o: not o.bo_order_ref)
            if len(unsynced) == 1:
                return unsynced, False
            pool = unsynced or matched
            closest = min(pool, key=lambda o: abs((o.date_order - order_dt).total_seconds()))
            return closest, False

        if len(matched) == 1:
            return matched, False

        # Fallback: si solo existe 1 orden de alquiler sin sincronizar en esa ventana
        unsynced_candidates = candidates.filtered(lambda o: not o.bo_order_ref)
        if len(unsynced_candidates) == 1:
            return unsynced_candidates, False

        return False, 'Orden del cliente encontrada en fecha, pero ninguna prenda coincidió por SKU/nombre.'

    def sync_historical_orders(
        self, bo_orders, overwrite=False, dry_run=False, date_window_days=7, batch_size=50
    ):
        summary = {'synced': 0, 'partial': 0, 'unmatched': 0, 'errors': []}

        for idx, bo_order in enumerate(bo_orders, start=1):
            order, error = self._find_matching_order(bo_order, date_window_days=date_window_days)
            if not order:
                summary['unmatched'] += 1
                summary['errors'].append({
                    'bo_ref': bo_order.get('order_ref'),
                    'reason': error,
                })
                continue

            # 1. Cabecera
            header_vals = {}
            field_map = {
                'bo_order_ref': bo_order.get('order_ref'),
                'client_order_ref': bo_order.get('order_ref'),
                'bo_internal_id': bo_order.get('internal_id'),
                'bo_rental_id': bo_order.get('rental_id'),
                'bo_rental_state': bo_order.get('rental_state'),
                'bo_channel': bo_order.get('channel'),
            }
            for fname, val in field_map.items():
                if val and (overwrite or not order[fname]):
                    header_vals[fname] = val

            # 2. Líneas (solo prendas almacenables)
            garment_lines = order.order_line.filtered(
                lambda l: not l.display_type and l.product_id.is_storable
            )
            remaining_bo_lines = list(bo_order.get('lines', []))
            only_in_odoo = []

            for line in garment_lines:
                matched_bo_line = next(
                    (
                        bl for bl in remaining_bo_lines
                        if self._sku_matches_odoo(bl.get('sku'), line, bl.get('name', ''))
                    ),
                    None,
                )
                if matched_bo_line:
                    remaining_bo_lines.remove(matched_bo_line)
                    line_vals = {'is_manual_odoo_line': False}
                    if matched_bo_line.get('line_id') and (overwrite or not line.bo_rental_line_id):
                        line_vals['bo_rental_line_id'] = matched_bo_line['line_id']
                    if matched_bo_line.get('sku') and (overwrite or not line.bo_garment_id):
                        line_vals['bo_garment_id'] = matched_bo_line['sku']

                    if not dry_run:
                        line.sudo().write(line_vals)
                        if UUID_RE.match(matched_bo_line.get('sku') or ''):
                            tmpl = line.product_id.product_tmpl_id
                            if overwrite or not tmpl.bo_garment_id:
                                tmpl.sudo().write({'bo_garment_id': matched_bo_line['sku']})
                else:
                    only_in_odoo.append(line.product_id.default_code or line.product_id.display_name)
                    if not dry_run:
                        line.sudo().write({'is_manual_odoo_line': True})

            only_in_bo = [
                f"{bl.get('sku')} ({bl.get('name')})"
                for bl in remaining_bo_lines
            ]
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
                        f"• Prendas solo en Odoo (manuales): {', '.join(only_in_odoo) or 'Ninguna'}<br/>"
                        f"• Prendas solo en BO (no agregadas a Odoo): {', '.join(only_in_bo) or 'Ninguna'}"
                    )
                    order.message_post(body=msg)

            summary['partial' if is_partial else 'synced'] += 1

            if not dry_run and idx % batch_size == 0:
                self.env.cr.commit()

        return summary
