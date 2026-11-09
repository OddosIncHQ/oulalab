from markupsafe import Markup

from odoo import _, api, fields, models


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
    # Canal de liquidación del pedido (subasta o venta directa). Lo usa la
    # entrega para llegar a la ubicación de clientes que atiende la regla.
    liquidation_channel = fields.Selection(
        [("auction", "Subasta"), ("shop", "Venta directa")],
        string="Canal de liquidación", readonly=True, copy=False, index=True,
    )
    shop_item_ids = fields.One2many(
        "liquidation.shop.item", "sale_order_id", string="Prendas en venta directa"
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
        auction_orders = self.filtered(
            lambda o: o.auction_ids or o.auction_origin_id or o.liquidation_channel
        )
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
            confirmed = auction_orders.filtered(lambda o: o.state == "sale")
            confirmed.filtered(
                lambda o: o.liquidation_channel != "shop")._sync_auction_after_confirm()
            confirmed.filtered(
                lambda o: o.liquidation_channel == "shop")._sync_shop_after_confirm()
        return res

    def _sync_shop_after_confirm(self):
        """Pedido de venta directa confirmado (pago o confirmación manual):
        sus prendas pasan a Vendida. Si alguna ya se vendió a otra persona,
        no se toca y se avisa (posible doble venta)."""
        Item = self.env["liquidation.shop.item"].sudo()
        for order in self:
            for line in order.order_line.filtered("product_id"):
                tmpl = line.product_id.product_tmpl_id
                item = Item.search([("product_id", "=", tmpl.id),
                                    ("state", "in", ("published", "reserved", "sold"))], limit=1)
                if not item:
                    continue  # OulaBag, despacho u otra línea que no es prenda
                if item.state == "sold" and item.sale_order_id == order:
                    continue
                if item.state == "published" or item.sale_order_id == order:
                    item._mark_sold(order)
                    continue
                warning = _(
                    "Atención: el pedido %(order)s se confirmó, pero la prenda %(item)s está "
                    "%(state)s con el pedido %(other)s. Revisar a mano: posible doble venta."
                ) % {"order": order.name, "item": item.name,
                     "state": dict(item._fields["state"].selection).get(item.state),
                     "other": item.sale_order_id.name or "-"}
                order.message_post(body=warning)
                item.message_post(body=warning)

    def _action_cancel(self):
        """Al cancelar un pedido de venta directa, sus prendas reservadas vuelven a publicarse."""
        res = super()._action_cancel()
        for order in self.filtered(lambda o: o.liquidation_channel == "shop"):
            items = order.sudo().shop_item_ids
            items.filtered(lambda i: i.state == "reserved")._release(
                _("Pedido %s cancelado: la prenda vuelve a estar a la venta.") % order.name)
            # Venta anulada después de confirmada: la prenda vuelve a BORRADOR (no se
            # republica sola: primero hay que recibirla de vuelta y revisarla).
            for item in items.filtered(lambda i: i.state == "sold"):
                item.write({"state": "draft", "sale_order_id": False, "buyer_id": False,
                            "reserved_until": False, "sold_date": False})
                item.message_post(body=_(
                    "Venta anulada: se canceló el pedido %s. La prenda vuelve a borrador; "
                    "publícala de nuevo cuando esté de vuelta y revisada.") % order.name)
        return res

    def _liquidation_customer_location(self):
        """Ubicación de clientes a la que entregan las reglas de liquidación.

        1) la configurada en Subastas > Configuración;
        2) si no hay, el destino de la regla de entrega a clientes del almacén del pedido;
        3) si tampoco, cualquier regla activa de entrega a clientes de la compañía.
        """
        self.ensure_one()
        param = self.env["ir.config_parameter"].sudo().get_param(
            "oulalab_shop.customer_location_id")
        Location = self.env["stock.location"].sudo()
        if param and str(param).isdigit():
            loc = Location.browse(int(param)).exists()
            if loc:
                return loc
        Rule = self.env["stock.rule"].sudo()
        base = [("action", "in", ("pull", "pull_push")),
                ("location_dest_id.usage", "=", "customer"),
                ("company_id", "in", (False, self.company_id.id))]
        rule = Rule.search(base + [("warehouse_id", "=", self.warehouse_id.id)], limit=1) \
            or Rule.search(base, limit=1)
        return rule.location_dest_id

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
