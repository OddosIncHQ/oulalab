import re

from odoo import fields, http
from odoo.http import request

from ..models.res_partner import validate_rut

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_KEY = "auction_guest_partner_id"


class AuctionPortal(http.Controller):

    # ------------------------------------------------------------------
    # Identidad del postor: cuenta Odoo o sesión verificada por correo
    # ------------------------------------------------------------------
    def _current_partner(self):
        user = request.env.user
        if not user._is_public():
            return user.partner_id
        pid = request.session.get(SESSION_KEY)
        if pid:
            return request.env["res.partner"].sudo().browse(pid).exists()
        return request.env["res.partner"]

    def _validate_delivery(self, Partner, mode, commune, street):
        """Devuelve (vals, error). Reutilizado por el registro sin cuenta y por la entrega."""
        valid_communes = dict(Partner._fields["auction_commune"].selection)
        if mode == "delivery":
            if commune not in valid_communes:
                return None, "Comuna fuera de cobertura de despacho."
            if not street:
                return None, "Indica la dirección de despacho."
            ok, reason = Partner._auction_verify_address(street, valid_communes[commune])
            if not ok:
                return None, reason
            return {
                "auction_delivery_mode": "delivery",
                "auction_commune": commune,
                "street": street,
            }, None
        if mode == "pickup":
            return {"auction_delivery_mode": "pickup", "auction_commune": False}, None
        return None, "Modalidad inválida."

    # ------------------------------------------------------------------
    # Listado público
    # ------------------------------------------------------------------
    @http.route("/auctions", type="http", auth="public", website=True)
    def auctions_list(self, **kw):
        now = fields.Datetime.now()
        auctions = request.env["liquidation.auction"].sudo().search(
            [("state", "in", ["published", "live"]), ("end_date", ">", now)]
        )
        return request.render(
            "oulalab_auction.auction_list_template",
            {"auctions": auctions, "now": now},
        )

    # ------------------------------------------------------------------
    # Detalle público
    # ------------------------------------------------------------------
    @http.route("/auctions/<int:auction_id>", type="http", auth="public", website=True)
    def auction_detail(self, auction_id, **kw):
        auction = request.env["liquidation.auction"].sudo().browse(auction_id)
        if not auction.exists() or auction.state not in ("published", "live"):
            return request.not_found()

        partner = self._current_partner()
        is_member = bool(partner and partner.is_oulalab_member)
        min_next = auction._min_next_bid_for(partner)
        communes = request.env["res.partner"]._fields["auction_commune"].selection

        return request.render(
            "oulalab_auction.auction_detail_template",
            {
                "auction": auction,
                "partner": partner,
                "is_member": is_member,
                "is_public": not partner,
                "delivery_ready": bool(partner and partner._auction_delivery_ready())
                and not kw.get("edit_delivery"),
                "communes": communes,
                "showroom": "Av. La Dehesa 222 of. 817, Lo Barnechea",
                "min_next": min_next,
                "server_now": fields.Datetime.now(),
            },
        )

    @http.route("/auctions/delivery", type="jsonrpc", auth="public")
    def save_delivery(self, mode, rut=None, commune=None, street=None, phone=None, **kw):
        """Guarda RUT + modalidad de entrega del postor antes de permitirle pujar."""
        partner = self._current_partner()
        if not partner:
            return {"ok": False, "error": "Verifica tu correo antes de continuar."}
        Partner = request.env["res.partner"].sudo()
        clean_rut = validate_rut(rut)
        if not clean_rut:
            return {"ok": False, "error": "El RUT no es válido. Revísalo (ej: 12.345.678-5)."}
        vals, error = self._validate_delivery(Partner, mode, commune, street)
        if error:
            return {"ok": False, "error": error}
        vals["vat"] = clean_rut
        if phone:
            vals["phone"] = phone
        partner.sudo().write(vals)
        return {"ok": True}

    # ------------------------------------------------------------------
    # Registro sin cuenta: datos básicos + código por correo
    # ------------------------------------------------------------------
    @http.route("/auctions/guest/start", type="jsonrpc", auth="public")
    def guest_start(self, name=None, rut=None, email=None, phone=None,
                    mode=None, commune=None, street=None, **kw):
        """Valida los datos y envía un código de 6 dígitos al correo indicado."""
        Partner = request.env["res.partner"].sudo()
        Otp = request.env["auction.guest.otp"]

        name = (name or "").strip()
        email = (email or "").strip().lower()
        phone = (phone or "").strip()
        if len(name) < 3:
            return {"ok": False, "error": "Indica tu nombre completo."}
        clean_rut = validate_rut(rut)
        if not clean_rut:
            return {"ok": False, "error": "El RUT no es válido. Revísalo (ej: 12.345.678-5)."}
        if not EMAIL_RE.match(email):
            return {"ok": False, "error": "El correo no es válido."}
        if len(re.sub(r"\D", "", phone)) < 8:
            return {"ok": False, "error": "Indica un teléfono de contacto válido."}
        vals, error = self._validate_delivery(Partner, mode, commune, street)
        if error:
            return {"ok": False, "error": error}

        # Si ya existe un contacto con ese correo, su RUT debe coincidir.
        # Así nadie puede usar el correo de otra persona con un RUT distinto.
        existing = Partner.search([("email", "=ilike", email)], limit=5)
        existing = existing.filtered(lambda p: (p.email or "").lower() == email)[:1]
        if existing and existing.vat and validate_rut(existing.vat) != clean_rut:
            return {"ok": False, "error": (
                "Los datos no coinciden con nuestro registro. "
                "Escríbenos a hola@oulalab.com para ayudarte."
            )}

        if Otp.recently_sent(email):
            return {"ok": False, "error": "Ya te enviamos un código. Espera un minuto para pedir otro."}

        payload = dict(vals, name=name, vat=clean_rut, phone=phone, email=email,
                       partner_id=existing.id or False)
        code = Otp.issue(email, payload)
        self._send_code(email, name, code)
        return {"ok": True, "sent_to": email}

    @http.route("/auctions/guest/verify", type="jsonrpc", auth="public")
    def guest_verify(self, email=None, code=None, **kw):
        email = (email or "").strip().lower()
        code = (code or "").strip()
        payload = request.env["auction.guest.otp"].consume(email, code)
        if payload is None:
            return {"ok": False, "error": "Código incorrecto o vencido. Pide uno nuevo."}

        Partner = request.env["res.partner"].sudo()
        delivery = {k: payload[k] for k in ("auction_delivery_mode", "auction_commune", "street") if k in payload}
        if payload.get("partner_id"):
            partner = Partner.browse(payload["partner_id"]).exists()
            if not partner:
                return {"ok": False, "error": "No pudimos completar el registro. Intenta de nuevo."}
            partner.write(dict(delivery, vat=payload["vat"], phone=payload["phone"]))
        else:
            partner = Partner.create(dict(
                delivery,
                name=payload["name"],
                email=payload["email"],
                vat=payload["vat"],
                phone=payload["phone"],
            ))
        request.session[SESSION_KEY] = partner.id
        return {"ok": True}

    def _send_code(self, email, name, code):
        company = request.env.company
        sender = company.email or "hola@oulalab.com"
        body = (
            "<p>Hola %s,</p>"
            "<p>Tu código para entrar a las subastas de OulaLab es:</p>"
            "<p style='font-size:24px;font-weight:bold;letter-spacing:4px'>%s</p>"
            "<p>Vence en 10 minutos. Si no lo pediste, ignora este correo.</p>"
        ) % (name, code)
        request.env["mail.mail"].sudo().create({
            "subject": "Tu código de verificación – OulaLab",
            "body_html": body,
            "email_to": email,
            "email_from": sender,
        }).send()

    # ------------------------------------------------------------------
    # Estado en vivo (polling ligero para reflejar pujas ajenas / extensiones)
    # ------------------------------------------------------------------
    @http.route("/auctions/<int:auction_id>/state", type="jsonrpc", auth="public")
    def auction_state(self, auction_id, **kw):
        auction = request.env["liquidation.auction"].sudo().browse(auction_id)
        if not auction.exists():
            return {"ok": False}
        partner = self._current_partner()
        return {
            "ok": True,
            "state": auction.state,
            "highest": auction.highest_amount,
            "bid_count": auction.bid_count,
            "min_next": auction._min_next_bid_for(partner),
            "end_date": fields.Datetime.to_string(auction.end_date),
            "server_now": fields.Datetime.to_string(fields.Datetime.now()),
        }

    # ------------------------------------------------------------------
    # Registro de puja (requiere sesión iniciada)
    # ------------------------------------------------------------------
    @http.route("/auctions/<int:auction_id>/bid", type="jsonrpc", auth="public")
    def submit_bid(self, auction_id, amount, **kw):
        auction = request.env["liquidation.auction"].sudo().browse(auction_id)
        if not auction.exists():
            return {"ok": False, "error": "Subasta inexistente."}

        partner = self._current_partner()
        if not partner:
            return {"ok": False, "error": "Verifica tu correo antes de pujar."}
        try:
            # place_bid corre con sudo: la validación está centralizada ahí,
            # el portal user no escribe auction.bid directamente.
            auction.place_bid(partner, amount)
        except Exception as e:  # ValidationError u otros
            return {"ok": False, "error": str(getattr(e, "args", [e])[0])}

        return {
            "ok": True,
            "highest": auction.highest_amount,
            "bid_count": auction.bid_count,
            "min_next": auction._min_next_bid_for(partner),
            "end_date": fields.Datetime.to_string(auction.end_date),
        }
