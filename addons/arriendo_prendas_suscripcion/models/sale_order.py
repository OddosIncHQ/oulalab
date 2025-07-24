from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta


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
        """Resetea los cambios usados en el mes para las suscripciones activas."""
        hoy = date.today()
        ordenes = self.search([
            ('x_proxima_fecha_reseteo_cambios', '<=', hoy)
        ])
        for orden in ordenes:
            nueva_fecha = (hoy + relativedelta(months=1)).replace(day=1)
            orden.write({
                'x_cambios_usados_mes': 0,
                'x_proxima_fecha_reseteo_cambios': nueva_fecha,
            })
            _logger = self.env['ir.logging']
            _logger.create({
                'name': 'Reset mensual',
                'type': 'server',
                'level': 'INFO',
                'message': f"Reset mensual aplicado a {orden.name}",
                'path': 'sale.order',
                'func': 'action_reset_monthly_changes',
                'line': 0,
            })
