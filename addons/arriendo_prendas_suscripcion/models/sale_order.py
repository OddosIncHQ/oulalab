from odoo import models, fields, api

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
