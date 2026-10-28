from markupsafe import Markup

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    auction_ids = fields.One2many(
        "liquidation.auction", "sale_order_id", string="Subastas"
    )
    # Vínculo permanente con la subasta que originó el pedido. A diferencia de
    # auction_ids, no se pierde cuando la subasta suelta el pedido por no pago.
    auction_origin_id = fields.Many2one(
        "liquidation.auction", string="Subasta de origen",
        readonly=True, copy=False, index=True,
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

    def action_confirm(self):
        """Confirma los pedidos de subasta en el contexto de SU compañía.

        La confirmación automática tras el pago corre como superusuario desde
        el webhook de Mercado Pago, sin la compañía del pedido en el contexto.
        Las reglas de reabastecimiento son por compañía: sin esto, Odoo no ve
        la regla de la compañía del pedido y falla con 'No rule has been found',
        dejando la transacción pagada y el pedido sin confirmar.
        """
        auction_orders = self.filtered(lambda o: o.auction_ids or o.auction_origin_id)
        others = self - auction_orders
        res = True
        for company in auction_orders.company_id:
            batch = auction_orders.filtered(lambda o: o.company_id == company)
            res = super(SaleOrder, batch.with_company(company).with_context(
                allowed_company_ids=[company.id]
            )).action_confirm()
        if others:
            res = super(SaleOrder, others).action_confirm()
        if not self.env.context.get("auction_skip_sync"):
            auction_orders.filtered(lambda o: o.state == "sale")._sync_auction_after_confirm()
        return res

    def _sync_auction_after_confirm(self):
        """Lleva la subasta al estado correcto cuando su pedido se confirma,
        venga del webhook de pago o de una confirmación manual."""
        for order in self:
            auction = order.auction_origin_id or order.auction_ids[:1]
            if not auction:
                continue
            if auction.state == "pending_payment" and auction.sale_order_id == order:
                auction._mark_paid()
            elif auction.state != "sold" or auction.sale_order_id != order:
                auction._restore_award_from_order(order)
