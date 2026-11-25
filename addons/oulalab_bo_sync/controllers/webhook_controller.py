import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OulalabBoWebhookController(http.Controller):

    def _validate_token(self):
        expected = request.env['ir.config_parameter'].sudo().get_param('oulalab_bo_sync.webhook_secret', default='')
        if not expected:
            return True
        auth_header = request.httprequest.headers.get('Authorization', '')
        api_key = request.httprequest.headers.get('X-Oulalab-Secret', '')
        bearer = auth_header.removeprefix('Bearer ').strip() if auth_header.startswith('Bearer ') else ''
        return expected in (bearer, api_key)

    @http.route('/api/oulalab/bo/webhook', type='http', auth='none', methods=['POST'], csrf=False)
    def handle_bo_webhook(self, **kwargs):
        if not self._validate_token():
            return request.make_response(
                json.dumps({'ok': False, 'error': 'Unauthorized'}),
                headers=[('Content-Type', 'application/json')],
                status=401,
            )

        try:
            raw_body = request.httprequest.data.decode('utf-8') or '{}'
            payload = json.loads(raw_body)
        except Exception as exc:
            return request.make_response(
                json.dumps({'ok': False, 'error': f'Invalid JSON: {exc}'}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        event_type = (payload.get('event') or payload.get('type') or '').strip().lower()
        data = payload.get('data') or payload
        env = request.env(su=True, context={'skip_bo_outbound': True})
        review_param = env['ir.config_parameter'].get_param('oulalab_bo_sync.webhook_review_mode', default='True')
        is_review_mode = str(kwargs.get('review') or payload.get('review') or review_param).lower() in ('1', 'true', 'yes', 'si')

        if is_review_mode:
            event_map = {
                'lead.new': ('leads', 'crm.lead'),
                'lead.created': ('leads', 'crm.lead'),
                'lead.updated': ('leads', 'crm.lead'),
                'customer.created': ('customers', 'res.partner'),
                'customer.updated': ('customers', 'res.partner'),
                'appointment.created': ('appointments', 'calendar.event'),
                'appointment.cancelled': ('appointments', 'calendar.event'),
                'appointment.updated': ('appointments', 'calendar.event'),
                'subscription.created': ('subscriptions', 'sale.order'),
                'subscription.updated': ('subscriptions', 'sale.order'),
                'subscription.cancelled': ('subscriptions', 'sale.order'),
                'payment.received': ('payments', 'sale.order'),
                'payment.failed': ('payments', 'sale.order'),
                'order.created': ('orders', 'sale.order'),
                'order.updated': ('orders', 'sale.order'),
                'rental.created': ('rentals', 'sale.order'),
                'rental.updated': ('rentals', 'sale.order'),
                'rental.return_scheduled': ('return_orders', 'sale.order'),
                'return.updated': ('return_orders', 'sale.order'),
                'inventory.updated': ('inventory', 'product.template'),
                'product.updated': ('garments', 'product.template'),
            }
            if event_type not in event_map:
                return request.make_response(
                    json.dumps({'ok': False, 'error': f'Unsupported event: {event_type}'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400,
                )
            eff_type, target_model = event_map[event_type]
            batch = env['oulalab.bo.staging.batch'].create({
                'source_type': 'webhook',
                'file_name': f'webhook:{event_type}',
                'entity_type': eff_type,
                'auto_create_partner_from_lead': True,
            })
            sline = env['oulalab.bo.staging.line'].create({
                'batch_id': batch.id,
                'row_number': 1,
                'effective_entity_type': eff_type,
                'external_key': event_type,
                'target_res_model': target_model,
                'raw_payload_json': json.dumps(data, ensure_ascii=False),
            })
            sline._run_precheck_validation()
            return request.make_response(
                json.dumps({
                    'ok': True,
                    'queued_for_review': True,
                    'batch_id': batch.id,
                    'validation_status': sline.validation_status,
                    'inconsistencies': sline.inconsistencies_text,
                }),
                headers=[('Content-Type', 'application/json')],
                status=200,
            )

        try:
            if event_type in ('lead.new', 'lead.created', 'lead.updated'):
                action, rec, msg = env['crm.lead'].upsert_from_bo_lead(data, auto_create_partner=True)
                res_model = 'crm.lead'
            elif event_type in ('customer.created', 'customer.updated'):
                action, rec, msg = env['res.partner'].upsert_from_bo_customer(data)
                res_model = 'res.partner'
            elif event_type in ('appointment.created', 'appointment.cancelled', 'appointment.updated'):
                action, rec, msg = env['calendar.event'].upsert_from_bo_appointment(data)
                res_model = 'calendar.event'
            elif event_type in ('subscription.created', 'subscription.updated', 'subscription.cancelled'):
                action, rec, msg = env['sale.order'].upsert_from_bo_subscription(data)
                res_model = 'sale.order'
            elif event_type in ('payment.received', 'payment.failed'):
                action, rec, msg = env['sale.order'].upsert_from_bo_payment(data)
                res_model = 'sale.order'
            elif event_type in ('order.created', 'order.updated'):
                action, rec, msg = env['sale.order'].upsert_from_bo_order(data)
                res_model = 'sale.order'
            elif event_type in ('rental.created', 'rental.updated'):
                action, rec, msg = env['sale.order'].upsert_from_bo_rental(data)
                res_model = 'sale.order'
            elif event_type in ('rental.return_scheduled', 'return.updated'):
                action, rec, msg = env['sale.order'].upsert_from_bo_return_order(data)
                res_model = 'sale.order'
            else:
                return request.make_response(
                    json.dumps({'ok': False, 'error': f'Unsupported event: {event_type}'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400,
                )

            env['oulalab.bo.sync.log'].create({
                'file_name': f'webhook:{event_type}',
                'entity_type': 'webhook_event',
                'state': 'done' if action != 'error' else 'failed',
                'total_rows': 1,
                'created_count': 1 if action == 'created' else 0,
                'updated_count': 1 if action == 'updated' else 0,
                'skipped_count': 1 if action == 'skipped' else 0,
                'error_count': 1 if action == 'error' else 0,
                'line_ids': [(0, 0, {
                    'row_number': 1,
                    'external_key': event_type,
                    'action': action,
                    'res_model': res_model,
                    'res_id': rec.id if rec else 0,
                    'message': msg,
                })],
            })

            return request.make_response(
                json.dumps({'ok': True, 'action': action, 'res_model': res_model, 'res_id': rec.id if rec else 0, 'message': msg}),
                headers=[('Content-Type', 'application/json')],
                status=200,
            )
        except Exception as exc:
            _logger.exception('Error processing OulaLab BO webhook %s', event_type)
            return request.make_response(
                json.dumps({'ok': False, 'error': str(exc)}),
                headers=[('Content-Type', 'application/json')],
                status=500,
            )


    @http.route('/api/oulalab/mp/webhook', type='http', auth='none', methods=['POST', 'GET'], csrf=False)
    def handle_mercadopago_webhook(self, **kwargs):
        """
        Endpoint Webhook oficial para recibir notificaciones IPN / Webhooks directamente desde Mercado Pago.
        URL para configurar en Mercado Pago Developers -> Tus Integraciones -> Webhooks:
        https://odoo.oulalab.com/api/oulalab/mp/webhook
        """
        try:
            raw_body = request.httprequest.data.decode('utf-8') or '{}'
            payload = json.loads(raw_body) if raw_body.strip().startswith('{') else {}
        except Exception:
            payload = {}

        # Mercado Pago envía el ID en payload['data']['id'] (Webhooks v2) o en query params ?id=...&topic=payment (IPN)
        topic = (
            payload.get('type')
            or payload.get('topic')
            or kwargs.get('type')
            or kwargs.get('topic')
            or ''
        ).strip().lower()
        data_obj = payload.get('data') if isinstance(payload.get('data'), dict) else {}
        payment_id = (
            data_obj.get('id')
            or payload.get('id')
            or kwargs.get('data.id')
            or kwargs.get('id')
            or ''
        )

        if topic and topic not in ('payment', 'subscription_authorized_payment', 'merchant_order'):
            return request.make_response(
                json.dumps({'ok': True, 'ignored_topic': topic}),
                headers=[('Content-Type', 'application/json')],
                status=200,
            )

        if not payment_id:
            return request.make_response(
                json.dumps({'ok': True, 'message': 'Ping recibido sin payment_id'}),
                headers=[('Content-Type', 'application/json')],
                status=200,
            )

        env = request.env(su=True, context={'skip_bo_outbound': True})
        try:
            action, rec, msg = env['sale.order'].process_mercadopago_webhook_payment(payment_id)
            env['oulalab.bo.sync.log'].create({
                'file_name': f'mercadopago_webhook:{payment_id}',
                'entity_type': 'mercadopago_sales',
                'state': 'done' if action != 'error' else 'failed',
                'total_rows': 1,
                'created_count': 1 if action == 'created' else 0,
                'updated_count': 1 if action == 'updated' else 0,
                'skipped_count': 1 if action == 'skipped' else 0,
                'error_count': 1 if action == 'error' else 0,
                'line_ids': [(0, 0, {
                    'row_number': 1,
                    'external_key': str(payment_id),
                    'action': action,
                    'res_model': 'sale.order',
                    'res_id': rec.id if rec else 0,
                    'message': msg,
                })],
            })
            return request.make_response(
                json.dumps({'ok': True, 'action': action, 'res_id': rec.id if rec else 0, 'message': msg}),
                headers=[('Content-Type', 'application/json')],
                status=200,
            )
        except Exception as exc:
            _logger.exception('Error processing Mercado Pago webhook payment_id=%s', payment_id)
            return request.make_response(
                json.dumps({'ok': False, 'error': str(exc)}),
                headers=[('Content-Type', 'application/json')],
                status=500,
            )
