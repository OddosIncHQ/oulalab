from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_prendas_en_posesion_ids = fields.One2many(
        comodel_name='arriendo_prendas_suscripcion.arriendo_prenda_linea',
        inverse_name='suscripcion_id',
        string='Prendas Arrendadas'
    )
