from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_location_final(self):
        """Destino de la entrega de los pedidos de subasta y venta directa.

        Odoo entrega a la «Ubicación del cliente» de la dirección de despacho. Si esa
        dirección no la tiene asignada, usa la ubicación de clientes por defecto, y
        ninguna regla de OulaLab entrega ahí: el pedido falla con «No se encontró
        ninguna regla de reabastecimiento». Para estos pedidos, si la ubicación del
        cliente no queda dentro de la que atiende la regla, se usa la de la regla.
        """
        location = super()._get_location_final()
        order = self.order_id
        if not (order.liquidation_channel or order.auction_origin_id):
            return location
        target = order._liquidation_customer_location()
        if not target:
            return location
        if not location or not (location.parent_path or "").startswith(target.parent_path or "#"):
            return target
        return location
