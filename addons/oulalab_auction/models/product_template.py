from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    auction_ids = fields.One2many(
        "liquidation.auction", "product_id", string="Subastas"
    )
    auction_count = fields.Integer(
        string="N.º subastas", compute="_compute_auction_count"
    )

    shop_item_ids = fields.One2many(
        "liquidation.shop.item", "product_id", string="Ventas directas"
    )
    shop_item_count = fields.Integer(
        string="N.º ventas directas", compute="_compute_auction_count"
    )
    liquidation_channel = fields.Selection(
        [("none", "Sin liquidar"), ("auction", "En subasta"), ("shop", "En venta directa")],
        string="Canal de liquidación", compute="_compute_auction_count",
    )

    def _compute_auction_count(self):
        from .shop_item import AUCTION_ACTIVE_STATES, SHOP_ACTIVE_STATES
        for product in self:
            product.shop_item_count = len(product.shop_item_ids)
            if any(s.state in SHOP_ACTIVE_STATES for s in product.shop_item_ids):
                product.liquidation_channel = "shop"
            elif any(a.state in AUCTION_ACTIVE_STATES for a in product.auction_ids):
                product.liquidation_channel = "auction"
            else:
                product.liquidation_channel = "none"
        for product in self:
            product.auction_count = len(product.auction_ids)

    def action_open_auction_web(self):
        """Abre la ficha pública de la subasta más reciente de esta prenda."""
        self.ensure_one()
        auction = self.auction_ids.sorted("id", reverse=True)[:1]
        if not auction:
            raise UserError(_("Esta prenda no tiene ninguna subasta asociada."))
        return {
            "type": "ir.actions.act_url",
            "url": "/auctions/%s" % auction.id,
            "target": "new",
        }

    def action_open_shop_items(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Ventas directas"),
            "res_model": "liquidation.shop.item",
            "view_mode": "list,form",
            "domain": [("product_id", "=", self.id)],
            "context": {"default_product_id": self.id},
        }

    def action_open_auctions(self):
        """Abre la lista backend de subastas de esta prenda."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Subastas"),
            "res_model": "liquidation.auction",
            "view_mode": "list,form",
            "domain": [("product_id", "=", self.id)],
        }
