import json
import logging
import re
import urllib.error
import urllib.request
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OulalabBoOutboundConfig(models.Model):
    _name = 'oulalab.bo.outbound.config'
    _description = 'Configuración de Webhook Saliente (Odoo -> BackOffice) y Mercado Pago'

    name = fields.Char(string='Nombre Integración', required=True, default='Webhook Saliente BackOffice OulaLab')
    active = fields.Boolean(string='Habilitado', default=False)
    target_url = fields.Char(
        string='URL Webhook Destino (BO)',
        default='https://integration-service-production-1b6b.up.railway.app/webhooks/odoo',
        help='Endpoint POST del BackOffice (integration-service) que recibirá los eventos desde Odoo.',
    )
    auth_header_name = fields.Char(
        string='Nombre Cabecera Auth',
        default='Authorization',
        help='Ej: Authorization o X-Oulalab-Secret',
    )
    auth_token = fields.Char(
        string='Token / Secreto Bearer',
        help='Si la cabecera es Authorization y el token no empieza con Bearer, se enviará como "Bearer <token>".',
    )
    timeout_seconds = fields.Integer(string='Timeout (segundos)', default=10)
    send_immediately = fields.Boolean(
        string='Envío Inmediato (Síncrono con respaldo en Cola)',
        default=True,
        help='Si está activo, intenta enviar al instante al ocurrir el cambio; si falla, queda en cola para reintento automático.',
    )
    notify_stock_changes = fields.Boolean(string='Notificar Cambios de Stock (inventory.updated)', default=True)
    notify_product_changes = fields.Boolean(string='Notificar Cambios en Prendas (product.updated)', default=True)
    notify_rental_changes = fields.Boolean(string='Notificar Cambios en Arriendos / Devoluciones (rental.updated)', default=True)

    # Parámetros Mercado Pago API (para Webhook en tiempo real desde Mercado Pago)
    mp_access_token = fields.Char(
        string='Mercado Pago Access Token (APP_USR-...)',
        help='Token privado de producción de Mercado Pago para consultar el detalle de pagos recibidos por webhook (/api/oulalab/mp/webhook).',
    )
    mp_webhook_secret = fields.Char(
        string='Mercado Pago Webhook Secret (Firma x-signature)',
        help='Clave secreta configurada en Tus Integraciones > Webhooks de Mercado Pago (opcional).',
    )

    @api.model
    def get_active_config(self):
        return self.search([('active', '=', True)], limit=1)

    @api.model
    def get_any_config(self):
        cfg = self.search([], limit=1)
        if not cfg:
            cfg = self.create({'name': 'Webhook Saliente BackOffice OulaLab', 'active': False})
        return cfg

    def _build_headers(self):
        self.ensure_one()
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Odoo-19-OulaLab-Sync/1.0',
        }
        if self.auth_token:
            hname = (self.auth_header_name or 'Authorization').strip()
            tok = self.auth_token.strip()
            if hname.lower() == 'authorization' and not tok.lower().startswith(('bearer ', 'basic ')):
                tok = f'Bearer {tok}'
            headers[hname] = tok
        return headers

    def action_test_webhook(self):
        self.ensure_one()
        if not self.target_url:
            raise UserError('Debe configurar la URL Webhook Destino antes de probar.')
        payload = {
            'event': 'ping.test',
            'source': 'odoo-19',
            'timestamp': fields.Datetime.now().isoformat() + 'Z',
            'data': {
                'message': 'Prueba de conexión saliente desde Odoo 19 OulaLab BO Sync',
                'company': self.env.company.name,
            },
        }
        q_item = self.env['oulalab.bo.outbound.queue'].create({
            'event_type': 'ping.test',
            'bo_sku': 'TEST-PING',
            'payload_json': json.dumps(payload, ensure_ascii=False, indent=2),
        })
        q_item.action_send_now()
        if q_item.state == 'sent':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Webhook Saliente Exitoso',
                    'message': f'Respuesta HTTP {q_item.response_code}: {q_item.response_body or "OK"}',
                    'type': 'success',
                    'sticky': False,
                },
            }
        raise UserError(f"Error al enviar webhook de prueba (HTTP {q_item.response_code}): {q_item.error_message}")

    def action_push_all_inventory_snapshot(self):
        self.ensure_one()
        if not self.target_url:
            raise UserError('Debe configurar la URL Webhook Destino.')
        ExportWiz = self.env['oulalab.bo.export.wizard'].create({'export_type': 'inventory_import'})
        grouped = ExportWiz._get_grouped_bo_products()
        count = 0
        for bo_sku in sorted(grouped.keys()):
            self.env['oulalab.bo.outbound.queue'].enqueue_sku_stock_update(bo_sku, dispatch_now=False)
            count += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Snapshot Encolado',
                'message': f'Se encolaron {count} SKUs consolidados para envío al BackOffice.',
                'type': 'info',
                'sticky': False,
            },
        }


class OulalabBoOutboundQueue(models.Model):
    _name = 'oulalab.bo.outbound.queue'
    _description = 'Cola de Eventos Salientes hacia BackOffice OulaLab'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Referencia', required=True, readonly=True, default='Nuevo')
    event_type = fields.Char(string='Evento', required=True, readonly=True, index=True)
    bo_sku = fields.Char(string='SKU BO / Referencia', readonly=True, index=True)
    payload_json = fields.Text(string='Payload JSON', readonly=True)
    state = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('sent', 'Enviado'),
            ('failed', 'Error / Reintento'),
        ],
        string='Estado',
        default='pending',
        readonly=True,
        index=True,
    )
    attempts = fields.Integer(string='Intentos', default=0, readonly=True)
    response_code = fields.Integer(string='HTTP Status', readonly=True)
    response_body = fields.Text(string='Respuesta BO', readonly=True)
    error_message = fields.Char(string='Detalle Error', readonly=True)
    sent_at = fields.Datetime(string='Enviado el', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Nuevo':
                vals['name'] = f"OUT-{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return super().create(vals_list)

    @api.model
    def _compute_bo_sku_snapshot(self, bo_sku):
        Product = self.env['product.product']
        units = Product.search([
            ('active', '=', True),
            ('rent_ok', '=', True),
            '|',
            ('x_bo_sku', '=ilike', bo_sku),
            '|',
            ('default_code', '=ilike', bo_sku),
            ('default_code', '=ilike', f'{bo_sku}-%'),
        ], order='default_code asc, id asc')
        if not units:
            return None

        stock_cfg = self.env['oulalab.bo.stock.config'].get_active_config()
        avail_locs = stock_cfg.get_available_locations_tree()
        fleet_locs = stock_cfg.get_fleet_locations_tree()
        Quant = self.env['stock.quant']

        fleet_quants = Quant.search([('product_id', 'in', units.ids), ('location_id', 'in', fleet_locs.ids)])
        avail_quants = Quant.search([('product_id', 'in', units.ids), ('location_id', 'in', avail_locs.ids)])

        stocked_qty = int(round(sum(max(0.0, q.quantity) for q in fleet_quants)))
        in_stock_qty = int(round(sum(max(0.0, q.quantity - q.reserved_quantity) for q in avail_quants)))
        if in_stock_qty > stocked_qty:
            stocked_qty = in_stock_qty
        reserved_qty = max(0, stocked_qty - in_stock_qty)

        rep = units[0].product_tmpl_id
        garment_name = (
            (rep.x_studio_descripcion if 'x_studio_descripcion' in rep._fields else '')
            or rep.name
            or bo_sku
        ).strip()
        variant_title = (
            (rep.x_studio_talla if 'x_studio_talla' in rep._fields else '')
            or (bo_sku.split('-')[-1] if '-' in bo_sku else 'UNQ')
        ).strip()

        serialized_units = []
        for u in units:
            u_avail = sum(
                max(0.0, q.quantity - q.reserved_quantity)
                for q in avail_quants.filtered(lambda q: q.product_id == u)
            )
            serialized_units.append({
                'default_code': u.default_code or '',
                'barcode': u.barcode or '',
                'available': int(round(u_avail)),
            })

        return {
            'sku': bo_sku,
            'garment_name': garment_name,
            'variant_title': variant_title,
            'stocked': stocked_qty,
            'reserved': reserved_qty,
            'in_stock': in_stock_qty,
            'operational_status': rep.x_bo_operational_status or ('Disponible' if in_stock_qty > 0 else 'Sin stock'),
            'units': serialized_units,
        }

    @api.model
    def enqueue_sku_stock_update(self, bo_sku, event_type='inventory.updated', dispatch_now=None):
        cfg = self.env['oulalab.bo.outbound.config'].get_active_config()
        if not cfg or not cfg.target_url:
            return self.browse()
        if event_type == 'inventory.updated' and not cfg.notify_stock_changes:
            return self.browse()
        if event_type == 'product.updated' and not cfg.notify_product_changes:
            return self.browse()

        snapshot = self._compute_bo_sku_snapshot(bo_sku)
        if not snapshot:
            return self.browse()

        # Evitar duplicar eventos pendientes idénticos en la misma transacción
        pending = self.search([
            ('state', '=', 'pending'),
            ('event_type', '=', event_type),
            ('bo_sku', '=', bo_sku),
        ], limit=1)

        payload = {
            'event': event_type,
            'source': 'odoo-19',
            'timestamp': fields.Datetime.now().isoformat() + 'Z',
            'data': snapshot,
        }
        payload_str = json.dumps(payload, ensure_ascii=False, indent=2)

        if pending:
            pending.write({'payload_json': payload_str})
            rec = pending
        else:
            rec = self.create({
                'event_type': event_type,
                'bo_sku': bo_sku,
                'payload_json': payload_str,
            })

        should_send = cfg.send_immediately if dispatch_now is None else dispatch_now
        if should_send:
            rec.action_send_now()
        return rec

    @api.model
    def enqueue_rental_event(self, order, event_type='rental.updated'):
        cfg = self.env['oulalab.bo.outbound.config'].get_active_config()
        if not cfg or not cfg.target_url or not cfg.notify_rental_changes:
            return self.browse()

        payload = {
            'event': event_type,
            'source': 'odoo-19',
            'timestamp': fields.Datetime.now().isoformat() + 'Z',
            'data': {
                'odoo_order_name': order.name,
                'bo_rental_id': order.x_bo_rental_id or (order.x_studio_bo_rental_id if 'x_studio_bo_rental_id' in order._fields else ''),
                'bo_order_code': order.x_bo_order_code or (order.x_studio_bo_order_code if 'x_studio_bo_order_code' in order._fields else ''),
                'rental_status': order.rental_status if 'rental_status' in order._fields else order.state,
                'return_status': order.x_bo_return_status or '',
                'customer_email': order.partner_id.email or '',
                'items': [
                    {
                        'default_code': l.product_id.default_code or '',
                        'barcode': l.product_id.barcode or '',
                        'bo_sku': re.sub(r'-\d{5}$', '', (l.product_id.default_code or '')),
                        'qty': l.product_uom_qty,
                    }
                    for l in order.order_line
                ],
            },
        }
        rec = self.create({
            'event_type': event_type,
            'bo_sku': order.name,
            'payload_json': json.dumps(payload, ensure_ascii=False, indent=2),
        })
        if cfg.send_immediately:
            rec.action_send_now()
        return rec

    def action_send_now(self):
        cfg = self.env['oulalab.bo.outbound.config'].get_active_config()
        if not cfg or not cfg.target_url:
            return False

        headers = cfg._build_headers()
        timeout = cfg.timeout_seconds or 10

        for rec in self:
            body_bytes = (rec.payload_json or '{}').encode('utf-8')
            req = urllib.request.Request(cfg.target_url, data=body_bytes, headers=headers, method='POST')
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status_code = resp.getcode()
                    resp_text = resp.read().decode('utf-8', errors='replace')[:1000]
                    rec.write({
                        'state': 'sent',
                        'attempts': rec.attempts + 1,
                        'response_code': status_code,
                        'response_body': resp_text,
                        'error_message': False,
                        'sent_at': fields.Datetime.now(),
                    })
            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode('utf-8', errors='replace')[:500]
                rec.write({
                    'state': 'failed',
                    'attempts': rec.attempts + 1,
                    'response_code': http_err.code,
                    'error_message': f"HTTP {http_err.code}: {err_body}",
                })
            except Exception as exc:
                rec.write({
                    'state': 'failed',
                    'attempts': rec.attempts + 1,
                    'error_message': str(exc)[:250],
                })
        return True

    @api.model
    def cron_process_outbound_queue(self, limit=50):
        cfg = self.env['oulalab.bo.outbound.config'].get_active_config()
        if not cfg or not cfg.target_url:
            return
        items = self.search([
            ('state', 'in', ('pending', 'failed')),
            ('attempts', '<', 5),
        ], order='id asc', limit=limit)
        if items:
            items.action_send_now()


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('quantity', 'reserved_quantity', 'location_id')):
            if not self.env.context.get('skip_bo_outbound'):
                self._notify_bo_stock_change()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_bo_outbound'):
            records._notify_bo_stock_change()
        return records

    def _notify_bo_stock_change(self):
        skus = set()
        for q in self:
            prod = q.product_id
            if not prod or not prod.rent_ok:
                continue
            tmpl = prod.product_tmpl_id
            bo_sku = (
                (tmpl.x_bo_sku if 'x_bo_sku' in tmpl._fields else '')
                or re.sub(r'-\d{5}$', '', (prod.default_code or ''))
            ).strip()
            if bo_sku:
                skus.add(bo_sku)
        Queue = self.env['oulalab.bo.outbound.queue'].sudo()
        for sku in skus:
            Queue.enqueue_sku_stock_update(sku, event_type='inventory.updated')
