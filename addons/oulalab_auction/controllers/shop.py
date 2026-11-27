import hmac
import re
import secrets
import time
from collections import namedtuple

from odoo import SUPERUSER_ID, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

from ..models.res_partner import validate_rut
from ..models.shop_item import fmt_clp, garment_type_of, shop_param
from .auction_portal import EMAIL_RE, AuctionPortal

CART_KEY = "oulalab_shop_cart"
REMOVED_KEY = "oulalab_shop_removed"
LAST_ORDER_KEY = "oulalab_shop_last_order"
LAST_ORDER_TS_KEY = "oulalab_shop_last_order_ts"
SHOWROOM = "Av. La Dehesa 222 of. 817, Lo Barnechea"
Tipo = namedtuple("Tipo", "id name")  # la plantilla lee tp.id y tp.name

# --- Verificación por código (OTP) del checkout -----------------------------
OTP_KEY = "oulalab_shop_otp"              # código pendiente en la sesión
VERIFIED_KEY = "oulalab_shop_verified"    # ids de contactos ya verificados
OTP_TTL = 10 * 60                         # 10 minutos de vigencia
OTP_MAX_ATTEMPTS = 5                      # intentos por código
AUTO_REDIRECT_TTL = 120                   # ventana anti-rebote WebView (segundos)


class OulaLabShop(http.Controller):

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _portal(self):
        return AuctionPortal()

    def _cart_items(self):
        """Prendas del carrito que siguen a la venta. Devuelve (items, quitadas)."""
        ids = [i for i in request.session.get(CART_KEY, []) if isinstance(i, int)]
        Item = request.env["liquidation.shop.item"].sudo()
        items = Item.browse(ids).exists()
        available = items.filtered(lambda i: i.state == "published" and i.active)
        removed = items - available
        if removed or len(available) != len(ids):
            request.session[CART_KEY] = available.ids
        return available, removed

    def _stash_removed(self, removed):
        if removed:
            prev = [i for i in request.session.get(REMOVED_KEY, []) if isinstance(i, int)]
            merged = list(dict.fromkeys(prev + removed.ids))
            request.session[REMOVED_KEY] = merged

    def _pop_stashed_removed(self):
        ids = [i for i in request.session.pop(REMOVED_KEY, []) if isinstance(i, int)]
        if not ids:
            return request.env["liquidation.shop.item"].sudo()
        return request.env["liquidation.shop.item"].sudo().browse(ids).exists()

    def _pending_order(self):
        """Devuelve la última orden creada en esta sesión si sigue pendiente de pago."""
        last_id = request.session.get(LAST_ORDER_KEY)
        if not last_id or not isinstance(last_id, int):
            return None
        order = request.env["sale.order"].sudo().browse(last_id).exists()
        if not order or order.state not in ("draft", "sent"):
            return None
        paid = any(t.state in ("done", "authorized") for t in order.transaction_ids)
        if paid:
            return None
        return order

    def _order_portal_relative_url(self, order):
        token = order._portal_ensure_token()
        return "/my/orders/%s?access_token=%s" % (order.id, token)

    def _recent_pending_order_url(self):
        """URL de pago si la orden se creó hace pocos segundos (evita rebote en Instagram WebView)."""
        ts = request.session.get(LAST_ORDER_TS_KEY) or 0
        if (time.time() - ts) > AUTO_REDIRECT_TTL:
            return None
        order = self._pending_order()
        return self._order_portal_relative_url(order) if order else None

    def _cart_count(self):
        return len(request.session.get(CART_KEY, []))

    def _common(self, **extra):
        values = {"fmt_clp": fmt_clp, "cart_count": self._cart_count(), "section": "shop"}
        values.update(extra)
        return values

    # ------------------------------------------------------------------
    # Catálogo
    # ------------------------------------------------------------------
    @http.route("/prendas", type="http", auth="public", website=True, sitemap=True)
    def shop_list(self, marca=None, tipo=None, talla=None, orden=None, **kw):
        Item = request.env["liquidation.shop.item"].sudo()
        base = Item.search([("state", "=", "published")])
        marcas = sorted({i.brand for i in base if i.brand})
        tipos = [Tipo(t, t) for t in sorted({garment_type_of(i.product_id) for i in base} - {False})]
        tallas = sorted({i.size for i in base if i.size})

        items = base
        if marca:
            items = items.filtered(lambda i: i.brand == marca)
        if tipo:
            items = items.filtered(lambda i: garment_type_of(i.product_id) == tipo)
        if talla:
            items = items.filtered(lambda i: i.size == talla)
        if orden == "precio_asc":
            items = items.sorted("price")
        elif orden == "precio_desc":
            items = items.sorted("price", reverse=True)
        elif orden == "descuento":
            items = items.sorted("discount_pct", reverse=True)

        offer = Item._oulabag_offer(0)
        return request.render("oulalab_auction.shop_list_template", self._common(
            items=items, marcas=marcas, tipos=tipos, tallas=tallas,
            marca_sel=marca or "", tipo_sel=tipo or "", talla_sel=talla or "",
            orden_sel=orden or "", cart_ids=request.session.get(CART_KEY, []),
            offer=offer,
        ))

    @http.route("/prendas/<int:item_id>", type="http", auth="public", website=True)
    def shop_detail(self, item_id, **kw):
        item = request.env["liquidation.shop.item"].sudo().browse(item_id)
        if not item.exists() or item.state not in ("published", "reserved", "sold"):
            return request.not_found()
        own_type = garment_type_of(item.product_id)
        related = request.env["liquidation.shop.item"].sudo().search([
            ("state", "=", "published"), ("id", "!=", item.id)])
        related = related.filtered(
            lambda r: (item.brand and r.brand == item.brand)
            or (own_type and garment_type_of(r.product_id) == own_type))[:4]
        return request.render("oulalab_auction.shop_detail_template", self._common(
            item=item, in_cart=item.id in request.session.get(CART_KEY, []),
            related=related, showroom=SHOWROOM,
            offer=request.env["liquidation.shop.item"].sudo()._oulabag_offer(0),
        ))

    # ------------------------------------------------------------------
    # Carrito
    # ------------------------------------------------------------------
    @http.route("/prendas/cart/add", type="jsonrpc", auth="public")
    def cart_add(self, item_id=None, **kw):
        item = request.env["liquidation.shop.item"].sudo().browse(int(item_id or 0))
        if not item.exists() or item.state != "published":
            return {"ok": False, "error": "Esta prenda ya no está disponible."}
        cart = list(request.session.get(CART_KEY, []))
        if item.id not in cart:
            cart.append(item.id)  # cada prenda es una sola unidad: nunca cantidad 2
        request.session[CART_KEY] = cart
        return {"ok": True, "count": len(cart)}

    @http.route("/prendas/cart/remove", type="jsonrpc", auth="public")
    def cart_remove(self, item_id=None, **kw):
        cart = [i for i in request.session.get(CART_KEY, []) if i != int(item_id or 0)]
        request.session[CART_KEY] = cart
        return {"ok": True, "count": len(cart)}

    @http.route("/prendas/carrito", type="http", auth="public", website=True, sitemap=False)
    def shop_cart(self, **kw):
        items, removed = self._cart_items()
        removed |= self._pop_stashed_removed()
        if not items and not removed and not kw.get("stay"):
            recent_url = self._recent_pending_order_url()
            if recent_url:
                return request.redirect(recent_url)
        pending_order = self._pending_order()
        pending_url = self._order_portal_relative_url(pending_order) if pending_order else None
        total = sum(items.mapped("price"))
        offer = request.env["liquidation.shop.item"].sudo()._oulabag_offer(total)
        return request.render("oulalab_auction.shop_cart_template", self._common(
            items=items, removed=removed, total=total, offer=offer,
            pending_order=pending_order, pending_url=pending_url,
        ))

    # ------------------------------------------------------------------
    # Verificación del comprador (OTP)
    # ------------------------------------------------------------------
    @staticmethod
    def _mask_email(email):
        """v***a@gmail.com — para nombrar el correo sin revelarlo entero."""
        email = (email or "").strip()
        if "@" not in email:
            return ""
        user, domain = email.split("@", 1)
        if len(user) <= 2:
            visible = user[:1]
        else:
            visible = user[0] + "***" + user[-1]
        return "%s@%s" % (visible, domain)

    def _find_existing_partner(self, clean_rut, email):
        """Contacto ya registrado que coincide por RUT o por correo.

        Se busca también por correo para no crear duplicados y para que el
        correo ajeno quede igual de protegido que el RUT ajeno.
        """
        Partner = request.env["res.partner"].sudo()
        found = self._portal()._find_partner_by_rut(clean_rut)
        if found:
            return found[:1]
        if email:
            return Partner.search([
                ("email", "=ilike", email),
                ("type", "!=", "delivery"),
            ], limit=1)
        return Partner.browse()

    def _is_verified(self, partner):
        """True si esta sesión ya demostró ser dueña de ese contacto."""
        if not partner:
            return False
        current = self._portal()._current_partner()
        if current and current.id == partner.id:
            return True
        return partner.id in (request.session.get(VERIFIED_KEY) or [])

    def _mark_verified(self, partner):
        ids = list(request.session.get(VERIFIED_KEY) or [])
        if partner.id not in ids:
            ids.append(partner.id)
        request.session[VERIFIED_KEY] = ids

    def _otp_send(self, partner):
        """Envía un código al correo REGISTRADO del contacto, nunca al tecleado."""
        code = "%06d" % secrets.randbelow(1000000)
        request.session[OTP_KEY] = {
            "partner_id": partner.id,
            "code": code,
            "expires": time.time() + OTP_TTL,
            "attempts": 0,
        }
        env = request.env(user=SUPERUSER_ID)
        company = env.company
        body = (
            "<p>Hola,</p>"
            "<p>Tu código para confirmar la compra en OulaLab es:</p>"
            "<p style='font-size:28px;letter-spacing:4px;'><strong>%s</strong></p>"
            "<p>Vence en 10 minutos. Si no fuiste tú quien lo pidió, "
            "ignora este correo: nadie puede comprar a tu nombre sin él.</p>"
        ) % code
        mail = env["mail.mail"].create({
            "subject": "Tu código de compra OulaLab",
            "body_html": body,
            "email_to": partner.email,
            "email_from": company.email or company.partner_id.email,
            "author_id": company.partner_id.id,
        })
        mail.send()

    def _otp_check(self, partner, code):
        """(ok, mensaje_de_error). Consume el código al acertar."""
        data = request.session.get(OTP_KEY) or {}
        if not data or data.get("partner_id") != partner.id:
            return False, "Necesitamos verificar tu correo. Te enviamos un código nuevo."
        if time.time() > data.get("expires", 0):
            request.session.pop(OTP_KEY, None)
            return False, "El código venció. Vuelve a enviar el formulario para recibir otro."
        if data.get("attempts", 0) >= OTP_MAX_ATTEMPTS:
            request.session.pop(OTP_KEY, None)
            return False, ("Demasiados intentos. Vuelve a enviar el formulario para "
                           "recibir un código nuevo.")
        data["attempts"] = data.get("attempts", 0) + 1
        request.session[OTP_KEY] = data
        if not hmac.compare_digest(str(data.get("code") or ""), str(code or "").strip()):
            return False, "El código no coincide. Revísalo e inténtalo de nuevo."
        request.session.pop(OTP_KEY, None)
        return True, None

    # ------------------------------------------------------------------
    # Checkout
    # ------------------------------------------------------------------
    def _checkout_values(self, items, form=None, error=None, removed=None,
                         otp_required=False, otp_email=""):
        partner = self._portal()._current_partner()
        total = sum(items.mapped("price"))
        Item = request.env["liquidation.shop.item"].sudo()
        offer = Item._oulabag_offer(total)
        form = form or {}
        if partner and not form:
            form = {
                "name": partner.name or "", "email": partner.email or "",
                "phone": partner.phone or "", "rut": partner.vat or "",
                "mode": partner.auction_delivery_mode or "pickup",
                "commune": partner.auction_commune or "", "street": partner.street or "",
            }
        quote_partner = partner
        if not quote_partner and (form.get("rut") or form.get("email")):
            clean_rut = validate_rut(form.get("rut") or "")
            quote_partner = self._find_existing_partner(
                clean_rut, (form.get("email") or "").strip().lower()
            )
        ship_quote = Item._compute_shipping_quote(
            items_count=len(items),
            garments_total=total,
            partner=quote_partner,
            commune=form.get("commune"),
        )
        return self._common(
            items=items, removed=removed or request.env["liquidation.shop.item"],
            total=total, offer=offer, form=form, error=error, partner=partner,
            communes=request.env["res.partner"]._fields["auction_commune"].selection,
            showroom=SHOWROOM,
            shipping_fee=ship_quote["final_fee"],
            shipping_quote=ship_quote,
            otp_required=otp_required, otp_email=otp_email,
        )

    @http.route("/prendas/checkout/shipping-quote", type="jsonrpc", auth="public")
    def shop_shipping_quote(self, rut=None, email=None, commune=None, **kw):
        """Devuelve la cotización de despacho en vivo según el carrito y si el RUT/email es suscriptora."""
        items, _ = self._cart_items()
        total = sum(items.mapped("price"))
        partner = self._portal()._current_partner()
        if not partner and (rut or email):
            clean_rut = validate_rut(rut or "")
            partner = self._find_existing_partner(clean_rut, (email or "").strip().lower())
        return request.env["liquidation.shop.item"].sudo()._compute_shipping_quote(
            items_count=len(items),
            garments_total=total,
            partner=partner,
            commune=commune,
        )

    @http.route("/prendas/checkout", type="http", auth="public", website=True,
                methods=["GET"], sitemap=False)
    def shop_checkout(self, **kw):
        items, removed = self._cart_items()
        if not items:
            if removed:
                self._stash_removed(removed)
                return request.redirect("/prendas/carrito")
            recent_url = self._recent_pending_order_url()
            if recent_url:
                return request.redirect(recent_url)
            return request.redirect("/prendas/carrito")
        return request.render("oulalab_auction.shop_checkout_template",
                              self._checkout_values(items, removed=removed))

    @http.route("/prendas/checkout", type="http", auth="public", website=True,
                methods=["POST"], sitemap=False)
    def shop_checkout_submit(self, **post):
        items, removed = self._cart_items()
        if not items:
            if removed:
                self._stash_removed(removed)
                return request.redirect("/prendas/carrito")
            recent_url = self._recent_pending_order_url()
            if recent_url:
                return request.redirect(recent_url)
            return request.redirect("/prendas/carrito")
        form = {k: (post.get(k) or "").strip() for k in
                ("name", "email", "phone", "rut", "mode", "commune", "street", "street2")}
        form["oulabag"] = bool(post.get("oulabag"))

        def fail(msg, otp_required=False, otp_email=""):
            return request.render("oulalab_auction.shop_checkout_template",
                                  self._checkout_values(items, form=form, error=msg,
                                                        removed=removed,
                                                        otp_required=otp_required,
                                                        otp_email=otp_email))

        if removed:
            return fail("Algunas prendas de tu carrito ya no están disponibles y las quitamos. "
                        "Revisa el resumen antes de pagar.")
        if not post.get("accept_terms"):
            return fail("Debes aceptar los términos de compra para continuar.")
        clean_rut = validate_rut(form["rut"])
        if not clean_rut:
            return fail("El RUT no es válido. Revísalo (ej: 12.345.678-5).")
        if len(form["name"]) < 3:
            return fail("Indica tu nombre completo.")
        email = form["email"].lower()
        if not EMAIL_RE.match(email):
            return fail("El correo no es válido.")
        if len(re.sub(r"\D", "", form["phone"])) < 8:
            return fail("Indica un teléfono de contacto válido
