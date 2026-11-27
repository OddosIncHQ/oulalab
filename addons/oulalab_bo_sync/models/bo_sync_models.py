# models/bo_sync_models.py
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    bo_order_ref = fields.Char(
        string='Código Pedido BO',
        index=True,
        copy=False,
    )
    bo_rental_id = fields.Char(
        string='ID Arriendo BO',
        index=True,
        copy=False,
    )
    bo_sync_status = fields.Selection(
        selection=[
            ('pending', 'Pendiente'),
            ('synced', 'Sincronizado'),
            ('partial', 'Parcial (Diferencia de prendas)'),
            ('manual_review', 'Revisión manual'),
        ],
        string='Estado Sync BO',
        default='pending',
        copy=False,
    )
    bo_last_sync = fields.Datetime(
        string='Última sincronización BO',
        copy=False,
    )
    
    bo_internal_id = fields.Char(string='ID Interno Pedido BO', index=True, copy=False)
    bo_rental_state = fields.Char(string='Estado Arriendo BO', copy=False)
    bo_channel = fields.Char(string='Canal BO', copy=False)



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bo_rental_line_id = fields.Char(
        string='ID Línea BO',
        index=True,
        copy=False,
    )
    bo_garment_id = fields.Char(
        string='ID Prenda BO',
        index=True,
        copy=False,
    )
    is_manual_odoo_line = fields.Boolean(
        string='Agregada manualmente en Odoo',
        default=False,
        copy=False,
        help='Indica que la prenda existe en Odoo pero no figuraba en el pedido original del BO.',
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bo_garment_id = fields.Char(
        string='ID Prenda BO',
        index=True,
        copy=False,
    )
