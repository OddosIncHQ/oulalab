from odoo import models, fields, api, _
from odoo.tools import date_utils
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_max_prendas_permitidas = fields.Integer(string='Máx. Prendas Permitidas')
    x_cambios_permitidos_mes = fields.Integer(string='Cambios Permitidos por Mes')
    x_cambios_usados_mes = fields.Integer(string='Cambios Usados este Mes', readonly=True, copy=False)
    x_proxima_fecha_reseteo_cambios = fields.Date(string='Próxima Fecha de Reseteo', readonly=True, copy=False)

    x_prendas_en_posesion_ids = fields.One2many(
        comodel_name='arriendo.prenda.linea',
        inverse_name='suscripcion_id',
        string='Prendas en Posesión del Cliente',
        domain=[('estado', '=', 'arrendada'), ('active', '=', True)],
        readonly=True,
        copy=False
    )
    x_cantidad_prendas_en_posesion = fields.Integer(
        string='Prendas en Posesión',
        compute='_compute_cantidad_prendas',
        store=True,
        help="Cantidad actual de prendas que el cliente tiene arrendadas y activas."
    )

    @api.depends('x_prendas_en_posesion_ids', 'x_prendas_en_posesion_ids.active')
    def _compute_cantidad_prendas(self):
        for suscripcion in self:
            suscripcion.x_cantidad_prendas_en_posesion = len(suscripcion.x_prendas_en_posesion_ids)

    @api.model
    def action_reset_monthly_changes(self):
        _logger.info("Iniciando cron 'action_reset_monthly_changes'...")
        hoy = fields.Date.context_today(self)
        suscripciones_a_resetear = self.search([
            ('is_subscription', '=', True),
            ('stage_category', '=', 'progress'),
            '|',
            ('x_proxima_fecha_reseteo_cambios', '=', False),
            ('x_proxima_fecha_reseteo_cambios', '<=', hoy)
        ])
        for rec in suscripciones_a_resetear:
            nueva_fecha = date_utils.start_of(hoy, 'month') + relativedelta(months=1)
            rec.write({
                'x_cambios_usados_mes': 0,
                'x_proxima_fecha_reseteo_cambios': nueva_fecha
            })
            _logger.info(f"Reset mensual aplicado a la suscripción {rec.name}.")
            rec.message_post(
                body=_(
                    "✔️ El contador de cambios mensuales ha sido reiniciado automáticamente. Próximo reseteo: %s"
                ) % nueva_fecha.strftime('%d/%m/%Y'),
                subtype_xmlid="mail.mt_note"
            )
        _logger.info("Cron 'action_reset_monthly_changes' finalizado.")

    def _create_rental_picking(self, picking_type, product_ids=None, lot_ids=None):
        """
        Crea un picking de salida (arriendo) o entrada (devolución) para la suscripción.
        picking_type: 'outgoing' o 'incoming'
        """
        self.ensure_one()
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        Lot = self.env['stock.production.lot']
        Product = self.env['product.product']

        # Selección de tipo de operación
        picking_type_ref = 'stock.picking_type_out' if picking_type == 'outgoing' else 'stock.picking_type_in'
        picking_type_obj = self.env.ref(picking_type_ref)

        # Crear el picking
        picking = Picking.create({
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_obj.id,
            'origin': self.name,
            'location_id': picking_type_obj.default_location_src_id.id,
            'location_dest_id': picking_type_obj.default_location_dest_id.id,
        })

        if picking_type == 'outgoing' and product_ids:
            for product_id in product_ids:
                # Buscar un número de serie disponible
                available_lot = Lot.search([
                    ('product_id', '=', product_id),
                    ('quant_ids.quantity', '>', 0),
                    ('quant_ids.location_id.usage', '=', 'internal'),
                    ('id', 'not in', self.env['arriendo.prenda.linea'].search([
                        ('estado', '=', 'arrendada'),
                        ('active', '=', True)
                    ]).mapped('numero_serie_id').ids)
                ], limit=1)

                if not available_lot:
                    raise ValidationError(_("No hay stock disponible para el producto ID %s") % product_id)

                Move.create({
                    'name': self.name,
                    'product_id': product_id,
                    'product_uom_qty': 1,
                    'product_uom': available_lot.product_id.uom_id.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'picking_id': picking.id,
                    'restrict_lot_id': available_lot.id,
                })

                # Registrar línea de arriendo
                self.env['arriendo.prenda.linea'].create({
                    'suscripcion_id': self.id,
                    'prenda_id': available_lot.product_id.id,
                    'numero_serie_id': available_lot.id,
                    'fecha_arriendo': fields.Datetime.now(),
                    'estado': 'arrendada',
                })

                # Incrementar contador de cambios
                self.x_cambios_usados_mes += 1

        elif picking_type == 'incoming' and lot_ids:
            for lot_id in lot_ids:
                lot = Lot.browse(lot_id)
                Move.create({
                    'name': self.name,
                    'product_id': lot.product_id.id,
                    'product_uom_qty': 1,
                    'product_uom': lot.product_id.uom_id.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'picking_id': picking.id,
                    'restrict_lot_id': lot.id,
                })

                # Actualizar línea de arriendo
                linea = self.env['arriendo.prenda.linea'].search([
                    ('numero_serie_id', '=', lot.id),
                    ('suscripcion_id', '=', self.id),
                    ('estado', '=', 'arrendada'),
                    ('active', '=', True)
                ], limit=1)

                if linea:
                    linea.write({
                        'estado': 'devuelta',
                        'fecha_devolucion': fields.Datetime.now(),
                        'active': False
                    })

        return picking

