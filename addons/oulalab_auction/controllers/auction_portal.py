from odoo import fields, http
from odoo.http import request


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

        return request.render(
            "oulalab_auction.auction_detail_template",
            {
                "auction": auction,
                "partner": partner,
                "is_member": is_member,
                "is_public": request.env.user._is_public(),
                "min_next": min_next,
                "server_now": fields.Datetime.now(),
            },
        )

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
