from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_oulalab_member = fields.Boolean(
        string="Socio OulaLab",
        compute="_compute_is_oulalab_member",
        store=True,
        help="Suscriptor activo del alquiler. Recibe acceso anticipado (preview) "
        "y menor incremento mínimo de puja en las subastas de liquidación.",
    )

    # NOTE: Ajusta el origen del cálculo a TU modelo real de suscripción.
    # Aquí lo derivamos de tener al menos un pedido de venta confirmado.
    # Si usas 'sale.subscription' o un modelo propio, cambia el @api.depends
    # y la condición interna por el estado 'activo' de ese modelo.
    @api.depends("sale_order_ids.state")
    def _compute_is_oulalab_member(self):
        for partner in self:
            partner.is_oulalab_member = any(
                order.state == "sale" for order in partner.sale_order_ids
            )
