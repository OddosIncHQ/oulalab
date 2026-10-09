from odoo import fields, http
from odoo.http import request

from ..models.res_partner import validate_rut


class AuctionPortal(http.Controller):

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

        partner = request.env.user.partner_id if not request.env.user._is_public() else None
        is_member = bool(partner and partner.is_oulalab_member)
        min_next = auction._min_next_bid_for(partner)
        communes = request.env["res.partner"]._fields["auction_commune"].selection

        return request.render(
            "oulalab_auction.auction_detail_template",
            {
                "auction": auction,
                "partner": partner,
                "is_member": is_member,
                "is_public": request.env.user._is_public(),
                "delivery_ready": bool(partner and partner._auction_delivery_ready())
                and not kw.get("edit_delivery"),
                "communes": communes,
                "showroom": "Av. La Dehesa 222 of. 817, Lo Barnechea",
                "min_next": min_next,
                "server_now": fields.Datetime.now(),
            },
        )

    @http.route("/auctions/delivery", type="jsonrpc", auth="user")
    def save_delivery(self, mode, rut=None, commune=None, street=None, phone=None, **kw):
        """Guarda RUT + modalidad de entrega del postor antes de permitirle pujar."""
        partner = request.env.user.partner_id
        Partner = request.env["res.partner"].sudo()

        # RUT obligatorio para todos (verificación de identidad).
        clean_rut = validate_rut(rut)
        if not clean_rut:
            return {"ok": False, "error": "El RUT no es válido. Revísalo (ej: 12.345.678-5)."}

        valid_communes = dict(Partner._fields["auction_commune"].selection)
        if mode == "delivery":
            if commune not in valid_communes:
                return {"ok": False, "error": "Comuna fuera de cobertura de despacho."}
            if not street:
                return {"ok": False, "error": "Indica la dirección de despacho."}
            ok, reason = Partner._auction_verify_address(street, valid_communes[commune])
            if not ok:
                return {"ok": False, "error": reason}
            vals = {
                "auction_delivery_mode": "delivery",
                "auction_commune": commune,
                "street": street,
            }
        elif mode == "pickup":
            vals = {"auction_delivery_mode": "pickup", "auction_commune": False}
        else:
            return {"ok": False, "error": "Modalidad inválida."}

        vals["vat"] = clean_rut
        if phone:
            vals["phone"] = phone
        partner.sudo().write(vals)
        return {"ok": True}

    # ------------------------------------------------------------------
    # Estado en vivo (polling ligero para reflejar pujas ajenas / extensiones)
    # ------------------------------------------------------------------
    @http.route("/auctions/<int:auction_id>/state", type="jsonrpc", auth="public")
    def auction_state(self, auction_id, **kw):
        auction = request.env["liquidation.auction"].sudo().browse(auction_id)
        if not auction.exists():
            return {"ok": False}
        partner = (
            request.env.user.partner_id if not request.env.user._is_public() else None
        )
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
    @http.route("/auctions/<int:auction_id>/bid", type="jsonrpc", auth="user")
    def submit_bid(self, auction_id, amount, **kw):
        auction = request.env["liquidation.auction"].sudo().browse(auction_id)
        if not auction.exists():
            return {"ok": False, "error": "Subasta inexistente."}

        partner = request.env.user.partner_id
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
