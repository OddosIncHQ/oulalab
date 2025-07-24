# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    """
    Hereda de 'sale.order' para añadir toda la lógica de negocio
    relacionada con la suscripción de arriendo.
    """
    _inherit = 'sale.order'

    # --- Campos para la gestión de límites de la suscripción ---

    x_max_prendas_permitidas = fields.Integer(
        string='Máx. Prendas Permitidas',
        help="Número máximo de prendas que el cliente puede tener en su posesión simultáneamente."
    )
    x_cambios_permitidos_mes = fields.Integer(
        string='Cambios Permitidos por Mes',
        help="Número de cambios o nuevos envíos de prendas que el cliente puede solicitar al mes."
    )
    x_cambios_usados_mes = fields.Integer(
        string='Cambios Usados este Mes',
        readonly=True,
        copy=False, # Este valor no debe copiarse al duplicar una suscripción
        help="Contador de los cambios ya utilizados en el ciclo de facturación actual."
    )
    x_proxima_fecha_reseteo_cambios = fields.Date(
        string='Próxima Fecha de Reseteo',
        readonly=True,
        copy=False,
        help="Fecha en la que el contador de 'cambios usados' se reiniciará a cero."
    )

    # --- Campos para el seguimiento de las prendas arrendadas ---

    x_prendas_en_posesion_ids = fields.One2many(
        comodel_name='arriendo.prenda.linea', # Nombre estandarizado
        inverse_name='suscripcion_id',
        string='Prendas en Posesión del Cliente',
        domain=[('estado', '=', 'arrendada'), ('active', '=', True)],
        readonly=True,
        copy=False
    )

    x_cantidad_prendas_en_posesion = fields.Integer(
        string='Prendas en Posesión',
        compute='_compute_cantidad_prendas',
        store=True, # Guardar en BBDD para mejor rendimiento
        help="Cantidad actual de prendas que el cliente tiene arrendadas y activas."
    )

    @api.depends('x_prendas_en_posesion_ids', 'x_prendas_en_posesion_ids.active')
    def _compute_cantidad_prendas(self):
        """
        Calcula la cantidad de prendas en posesión basándose en las líneas de arriendo activas.
        """
        for suscripcion in self:
            # El dominio del campo ya filtra, pero esta es una doble confirmación.
            suscripcion.x_cantidad_prendas_en_posesion = len(suscripcion.x_prendas_en_posesion_ids)

    # --- Acción del Cron Job ---

    @api.model
    def action_reset_monthly_changes(self):
        """
        Método para ser llamado por una Acción Planificada (Cron Job).
        Busca todas las suscripciones activas cuya fecha de reseteo ha pasado y
        reinicia su contador de cambios.
        """
        _logger.info("Iniciando cron 'action_reset_monthly_changes'...")
        hoy = fields.Date.context_today(self)
        
        # Busca suscripciones en progreso que necesiten un reseteo.
        suscripciones_a_resetear = self.search([
            ('is_subscription', '=', True),
            ('stage_category', '=', 'progress'), # 'progress' es la categoría para etapas en curso
            '|',
            ('x_proxima_fecha_reseteo_cambios', '=', False),
            ('x_proxima_fecha_reseteo_cambios', '<=', hoy)
        ])

        for rec in suscripciones_a_resetear:
            # Calcula el primer día del mes siguiente para la nueva fecha de reseteo.
            nueva_fecha = date_utils.start_of(hoy, 'month') + date_utils.relativedelta(months=1)
            
            rec.write({
                'x_cambios_usados_mes': 0,
                'x_proxima_fecha_reseteo_cambios': nueva_fecha
            })
            
            # Log y mensaje en el chatter
            _logger.info(f"Reset mensual aplicado a la suscripción {rec.name}.")
            rec.message_post(
                body=_(
                    "✔️ El contador de cambios mensuales ha sido reiniciado automáticamente. Próximo reseteo: %s"
                ) % nueva_fecha.strftime('%d/%m/%Y'),
                subtype_xmlid="mail.mt_note"
            )
        _logger.info("Cron 'action_reset_monthly_changes' finalizado.")


    # --- Métodos Auxiliares ---
    
    def _create_rental_picking(self, picking_type_code, product_ids=None, lot_ids=None):
        """
        Crea y devuelve un albarán (stock.picking) para arriendos o devoluciones.
        :param picking_type_code: 'outgoing' (envío) o 'incoming' (devolución).
        :param product_ids: Lista de IDs de productos a enviar.
        :param lot_ids: Lista de IDs de lotes/series a devolver.
        """
        self.ensure_one()
        StockPicking = self.env['stock.picking']
        
        if picking_type_code == 'outgoing':
            picking_type = self.env.ref('stock.picking_type_out')
            location_src = picking_type.default_location_src_id
            location_dest = self.partner_id.property_stock_customer
        elif picking_type_code == 'incoming':
            picking_type = self.env.ref('stock.picking_type_in')
            location_src = self.partner_id.property_stock_customer
            location_dest = picking_type.default_location_dest_id
        else:
            raise ValidationError(_("Tipo de albarán no válido: %s") % picking_type_code)

        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': location_src.id,
            'location_dest_id': location_dest.id,
            'origin': self.name,
            'x_suscripcion_id': self.id,
        }
        picking = StockPicking.create(picking_vals)

        # Crear líneas de movimiento
        moves_vals = []
        if product_ids:
             for product_id in self.env['product.product'].browse(product_ids):
                moves_vals.append({
                    'name': product_id.display_name,
                    'product_id': product_id.id,
                    'product_uom_qty': 1,
                    'product_uom': product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': location_src.id,
                    'location_dest_id': location_dest.id,
                })
        elif lot_ids:
            for lot in self.env['stock.lot'].browse(lot_ids):
                moves_vals.append({
                    'name': lot.product_id.display_name,
                    'product_id': lot.product_id.id,
                    'product_uom_qty': 1,
                    'product_uom': lot.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': location_src.id,
                    'location_dest_id': location_dest.id,
                })

        self.env['stock.move'].create(moves_vals)
        return picking
