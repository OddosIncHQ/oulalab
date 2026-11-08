import logging
import re
from datetime import timedelta

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Una prenda (1 producto = 1 variante = 1 unidad) vive en UN solo canal.
AUCTION_ACTIVE_STATES = ("draft", "published", "live", "pending_payment", "sold")
SHOP_ACTIVE_STATES = ("draft", "published", "reserved", "sold")

PARAM_PREFIX = "oulalab_shop."
# Valores por defecto (CLP, IVA incluido). Se cambian en Subastas > Configuración.
SHOP_DEFAULTS = {
    "oulabag_price": 39990,            # precio del OulaBag en el checkout
    "oulabag_reference_price": 49990,  # precio "normal" que se muestra tachado
    "oulabag_min_cart": 100000,        # compra mínima en prendas para ofrecerlo
    "oulabag_floor_price": 32990,      # piso: costo puesto en Chile + IVA (lote aéreo)
    "reservation_minutes": 60,         # minutos que una prenda queda reservada para pagar
    "pending_grace_minutes": 120,      # margen extra si hay un pago en línea pendiente
    "shipping_fee": 0,                 # despacho (0 = gratis en comunas habilitadas)
}


def shop_param(env, key):
    """Parámetro numérico de la tienda, con su valor por defecto."""
    raw = env["ir.config_parameter"].sudo().get_param(PARAM_PREFIX + key)
    try:
        return int(float(raw)) if raw not in (None, False, "") else SHOP_DEFAULTS[key]
    except (TypeError, ValueError):
        return SHOP_DEFAULTS[key]


def fmt_clp(amount):
    return "$" + "{:,.0f}".format(amount or 0).replace(",", ".")


class LiquidationShopItem(models.Model):
    _name = "liquidation.shop.item"
    _description = "Prenda en venta directa"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "published_date desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one(
        "product.template", string="Prenda", required=True, ondelete="restrict",
        tracking=True, help="Cada prenda es un product.template único (1 unidad).",
    )
    default_code = fields.Char(related="product_id.default_code", string="Código", store=True)
    barcode = fields.Char(related="product_id.barcode", string="Código de barras")
    image_128 = fields.Image(related="product_id.image_128", string="Imagen")

    image_url_1 = fields.Char(string="URL imagen 1")
    image_url_2 = fields.Char(string="URL imagen 2")
    image_url_3 = fields.Char(string="URL imagen 3")
    image_url_4 = fields.Char(string="URL imagen 4")
    image_url_5 = fields.Char(string="URL imagen 5")
    image_url_6 = fields.Char(string="URL imagen 6")
    image_url_7 = fields.Char(string="URL imagen 7")
    image_url_8 = fields.Char(string="URL imagen 8")
    image_url_9 = fields.Char(string="URL imagen 9")
    image_url_10 = fields.Char(string="URL imagen 10")

    reason = fields.Selection(
        [("worn", "Muy usada"), ("off_season", "Fuera de temporada"),
         ("dead_stock", "Baja rotación"), ("other", "Otro")],
        string="Motivo de retiro", default="off_season",
    )
    description = fields.Html(string="Descripción pública")

    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id.id, required=True,
    )
    price = fields.Monetary(
        string="Precio de venta (IVA incl.)", currency_field="currency_id", tracking=True,
        help="Precio final que paga la clienta, con IVA incluido.",
    )
    retail_price = fields.Monetary(
        string="Precio retail de referencia", currency_field="currency_id",
        help="Precio de la prenda nueva en tienda; se muestra tachado como referencia.",
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("published", "Publicada"),
            ("reserved", "Reservada (pago pendiente)"),
            ("sold", "Vendida"),
            ("withdrawn", "Retirada"),
        ],
        default="draft", tracking=True, required=True, copy=False,
    )
    published_date = fields.Datetime(string="Publicada el", readonly=True, copy=False)
    sale_order_id = fields.Many2one("sale.order", string="Pedido", readonly=True, copy=False)
    buyer_id = fields.Many2one("res.partner", string="Compradora", readonly=True, copy=False)
    reserved_until = fields.Datetime(string="Reservada hasta", readonly=True, copy=False)
    sold_date = fields.Datetime(string="Vendida el", readonly=True, copy=False)

    # Catálogo: mismos atributos de Studio que usa la subasta.
    brand = fields.Char(related="product_id.x_studio_marca", string="Marca", store=True)
    categ = fields.Many2one(related="product_id.categ_id", string="Tipo de prenda", store=True)
    occasion_ids = fields.Many2many(related="product_id.x_studio_ocasiones", string="Ocasión")
    size = fields.Char(compute="_compute_size", string="Talla")
    web_title = fields.Char(compute="_compute_web_title", string="Título web")
    web_description = fields.Html(compute="_compute_web_title", string="Descripción web")
    materials = fields.Char(compute="_compute_product_info", string="Materialidad")
    care_tips = fields.Text(compute="_compute_product_info", string="Tips de cuidado")
    discount_pct = fields.Integer(compute="_compute_discount", string="% bajo retail")

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends("product_id", "product_id.name", "product_id.default_code")
    def _compute_name(self):
        for rec in self:
            prod = rec.product_id
            if not prod:
                rec.name = _("Venta: (sin prenda)")
            elif prod.default_code:
                rec.name = _("Venta [%s]: %s") % (prod.default_code, prod.name)
            else:
                rec.name = _("Venta: %s") % prod.name

    def _compute_size(self):
        for rec in self:
            prod = rec.product_id
            value = prod.x_studio_talla if prod and "x_studio_talla" in prod._fields else False
            rec.size = str(value) if value else False

    def _compute_web_title(self):
        for rec in self:
            prod = rec.product_id
            seo = prod.seo_name if prod and "seo_name" in prod._fields else False
            desc = rec.description or ""
            m = re.search(r"<strong>(.*?)</strong>", desc, re.S)
            if seo:
                rec.web_title, rec.web_description = seo, desc
            elif m:
                rec.web_title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                rec.web_description = re.sub(
                    r"<p>\s*<strong>.*?</strong>\s*</p>", "", desc, count=1, flags=re.S)
            else:
                rec.web_title = prod.name if prod else False
                rec.web_description = desc

    def _compute_product_info(self):
        for rec in self:
            prod = rec.product_id
            rec.materials = (prod.x_studio_materialidad
                             if prod and "x_studio_materialidad" in prod._fields else False) or False
            rec.care_tips = (prod.x_studio_tips_cuidado
                             if prod and "x_studio_tips_cuidado" in prod._fields else False) or False

    @api.depends("price", "retail_price")
    def _compute_discount(self):
        for rec in self:
            if rec.retail_price and rec.price and rec.retail_price > rec.price:
                rec.discount_pct = int(round(100 * (1 - rec.price / rec.retail_price)))
            else:
                rec.discount_pct = 0

    # ------------------------------------------------------------------
    # Imágenes (misma convención que la subasta: la última URL es la prenda sola)
    # ------------------------------------------------------------------
    def _image_url_fields(self):
        return ["image_url_%d" % i for i in range(1, 11)]

    def _get_image_urls(self):
        self.ensure_one()
        urls = [self[n].strip() for n in self._image_url_fields() if self[n] and self[n].strip()]
        if len(urls) > 1:
            urls = [urls[-1]] + urls[:-1]
        if not urls and self.product_id:
            urls = ["/web/image/product.template/%s/image_1024" % self.product_id.id]
        return urls

    def _get_primary_image_url(self):
        self.ensure_one()
        urls = self._get_image_urls()
        return urls[0] if urls else ""

    # ------------------------------------------------------------------
    # Exclusividad de canal: subasta XOR venta directa
    # ------------------------------------------------------------------
    @api.constrains("product_id", "state", "active")
    def _check_exclusive_channel(self):
        Auction = self.env["liquidation.auction"].sudo()
        for rec in self.filtered(lambda r: r.active and r.state in SHOP_ACTIVE_STATES):
            twin = self.sudo().search([
                ("id", "!=", rec.id), ("product_id", "=", rec.product_id.id),
                ("state", "in", SHOP_ACTIVE_STATES),
            ], limit=1)
            if twin:
                raise ValidationError(_(
                    "La prenda %(code)s ya tiene otra venta directa activa (%(other)s)."
                ) % {"code": rec.product_id.display_name, "other": twin.name})
            auction = Auction.search([
                ("product_id", "=", rec.product_id.id), ("state", "in", AUCTION_ACTIVE_STATES),
            ], limit=1)
            if auction:
                raise ValidationError(_(
                    "La prenda %(code)s está en la subasta «%(auction)s» (%(state)s). "
                    "Una prenda no puede estar en subasta y en venta directa a la vez: "
                    "cancela la subasta o espera a que quede desierta."
                ) % {
                    "code": rec.product_id.display_name,
                    "auction": auction.name,
                    "state": dict(auction._fields["state"].selection).get(auction.state),
                })

    # ------------------------------------------------------------------
    # Acciones de backend
    # ------------------------------------------------------------------
    def action_publish(self):
        for rec in self:
            if rec.state not in ("draft", "withdrawn"):
                raise UserError(_("Solo se publican prendas en borrador o retiradas (%s).") % rec.name)
            if not rec.price or rec.price <= 0:
                raise UserError(_("Define el precio de venta de %s antes de publicarla.") % rec.name)
            if "rent_ok" in rec.product_id._fields and rec.product_id.rent_ok:
                raise UserError(_(
                    "%s sigue marcada como arrendable («Se puede alquilar»). Desmárcala en la "
                    "ficha del producto antes de publicarla en venta: una prenda vendida no "
                    "puede seguir en el catálogo de arriendo."
                ) % rec.product_id.display_name)
        self.write({"state": "published", "published_date": fields.Datetime.now()})

    def action_withdraw(self):
        for rec in self:
            if rec.state == "reserved":
                raise UserError(_(
                    "%s está reservada con el pedido %s. Cancela ese pedido primero."
                ) % (rec.name, rec.sale_order_id.name))
            if rec.state == "sold":
                raise UserError(_("%s ya está vendida.") % rec.name)
        self.write({"state": "withdrawn"})

    def action_back_to_draft(self):
        for rec in self:
            if rec.state not in ("published", "withdrawn"):
                raise UserError(_("Solo vuelven a borrador prendas publicadas o retiradas."))
        self.write({"state": "draft", "sale_order_id": False, "buyer_id": False,
                    "reserved_until": False})

    def action_move_to_auction(self):
        """Saca la prenda de la venta directa y crea una subasta en borrador con sus datos."""
        self.ensure_one()
        if self.state in ("reserved", "sold"):
            raise UserError(_("No se puede pasar a subasta una prenda reservada o vendida."))
        self.write({"state": "withdrawn"})
        vals = {
            "product_id": self.product_id.id,
            "reserve_price": self.price or 0.0,
            "retail_price": self.retail_price,
            "description": self.description,
            "reason": self.reason,
        }
        vals.update({f: self[f] for f in self._image_url_fields()})
        auction = self.env["liquidation.auction"].create(vals)
        self.message_post(body=_("Retirada de la venta directa y enviada a la subasta %s.")
                          % auction.name)
        return {
            "type": "ir.actions.act_window", "res_model": "liquidation.auction",
            "res_id": auction.id, "view_mode": "form", "target": "current",
        }

    def action_open_web(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url", "url": "/prendas/%s" % self.id, "target": "new"}

    def action_view_order(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "sale.order",
            "res_id": self.sale_order_id.id, "view_mode": "form", "target": "current",
        }

    @api.model
    def action_create_from_products(self, products):
        """Acción masiva desde Productos: crea ventas en borrador (sin precio)."""
        created = self.browse()
        for prod in products:
            if not self.search_count([("product_id", "=", prod.id),
                                      ("state", "in", SHOP_ACTIVE_STATES)]):
                created |= self.create({"product_id": prod.id})
        return {
            "type": "ir.actions.act_window", "name": _("Ventas directas creadas"),
            "res_model": "liquidation.shop.item", "view_mode": "list,form",
            "domain": [("id", "in", created.ids)],
        }

    # ------------------------------------------------------------------
    # Venta: compañía, impuestos y neto (las prendas se publican con IVA incluido)
    # ------------------------------------------------------------------
    def _sale_company(self):
        self.ensure_one()
        variant = self.product_id.product_variant_id
        return self.product_id.company_id or variant.taxes_id[:1].company_id or self.env.company

    @api.model
    def _taxes_for(self, variant, company):
        taxes = variant.taxes_id.filtered(lambda t: not t.company_id or t.company_id == company)
        if not taxes and company.account_sale_tax_id:
            taxes = company.account_sale_tax_id
        return taxes

    @api.model
    def _net_from_gross(self, gross, taxes, currency):
        percent = sum(t.amount for t in taxes if t.amount_type == "percent")
        net = gross / (1.0 + percent / 100.0) if percent else gross
        return currency.round(net) if currency else round(net, 2)

    def _sale_warehouse(self, company):
        variant = self.product_id.product_variant_id
        route = variant.route_ids.filtered(
            lambda r: r.supplied_wh_id and (not r.company_id or r.company_id == company))[:1]
        if route:
            return route.supplied_wh_id
        return self.env["stock.warehouse"].sudo().search([("company_id", "=", company.id)], limit=1)

    # ------------------------------------------------------------------
    # OulaBag: oferta del checkout (máximo 1 por compra)
    # ------------------------------------------------------------------
    @api.model
    def _oulabag_variant(self):
        param = self.env["ir.config_parameter"].sudo().get_param(PARAM_PREFIX + "oulabag_product_id")
        variant = self.env["product.product"].sudo().browse(int(param)).exists() if param and str(param).isdigit() else None
        if not variant:
            variant = self.env.ref("oulalab_auction.product_oulabag", raise_if_not_found=False)
            variant = variant.sudo().product_variant_id if variant else self.env["product.product"]
        return variant

    @api.model
    def _oulabag_offer(self, garments_total, company=None):
        """Datos de la oferta del OulaBag para un total de prendas (IVA incl.)."""
        variant = self._oulabag_variant()
        company = company or self.env.company
        price = shop_param(self.env, "oulabag_price")
        min_cart = shop_param(self.env, "oulabag_min_cart")
        available = bool(variant) and variant.active and variant.sale_ok
        if available and variant.is_storable:
            available = variant.with_company(company).qty_available >= 1
        return {
            "variant": variant,
            "available": available,
            "price": price,
            "reference": shop_param(self.env, "oulabag_reference_price"),
            "min_cart": min_cart,
            "eligible": available and garments_total >= min_cart,
            "missing": max(0, min_cart - garments_total),
            "progress": min(100, int(100 * garments_total / min_cart)) if min_cart else 100,
        }

    # ------------------------------------------------------------------
    # Checkout: crea el pedido y reserva las prendas
    # ------------------------------------------------------------------
    def _lock_for_checkout(self):
        """Bloquea las filas para que dos compradoras no reserven la misma prenda."""
        if not self.ids:
            return
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(
                    "SELECT id FROM liquidation_shop_item WHERE id IN %s FOR UPDATE NOWAIT",
                    (tuple(self.ids),),
                )
        except Exception:
            raise UserError(_("Otra persona está comprando una de estas prendas en este "
                              "momento. Intenta de nuevo en unos minutos."))
        self.invalidate_recordset(["state", "sale_order_id"])

    @api.model
    def _shop_create_order(self, items, partner, shipping_partner, with_bag=False,
                           delivery_mode="pickup"):
        items = items.sudo()
        if not items:
            raise UserError(_("Tu carrito está vacío."))
        items._lock_for_checkout()
        gone = items.filtered(lambda i: i.state != "published" or not i.active)
        if gone:
            raise UserError(_("Ya no están disponibles: %s. Quítalas del carrito para continuar.")
                            % ", ".join(gone.mapped(lambda i: i.web_title or i.name)))

        company = items[0]._sale_company()
        if any(i._sale_company() != company for i in items):
            raise UserError(_("Estas prendas se venden desde compañías distintas; "
                              "cómpralas en pedidos separados."))
        warehouse = items[0]._sale_warehouse(company)
        currency = company.currency_id

        lines = []
        for item in items:
            variant = item.product_id.product_variant_id
            taxes = self._taxes_for(variant, company)
            lines.append((0, 0, {
                "product_id": variant.id,
                "product_uom_qty": 1,
                "price_unit": self._net_from_gross(item.price, taxes, currency),
                "tax_ids": [(6, 0, taxes.ids)],
                "name": _("%(title)s [%(code)s] — prenda usada OulaLab") % {
                    "title": item.web_title or item.product_id.name,
                    "code": item.product_id.default_code or "-",
                },
            }))

        garments_total = sum(items.mapped("price"))
        if with_bag:
            offer = self._oulabag_offer(garments_total, company)
            if not offer["eligible"]:
                raise UserError(_("El OulaBag está disponible para compras desde %s.")
                                % fmt_clp(offer["min_cart"]))
            bag = offer["variant"]
            taxes = self._taxes_for(bag, company)
            lines.append((0, 0, {
                "product_id": bag.id,
                "product_uom_qty": 1,  # máximo 1 por compra
                "price_unit": self._net_from_gross(offer["price"], taxes, currency),
                "tax_ids": [(6, 0, taxes.ids)],
                "name": _("OulaBag — bolso portatrajes OulaLab (1 por compra)"),
            }))

        fee = shop_param(self.env, "shipping_fee")
        shipping = self.env.ref("oulalab_auction.product_shop_shipping", raise_if_not_found=False)
        if delivery_mode == "delivery" and fee > 0 and shipping:
            ship_variant = shipping.sudo().product_variant_id
            taxes = self._taxes_for(ship_variant, company)
            lines.append((0, 0, {
                "product_id": ship_variant.id, "product_uom_qty": 1,
                "price_unit": self._net_from_gross(fee, taxes, currency),
                "tax_ids": [(6, 0, taxes.ids)],
                "name": _("Despacho a domicilio"),
            }))

        minutes = shop_param(self.env, "reservation_minutes")
        SaleOrder = self.env["sale.order"].sudo().with_company(company)
        vals = {
            "company_id": company.id,
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": (shipping_partner or partner).id,
            "origin": _("Venta directa OulaLab"),
            "liquidation_channel": "shop",
            "warehouse_id": warehouse.id if warehouse else False,
            "require_payment": True,
            "prepayment_percent": 1.0,
            "require_signature": False,
            "note": self._shop_order_note(delivery_mode),
            "validity_date": (fields.Datetime.now() + timedelta(days=2)).date(),
            "order_line": lines,
        }
        if "sale_order_template_id" in SaleOrder._fields:
            vals["sale_order_template_id"] = False
        if "plan_id" in SaleOrder._fields:
            vals["plan_id"] = False
        seq = self.env["ir.sequence"].sudo().with_company(company).next_by_code("liquidation.shop.order")
        if seq:
            vals["name"] = seq
        order = SaleOrder.create(vals)
        order.write({"state": "sent"})
        order._portal_ensure_token()

        items.write({
            "state": "reserved",
            "sale_order_id": order.id,
            "buyer_id": partner.id,
            "reserved_until": fields.Datetime.now() + timedelta(minutes=minutes),
        })
        for item in items:
            item.message_post(body=_("Reservada para %(partner)s con el pedido %(order)s "
                                     "por %(price)s.") % {
                "partner": partner.display_name, "order": order.name,
                "price": fmt_clp(item.price)})
        return order

    def _shop_order_note(self, delivery_mode):
        base = self.get_base_url()
        delivery = (_("Despacho a domicilio en comunas habilitadas.") if delivery_mode == "delivery"
                    else _("Retiro en showroom: Av. La Dehesa 222 of. 817, Lo Barnechea."))
        return Markup(
            "<p><strong>Venta directa OulaLab</strong>. %(delivery)s</p>"
            "<p>Prendas usadas, provenientes del servicio de arriendo de OulaLab, vendidas en "
            "el estado informado en su ficha (art. 14, Ley 19.496). Precios con IVA incluido. "
            "Tienes derecho a retracto dentro de 10 días desde que recibes la compra, "
            "devolviéndola en el mismo estado en que la recibiste. Rigen los Términos y "
            "condiciones de uso de OulaLab (<a href='%(base)s/terms'>%(base)s/terms</a>). "
            "Consultas y reclamos: contactotyc@oulalab.com.</p>"
        ) % {"delivery": delivery, "base": base}

    # ------------------------------------------------------------------
    # Ciclo del pago
    # ------------------------------------------------------------------
    def _mark_sold(self, order):
        for item in self:
            item.write({"state": "sold", "sold_date": fields.Datetime.now(),
                        "sale_order_id": order.id, "buyer_id": order.partner_id.id,
                        "reserved_until": False})
            item.message_post(body=_("Vendida: pedido %s confirmado.") % order.name)

    def _release(self, reason):
        for item in self:
            item.write({"state": "published", "sale_order_id": False, "buyer_id": False,
                        "reserved_until": False})
            item.message_post(body=reason)

    @api.model
    def _cron_release_reservations(self):
        """Libera las prendas cuya reserva venció sin pago."""
        now = fields.Datetime.now()
        grace = timedelta(minutes=shop_param(self.env, "pending_grace_minutes"))
        expired = self.sudo().search([("state", "=", "reserved"), ("reserved_until", "<", now)])
        for order in expired.mapped("sale_order_id"):
            try:
                with self.env.cr.savepoint():
                    txs = order.transaction_ids
                    paid = order.state == "sale" or any(t.state in ("done", "authorized") for t in txs)
                    if paid:
                        if order.state in ("draft", "sent"):
                            order.action_confirm()
                        else:
                            order._sync_shop_after_confirm()
                        continue
                    pending = any(t.state == "pending" and t.provider_id.code != "custom" for t in txs)
                    items = expired.filtered(lambda i: i.sale_order_id == order)
                    if pending and now < max(items.mapped("reserved_until")) + grace:
                        continue
                    order._action_cancel()  # libera las prendas (ver sale.order._action_cancel)
            except Exception:
                _logger.exception("Venta directa: error liberando el pedido %s", order.id)
        orphans = expired.filtered(lambda i: not i.sale_order_id and i.state == "reserved")
        orphans._release(_("Reserva sin pedido: vuelve a publicarse."))
