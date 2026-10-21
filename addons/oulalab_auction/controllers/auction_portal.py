import random
import re
import time

from odoo import fields, http
from odoo.http import request

from ..models.res_partner import validate_rut

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_KEY = "auction_guest_partner_id"
PENDING_KEY = "auction_pending_email"
GUEST_AT_KEY = "auction_guest_at"
GUEST_TTL = 2 * 3600  # 2 horas sin usar el sitio: se pide el RUT otra vez


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
            since = request.session.get(GUEST_AT_KEY) or 0
            if time.time() - since < GUEST_TTL:
                return request.env["res.partner"].sudo().browse(pid).exists()
            # Sesión vencida: se cierra. Solo en este caso; sin sesión no se toca
            # el correo pendiente de verificación (la pantalla hace polling cada pocos segundos).
            self._guest_logout_session()
        return request.env["res.partner"]

    def _guest_logout_session(self):
        for key in (SESSION_KEY, PENDING_KEY, GUEST_AT_KEY):
            request.session.pop(key, None)

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
    @http.route("/auctions/terminos", type="http", auth="public", website=True, sitemap=True)
    def auction_terms(self, **kw):
        from ..models.res_partner import AUCTION_TERMS_VERSION
        return request.render("oulalab_auction.auction_terms_template", {
            "company": request.website.company_id.sudo(),
            "terms_version": AUCTION_TERMS_VERSION,
        })

    @http.route("/auctions", type="http", auth="public", website=True)
    def auctions_list(self, marca=None, tipo=None, ocasion=None, **kw):
        now = fields.Datetime.now()
        base = request.env["liquidation.auction"].sudo().search(
            [("state", "in", ["published", "live"]), ("end_date", ">", now)]
        )
        # Opciones de los filtros: solo valores que existen en subastas activas
        marcas = sorted({a.brand for a in base if a.brand})
        tipos = {a.categ.id: a.categ for a in base if a.categ}
        ocasiones = {}
        for a in base:
            for o in a.occasion_ids:
                ocasiones[o.id] = o
        tipos = sorted(tipos.values(), key=lambda r: r.complete_name or r.name)
        ocasiones = sorted(ocasiones.values(), key=lambda r: r.display_name or "")

        auctions = base
        if marca:
            auctions = auctions.filtered(lambda a: a.brand == marca)
        if tipo and tipo.isdigit():
            auctions = auctions.filtered(lambda a: a.categ.id == int(tipo))
        if ocasion and ocasion.isdigit():
            auctions = auctions.filtered(lambda a: int(ocasion) in a.occasion_ids.ids)

        # Orden al azar, estable durante la sesión para que el filtro no reordene todo.
        seed = request.session.get("auction_shuffle_seed")
        if not seed:
            seed = random.randint(1, 10 ** 9)
            request.session["auction_shuffle_seed"] = seed
        shuffled = list(auctions)
        random.Random(seed).shuffle(shuffled)
        auctions = request.env["liquidation.auction"].sudo().browse([a.id for a in shuffled])

        return request.render(
            "oulalab_auction.auction_list_template",
            {
                "auctions": auctions,
                "now": now,
                "marcas": marcas,
                "tipos": tipos,
                "ocasiones": ocasiones,
                "marca_sel": marca or "",
                "tipo_sel": tipo or "",
                "ocasion_sel": ocasion or "",
            },
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
        server_now = fields.Datetime.now()
        preview_locked = bool(
            partner and not partner.is_oulalab_member
            and auction.state == "live"
            and auction.public_start and server_now < auction.public_start
        )
        remaining_ms = (
            int((auction.public_start - server_now).total_seconds() * 1000)
            if preview_locked else 0
        )

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
                "server_now": server_now,
                "guest_session": bool(partner) and request.env.user._is_public(),
                "guest_name": partner.name if partner else "",
                "guest_rut": partner.vat if partner else "",
                "preview_locked": preview_locked,
                "remaining_ms": remaining_ms,
            },
        )

    @http.route("/auctions/delivery", type="jsonrpc", auth="public")
    def save_delivery(self, mode, rut=None, commune=None, street=None, phone=None, **kw):
        """Guarda RUT + modalidad de entrega del postor antes de permitirle subastar."""
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
    def _find_partner_by_rut(self, clean_rut):
        Partner = request.env["res.partner"].sudo()
        body = clean_rut.split("-")[0]
        candidates = Partner.search([("vat", "ilike", body)], limit=50)
        return candidates.filtered(lambda p: validate_rut(p.vat) == clean_rut)[:1]

    @staticmethod
    def _mask_email(email):
        local, _, domain = email.partition("@")
        return "%s***@%s" % (local[:1], domain)

    def _start_code(self, email, payload, name):
        """Envía el código y deja el correo pendiente en la sesión. Devuelve error o None."""
        Otp = request.env["auction.guest.otp"]
        if Otp.recently_sent(email):
            return "Ya te enviamos un código. Espera un minuto para pedir otro."
        code = Otp.issue(email, payload)
        self._send_code(email, name, code)
        request.session[PENDING_KEY] = email
        return None

    @http.route(["/app", "/auctions/app"], type="http", auth="public", website=True, sitemap=True)
    def app_install(self, **kw):
        """Guía para dejar OulaLab en la pantalla de inicio del teléfono."""
        return request.render("oulalab_auction.app_install_template", {})

    @http.route("/auctions/guest/logout", type="http", auth="public", website=True)
    def guest_logout(self, **kw):
        """Cierra la sesión del postor sin cuenta (dispositivo compartido o cambio de RUT).
        No cierra una sesión de Odoo con cuenta: esa se cierra desde el menú del usuario."""
        self._guest_logout_session()
        return request.redirect("/auctions")

    @http.route("/auctions/guest/lookup", type="jsonrpc", auth="public")
    def guest_lookup(self, rut=None, **kw):
        """Paso 1: con el RUT, si ya existe un correo registrado se envía el código a ese correo."""
        clean = validate_rut(rut)
        if not clean:
            return {"ok": False, "error": "El RUT no es válido. Revísalo (ej: 12.345.678-5)."}
        partner = self._find_partner_by_rut(clean)
        if partner and partner.email:
            email = partner.email.strip().lower()
            error = self._start_code(email, {"partner_id": partner.id}, partner.name)
            if error:
                return {"ok": False, "error": error}
            return {"ok": True, "mode": "code", "masked": self._mask_email(email)}
        return {"ok": True, "mode": "new", "rut": clean}

    @http.route("/auctions/guest/start", type="jsonrpc", auth="public")
    def guest_start(self, name=None, rut=None, email=None, phone=None,
                    mode=None, commune=None, street=None, **kw):
        """Paso 2 (RUT nuevo): valida los datos completos y envía el código."""
        Partner = request.env["res.partner"].sudo()
        clean_rut = validate_rut(rut)
        if not clean_rut:
            return {"ok": False, "error": "El RUT no es válido. Revísalo (ej: 12.345.678-5)."}

        partner = self._find_partner_by_rut(clean_rut)
        if partner and partner.email:
            # Ya tiene correo: el código va a ese correo, no al que escriban aquí.
            email = partner.email.strip().lower()
            error = self._start_code(email, {"partner_id": partner.id}, partner.name)
            if error:
                return {"ok": False, "error": error}
            return {"ok": True, "mode": "code", "masked": self._mask_email(email)}

        name = (name or "").strip()
        email = (email or "").strip().lower()
        phone = (phone or "").strip()
        if len(name) < 3:
            return {"ok": False, "error": "Indica tu nombre completo."}
        if not EMAIL_RE.match(email):
            return {"ok": False, "error": "El correo no es válido."}
        if len(re.sub(r"\D", "", phone)) < 8:
            return {"ok": False, "error": "Indica un teléfono de contacto válido."}
        vals, error = self._validate_delivery(Partner, mode, commune, street)
        if error:
            return {"ok": False, "error": error}

        # Un correo ya usado por otro RUT no se puede reclamar.
        existing = Partner.search([("email", "=ilike", email)], limit=5)
        existing = existing.filtered(lambda p: (p.email or "").lower() == email)[:1]
        if existing and existing.vat and validate_rut(existing.vat) != clean_rut:
            return {"ok": False, "error": (
                "Ese correo ya está asociado a otro RUT. "
                "Escríbenos a hola@oulalab.com para ayudarte."
            )}
        target = partner or existing

        payload = dict(vals, name=name, vat=clean_rut, phone=phone, email=email,
                       partner_id=target.id or False)
        error = self._start_code(email, payload, name)
        if error:
            return {"ok": False, "error": error}
        return {"ok": True, "mode": "code", "masked": self._mask_email(email)}

    @http.route("/auctions/guest/verify", type="jsonrpc", auth="public")
    def guest_verify(self, code=None, **kw):
        email = request.session.get(PENDING_KEY)
        if not email:
            return {"ok": False, "error": "Vuelve a empezar: ingresa tu RUT otra vez."}
        payload = request.env["auction.guest.otp"].consume(email, (code or "").strip())
        if payload is None:
            return {"ok": False, "error": "Código incorrecto o vencido. Pide uno nuevo."}

        Partner = request.env["res.partner"].sudo()
        if payload.get("partner_id"):
            partner = Partner.browse(payload["partner_id"]).exists()
            if not partner:
                return {"ok": False, "error": "No pudimos completar el ingreso. Intenta de nuevo."}
            if not partner.email:
                partner.email = email
            if not partner.vat and payload.get("vat"):
                partner.vat = payload["vat"]
            updates = {k: payload[k] for k in ("auction_delivery_mode", "auction_commune", "street", "phone")
                       if payload.get(k)}
            if "auction_delivery_mode" in payload:
                updates["auction_commune"] = payload.get("auction_commune") or False
            if updates:
                partner.write(updates)
        else:
            # Con retiro en showroom el payload no trae "street": usar get() evita
            # el KeyError que mostraba "street" como error al verificar el código.
            partner = Partner.create(dict(
                {k: payload.get(k) for k in ("auction_delivery_mode", "auction_commune", "street")
                 if payload.get(k)},
                name=payload["name"], email=payload["email"],
                vat=payload["vat"], phone=payload["phone"],
            ))
        request.session[SESSION_KEY] = partner.id
        request.session[GUEST_AT_KEY] = time.time()
        request.session.pop(PENDING_KEY, None)
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
    # Resumen del postor: estado de cada subasta en la que ha ofertado
    # ------------------------------------------------------------------
    @http.route("/auctions/mis-subastas", type="http", auth="public", website=True)
    def my_auctions(self, **kw):
        partner = self._current_partner()
        rows = self._my_auction_rows(partner) if partner else []
        alerts = sum(1 for r in rows if r["alert"])
        return request.render(
            "oulalab_auction.auction_my_template",
            {
                "partner": partner,
                "rows": rows,
                "alerts": alerts,
                "now": fields.Datetime.now(),
                # El bloque de ingreso por RUT necesita los mismos datos que en la ficha.
                "communes": request.env["res.partner"]._fields["auction_commune"].selection,
                "showroom": "Av. La Dehesa 222 of. 817, Lo Barnechea",
            },
        )

    def _fmt_clp(self, amount):
        return "{:,.0f}".format(amount or 0).replace(",", ".")

    def _my_auction_rows(self, partner):
        bids = request.env["auction.bid"].sudo().search([("partner_id", "=", partner.id)])
        by_auction = {}
        for bid in bids:
            by_auction.setdefault(bid.auction_id, []).append(bid)

        rows = []
        for auction, abids in by_auction.items():
            active = [b for b in abids if not b.rejected] or abids
            my_best = max(active, key=lambda b: b.amount)
            state = auction.state
            leader = bool(auction.highest_bid_id and auction.highest_bid_id.partner_id == partner)
            winner = auction.winner_id == partner

            if state == "published":
                key, label, tone = "upcoming", "Próxima", "info"
            elif state == "live":
                if leader:
                    key, label, tone = "winning", "Vas ganando", "success"
                else:
                    key, label, tone = "outbid", "¡Te superaron!", "danger"
            elif state == "pending_payment":
                if winner:
                    key, label, tone = "pay", "Adjudicada: pendiente de pago", "warning"
                else:
                    key, label, tone = "lost", "No adjudicada", "secondary"
            elif state == "sold":
                key, label, tone = (("won", "Ganaste", "success") if winner
                                    else ("lost", "No adjudicada", "secondary"))
            elif state == "unsold":
                key, label, tone = "unsold", "Desierta", "secondary"
            elif state == "cancelled":
                key, label, tone = "cancelled", "Cancelada", "secondary"
            else:
                key, label, tone = "other", "Sin estado", "secondary"

            min_next = auction._min_next_bid_for(partner) if state == "live" else None
            rows.append({
                "id": auction.id,
                "name": auction.web_title or "Prenda en subasta",
                "state": state,
                "key": key,
                "label": label,
                "tone": tone,
                "alert": key == "outbid",
                "my_amount": self._fmt_clp(my_best.amount),
                "highest": self._fmt_clp(auction.highest_amount),
                "bid_count": auction.bid_count,
                "min_next": self._fmt_clp(min_next) if min_next is not None else None,
                "end_date": auction.end_date,
                "sort": {"outbid": 0, "winning": 1, "pay": 2, "upcoming": 3}.get(key, 4),
            })
        rows.sort(key=lambda r: (r["sort"], r["end_date"] or fields.Datetime.now()))
        return rows

    # ------------------------------------------------------------------
    # Estado en vivo (polling ligero para reflejar ofertas ajenas / extensiones)
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
    # Registro de oferta (requiere sesión iniciada)
    # ------------------------------------------------------------------
    @http.route("/auctions/<int:auction_id>/bid", type="jsonrpc", auth="public")
    def submit_bid(self, auction_id, amount, **kw):
        auction = request.env["liquidation.auction"].sudo().browse(auction_id)
        if not auction.exists():
            return {"ok": False, "error": "Subasta inexistente."}

        partner = self._current_partner()
        if not partner:
            return {"ok": False, "error": "Verifica tu correo antes de subastar."}
        if not partner.auction_terms_ok:
            if not kw.get("accept_terms"):
                return {"ok": False, "need_terms": True,
                        "error": "Debes aceptar los Términos y condiciones de subastas."}
            partner._auction_accept_terms()
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
