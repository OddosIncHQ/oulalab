import hmac
import re
import secrets
import time

from odoo import SUPERUSER_ID, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

from ..models.res_partner import validate_rut
from collections import namedtuple

from ..models.shop_item import fmt_clp, garment_type_of, shop_param
from .auction_portal import EMAIL_RE, AuctionPortal

CART_KEY = "oulalab_shop_cart"
SHOWROOM = "Av. La Dehesa 222 of. 817, Lo Barnechea"
Tipo = namedtuple("Tipo", "id name")  # la plantilla lee tp.id y tp.name

# --- Verificación por código (OTP) del checkout -----------------------------
OTP_KEY = "oulalab_shop_otp"              # código pendiente en la sesión
VERIFIED_KEY = "oulalab_shop_verified"    # ids de contactos ya verificados
OTP_TTL = 10 * 60                         # 10 minutos de vigencia
OTP_MAX_ATTEMPTS = 5                      # intentos por código


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
        total = sum(items.mapped("price"))
        offer = request.env["liquidation.shop.item"].sudo()._oulabag_offer(total)
        return request.render("oulalab_auction.shop_cart_template", self._common(
            items=items, removed=removed, total=total, offer=offer,
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
        offer = request.env["liquidation.shop.item"].sudo()._oulabag_offer(total)
        form = form or {}
        if partner and not form:
            form = {
                "name": partner.name or "", "email": partner.email or "",
                "phone": partner.phone or "", "rut": partner.vat or "",
                "mode": partner.auction_delivery_mode or "pickup",
                "commune": partner.auction_commune or "", "street": partner.street or "",
            }
        return self._common(
            items=items, removed=removed or request.env["liquidation.shop.item"],
            total=total, offer=offer, form=form, error=error, partner=partner,
            communes=request.env["res.partner"]._fields["auction_commune"].selection,
            showroom=SHOWROOM, shipping_fee=shop_param(request.env, "shipping_fee"),
            otp_required=otp_required, otp_email=otp_email,
        )

    @http.route("/prendas/checkout", type="http", auth="public", website=True,
                methods=["GET"], sitemap=False)
    def shop_checkout(self, **kw):
        items, removed = self._cart_items()
        if not items:
            return request.redirect("/prendas/carrito")
        return request.render("oulalab_auction.shop_checkout_template",
                              self._checkout_values(items, removed=removed))

    @http.route("/prendas/checkout", type="http", auth="public", website=True,
                methods=["POST"], sitemap=False)
    def shop_checkout_submit(self, **post):
        items, removed = self._cart_items()
        if not items:
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
            return fail("Indica un teléfono de contacto válido.")

        Partner = request.env["res.partner"].sudo()
        mode = form["mode"] if form["mode"] in ("pickup", "delivery") else "pickup"
        delivery_vals, error = self._portal()._validate_delivery(
            Partner, mode, form["commune"], form["street"])
        if error:
            return fail(error)

        # --- Puerta de verificación -----------------------------------
        # Un RUT o un correo no son secretos: antes de usar un contacto ya
        # registrado hay que probar que la sesión es su dueña.
        existing = self._portal()._current_partner() or \
            self._find_existing_partner(clean_rut, email)
        if existing and not self._is_verified(existing):
            if not existing.email:
                return fail("Ese RUT ya está registrado y no tiene correo asociado. "
                            "Escríbenos a hola@oulalab.com para completar tu compra.")
            masked = self._mask_email(existing.email)
            code = (post.get("otp") or "").strip()
            if not code:
                self._otp_send(existing)
                return fail(
                    "Ese RUT o correo ya está registrado con nosotros. Te enviamos un "
                    "código de 6 dígitos a %s para confirmar que eres tú." % masked,
                    otp_required=True, otp_email=masked)
            ok, msg = self._otp_check(existing, code)
            if not ok:
                if "código nuevo" in msg or "venció" in msg:
                    self._otp_send(existing)
                return fail(msg, otp_required=True, otp_email=masked)
            self._mark_verified(existing)

        partner, shipping = self._resolve_partner(
            form, clean_rut, email, mode, delivery_vals, existing=existing)
        Item = request.env["liquidation.shop.item"].sudo()
        try:
            order = Item._shop_create_order(items, partner, shipping,
                                            with_bag=form["oulabag"], delivery_mode=mode)
        except (UserError, ValidationError) as e:
            request.env.cr.rollback()
            return fail(str(getattr(e, "args", [e])[0]))

        request.session[CART_KEY] = []
        request.session["oulalab_shop_last_order"] = order.id
        return request.redirect(order.get_portal_url())

    def _resolve_partner(self, form, clean_rut, email, mode, delivery_vals, existing=None):
        """Cliente del pedido y dirección de despacho.

        `existing` llega ya verificado desde shop_checkout_submit: este método
        nunca busca un contacto por su cuenta. Nunca se sobrescriben los datos
        de un contacto existente a partir de un formulario público: solo se
        completan campos vacíos. Una dirección nueva se guarda como contacto de
        entrega hijo.
        """
        Partner = request.env["res.partner"].sudo()
        partner = existing
        if partner:
            partner = partner.sudo()
            fill = {}
            if not partner.vat:
                fill["vat"] = clean_rut
            if not partner.phone:
                fill["phone"] = form["phone"]
            if not partner.email:
                fill["email"] = email
            if not partner.auction_delivery_mode:
                fill.update(delivery_vals)
            if fill:
                partner.write(fill)
        else:
            partner = Partner.create(dict(
                delivery_vals, name=form["name"], email=email,
                vat=clean_rut, phone=form["phone"],
            ))

        shipping = partner
        if mode == "delivery":
            same = (partner.street or "").strip().lower() == form["street"].lower() \
                and partner.auction_commune == form["commune"]
            if not same:
                communes = dict(Partner._fields["auction_commune"].selection)
                shipping = Partner.create({
                    "type": "delivery",
                    "parent_id": partner.id,
                    "name": form["name"],
                    "street": form["street"],
                    "street2": form.get("street2") or False,
                    "city": communes.get(form["commune"]),
                    "phone": form["phone"],
                })
        return partner, shipping
