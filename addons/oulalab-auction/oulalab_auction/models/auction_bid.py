from odoo import fields, models


class AuctionBid(models.Model):
    _name = "auction.bid"
    _description = "Puja de subasta"
    _order = "amount desc, id desc"

    auction_id = fields.Many2one(
        "liquidation.auction",
        string="Subasta",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner", string="Postor", required=True, index=True
    )
    amount = fields.Monetary(
        string="Monto",
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="auction_id.currency_id", store=True, readonly=True
    )
    is_member = fields.Boolean(
        related="partner_id.is_oulalab_member",
        string="Socio",
        store=True,
        readonly=True,
    )

    # Toda validación de reglas (monto mínimo, ventana, estado, concurrencia)
    # vive en liquidation.auction.place_bid(). Este modelo solo persiste el hecho.
