from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_max_prendas_permitidas = fields.Integer(string='Máximo de prendas permitidas')
    x_cambios_permitidos_mes = fields.Integer(string='Cambios permitidos por mes')
    x_cambios_usados_mes = fields.Integer(string='Cambios usados este mes')
    x_proxima_fecha_reseteo_cambios = fields.Date(string='Fecha de reseteo de cambios')
    x_cantidad_prendas_en_posesion = fields.Integer(string='Cantidad actual de prendas')

    x_prendas_en_posesion_ids = fields.One2many(
        comodel_name='arriendo_prendas_suscripcion.arriendo_prenda_linea',
        inverse_name='suscripcion_id',
        string='Prendas Arrendadas'
    )

    @api.model
    def action_reset_monthly_changes(self):
        """Resetea los cambios usados en el mes para suscripciones activas (state = 'sale')."""
        hoy = date.today()
        nueva_fecha = (hoy + relativedelta(months=1)).replace(day=1)
        ordenes = self.search([
            ('x_proxima_fecha_reseteo_cambios', '<=', hoy),
            ('state', '=', 'sale')
        ])
        for orden in ordenes:
            orden.write({
                'x_cambios_usados_mes': 0,
                'x_proxima_fecha_reseteo_cambios': nueva_fecha,
            })
            # Log en servidor
            _logger.info("Reset mensual aplicado a %s", orden.name)

            # Mensaje en el chatter
            orden.message_post(
                body=f"✔️ Cambios usados este mes fueron reiniciados automáticamente el {hoy.strftime('%Y-%m-%d')}. "
                     f"Próximo reseteo: {nueva_fecha.strftime('%Y-%m-%d')}",
                subtype_xmlid="mail.mt_note"
            )
