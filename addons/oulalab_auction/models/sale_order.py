from markupsafe import Markup

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    auction_ids = fields.One2many(
        "liquidation.auction", "sale_order_id", string="Subastas"
    )
    auction_photo_html = fields.Html(
        string="Foto de la prenda", compute="_compute_auction_photo", sanitize=False
    )

    @api.depends("auction_ids")
    def _compute_auction_photo(self):
        for order in self:
            src = order._get_auction_photo_src()
            order.auction_photo_html = (
                Markup('<img src="%s" style="max-height:180px;border-radius:6px;"/>') % src
                if src else False
            )

    def _get_auction_photo_src(self):
        """Foto para el correo y la ficha: prioridad URL 4→3→2→1, y si no hay
        ninguna, la foto del producto de Alquiler (lo resuelve la subasta)."""
        self.ensure_one()
        if self.auction_ids:
            return self.auction_ids[:1]._get_primary_image_url()
        tmpl = self.order_line[:1].product_id.product_tmpl_id
        if tmpl:
            return "%s/web/image/product.template/%s/image_1024" % (
                self.get_base_url(), tmpl.id)
        return ""
