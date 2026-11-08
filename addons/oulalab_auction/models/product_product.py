from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # La ficha de variante reutiliza los botones de la plantilla.
    # Delegamos en product.template para no duplicar lógica.
    auction_count = fields.Integer(
        related="product_tmpl_id.auction_count",
        string="N.º subastas",
    )

    def action_open_auctions(self):
        self.ensure_one()
        return self.product_tmpl_id.action_open_auctions()

    def action_open_auction_web(self):
        self.ensure_one()
        return self.product_tmpl_id.action_open_auction_web()

    # La ficha de variante hereda los botones de la plantilla: el de ventas
    # directas también necesita su campo y su acción aquí.
    shop_item_count = fields.Integer(
        related="product_tmpl_id.shop_item_count",
        string="N.º ventas directas",
    )

    def action_open_shop_items(self):
        self.ensure_one()
        return self.product_tmpl_id.action_open_shop_items()
