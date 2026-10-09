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

    def _compute_auction_count(self):
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
