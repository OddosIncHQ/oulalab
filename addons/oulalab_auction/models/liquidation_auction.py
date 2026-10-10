from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class LiquidationAuction(models.Model):
    _name = "liquidation.auction"
    _description = "Subasta de liquidación de prenda"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "end_date asc, id desc"

    # ------------------------------------------------------------------
    # Campos base
    # ------------------------------------------------------------------
    name = fields.Char(compute="_compute_name", store=True)
    active = fields.Boolean(default=True)

    product_id = fields.Many2one(
        "product.template",
        string="Prenda",
        required=True,
        ondelete="restrict",
        help="Cada prenda es un product.template único (sin variantes).",
    )
    barcode = fields.Char(related="product_id.barcode", string="Código de barras", store=True)
    image_128 = fields.Image(related="product_id.image_128", string="Imagen", store=False)

    # URLs externas de imágenes (hasta 4) para el carrusel del portal.
    image_url_1 = fields.Char(string="URL imagen 1")
    image_url_2 = fields.Char(string="URL imagen 2")
    image_url_3 = fields.Char(string="URL imagen 3")
    image_url_4 = fields.Char(string="URL imagen 4")

    reason = fields.Selection(
        [
            ("worn", "Muy usada"),
            ("off_season", "Fuera de temporada"),
            ("dead_stock", "Baja rotación"),
            ("other", "Otro"),
        ],
        string="Motivo de retiro",
        default="off_season",
    )
    description = fields.Html(string="Descripción pública")

    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id.id,
        required=True,
    )
    reserve_price = fields.Monetary(
        string="Precio mínimo (reserva)",
        required=True,
        currency_field="currency_id",
        help="Puja mínima aceptable. Bajo este monto la subasta se declara desierta.",
    )
    min_increment = fields.Monetary(
        string="Incremento mínimo fijo",
        currency_field="currency_id",
        default=1000.0,
        help="Piso absoluto del salto entre pujas (además del porcentaje).",
    )
    member_increment_pct = fields.Float(
        string="Incremento socio (%)",
        default=2.0,
        help="Los socios pueden superar la puja actual con un salto porcentual menor.",
    )
    public_increment_pct = fields.Float(
        string="Incremento público (%)",
        default=5.0,
    )

    # ------------------------------------------------------------------
    # Temporización
    # ------------------------------------------------------------------
    start_date = fields.Datetime(
        string="Inicio",
        required=True,
        default=fields.Datetime.now,
        help="Momento en que abre la subasta (acceso de socios).",
    )
    member_preview_hours = fields.Integer(
        string="Preview socios (horas)",
        default=24,
        help="Ventana en la que SOLO los socios OulaLab pueden pujar.",
    )
    public_start = fields.Datetime(
        string="Apertura pública",
        compute="_compute_public_start",
        store=True,
    )
    end_date = fields.Datetime(string="Cierre", required=True)
    anti_sniping_minutes = fields.Integer(
        string="Anti-sniping (min)",
        default=5,
        help="Si entra una puja dentro de estos minutos finales, el cierre se extiende "
        "ese mismo lapso. Evita el 'francotirador' del último segundo.",
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("published", "Publicada"),
            ("live", "En curso"),
            ("pending_payment", "Esperando pago"),
            ("sold", "Adjudicada"),
            ("unsold", "Desierta"),
            ("cancelled", "Cancelada"),
        ],
        default="draft",
        tracking=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Pujas / resultado
    # ------------------------------------------------------------------
    bid_ids = fields.One2many("auction.bid", "auction_id", string="Pujas")
    bid_count = fields.Integer(compute="_compute_bid_stats", store=True)
    highest_bid_id = fields.Many2one("auction.bid", compute="_compute_bid_stats", store=True)
    highest_amount = fields.Monetary(
        currency_field="currency_id", compute="_compute_bid_stats", store=True
    )
    winner_id = fields.Many2one("res.partner", string="Adjudicatario", readonly=True)
    sale_order_id = fields.Many2one("sale.order", string="Pedido generado", readonly=True)
    current_winner_bid_id = fields.Many2one(
        "auction.bid", string="Puja adjudicada", readonly=True
    )
    payment_deadline_hours = fields.Integer(
        string="Plazo de pago (horas)",
        default=24,
        help="Horas que tiene el ganador para pagar antes de reasignar al siguiente postor.",
    )
    payment_deadline = fields.Datetime(string="Vence el pago", readonly=True)
    payment_url = fields.Char(compute="_compute_payment_url")

    def _compute_payment_url(self):
        for rec in self:
            if rec.sale_order_id:
                rec.payment_url = rec.get_base_url() + rec.sale_order_id.get_portal_url()
            else:
                rec.payment_url = False

    # ==================================================================
    # Computes
    # ==================================================================
    @api.depends("product_id")
    def _compute_name(self):
        for rec in self:
            rec.name = _("Subasta: %s") % (rec.product_id.name or _("(sin prenda)"))

    def _get_image_urls(self):
        """Lista ordenada de URLs de imagen no vacías (para el carrusel)."""
        self.ensure_one()
        urls = [self.image_url_1, self.image_url_2, self.image_url_3, self.image_url_4]
        return [u.strip() for u in urls if u and u.strip()]

    @api.depends("start_date", "member_preview_hours")
    def _compute_public_start(self):
        for rec in self:
            if rec.start_date:
                rec.public_start = rec.start_date + timedelta(
                    hours=rec.member_preview_hours or 0
                )
            else:
                rec.public_start = False

    @api.depends("bid_ids", "bid_ids.amount")
    def _compute_bid_stats(self):
        for rec in self:
            bids = rec.bid_ids.sorted(lambda b: (b.amount, b.id), reverse=True)
            rec.bid_count = len(bids)
            rec.highest_bid_id = bids[:1].id
            rec.highest_amount = bids[:1].amount if bids else 0.0

    # ==================================================================
    # Lógica de negocio: preferencia de socio
    # ==================================================================
    def _min_next_bid_for(self, partner):
        """Puja mínima válida para ESTE partner.

        La preferencia de socio se materializa de dos formas:
          1) Ventana de preview (gestionada en place_bid / puede pujar antes).
          2) Incremento porcentual menor -> le cuesta menos mantenerse arriba.
        """
        self.ensure_one()
        highest = self.highest_amount
        if not highest:
            return self.reserve_price
        pct = (
            self.member_increment_pct
            if (partner and partner.is_oulalab_member)
            else self.public_increment_pct
        )
        step = max(self.min_increment, highest * (pct / 100.0))
        return self.currency_id.round(highest + step)

    def _can_bid_now(self, partner):
        """(bool, motivo) — ¿puede este partner pujar en este instante?"""
        self.ensure_one()
        now = fields.Datetime.now()
        if self.state != "live":
            return False, _("La subasta no está en curso.")
        if now >= self.end_date:
            return False, _("La subasta ya cerró.")
        if not (partner and partner._auction_delivery_ready()):
            return False, _(
                "Antes de pujar, indica cómo quieres recibir la prenda: "
                "retiro en showroom o despacho a Lo Barnechea, Las Condes o Vitacura."
            )
        if not (partner and partner.is_oulalab_member) and now < self.public_start:
            return False, _(
                "Estás en la ventana exclusiva para socios OulaLab. "
                "La apertura pública es a las %s."
            ) % fields.Datetime.to_string(self.public_start)
        return True, ""

    # ==================================================================
    # Núcleo transaccional de puja (concurrencia segura)
    # ==================================================================
    def place_bid(self, partner, amount):
        """Registra una puja de forma atómica.

        Se bloquea la fila de la subasta (SELECT ... FOR UPDATE) para serializar
        pujas concurrentes: dos usuarios pujando en el mismo milisegundo no pueden
        ambos 'ganar' contra el mismo highest. El segundo espera al commit del
        primero y revalida contra el estado ya actualizado.
        """
        self.ensure_one()

        # 1) Bloqueo pesimista de la fila.
        self.env.cr.execute(
            "SELECT id FROM liquidation_auction WHERE id = %s FOR UPDATE NOWAIT",
            (self.id,),
        )
        # 2) Releer valores frescos tras el lock (el cache podría estar viejo).
        self.invalidate_recordset(
            ["highest_amount", "highest_bid_id", "state", "end_date"]
        )

        can, reason = self._can_bid_now(partner)
        if not can:
            raise ValidationError(reason)

        amount = self.currency_id.round(float(amount))
        min_required = self._min_next_bid_for(partner)
        if amount < min_required:
            raise ValidationError(
                _("Tu puja debe ser al menos %(min)s.")
                % {"min": self.currency_id.format(min_required)}
                if hasattr(self.currency_id, "format")
                else _("Tu puja debe ser al menos %s.") % min_required
            )

        bid = self.env["auction.bid"].create(
            {
                "auction_id": self.id,
                "partner_id": partner.id,
                "amount": amount,
            }
        )

        # 3) Anti-sniping (soft close): extiende el cierre si la puja entra al final.
        now = fields.Datetime.now()
        remaining = (self.end_date - now).total_seconds()
        if remaining < (self.anti_sniping_minutes or 0) * 60:
            self.end_date = now + timedelta(minutes=self.anti_sniping_minutes)

        self.message_post(
            body=_("Nueva puja: %(amt)s por %(name)s")
            % {"amt": amount, "name": partner.name}
        )
        return bid

    # ==================================================================
    # Ciclo de vida / cron
    # ==================================================================
    def action_publish(self):
        for rec in self:
            if not rec.end_date or rec.end_date <= rec.start_date:
                raise UserError(_("El cierre debe ser posterior al inicio."))
            rec.state = "published"

    def action_cancel(self):
        for rec in self:
            if rec.bid_ids:
                raise UserError(_("No puedes cancelar una subasta con pujas."))
            rec.state = "cancelled"

    def action_back_to_draft(self):
        self.write({"state": "draft"})

    def action_open_web(self):
        """Abre la ficha pública de esta subasta en una pestaña nueva."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": "/auctions/%s" % self.id,
            "target": "new",
        }

    @api.model
    def _cron_manage_states(self):
        """Cron de 1 minuto: abre y cierra subastas según reloj del servidor."""
        now = fields.Datetime.now()
        # Publicada -> En curso
        self.search(
            [("state", "=", "published"), ("start_date", "<=", now)]
        ).write({"state": "live"})
        # En curso -> cierre
        to_close = self.search([("state", "=", "live"), ("end_date", "<=", now)])
        for auction in to_close:
            auction._close_auction()

        # Esperando pago: ¿pagó? ¿se venció el plazo?
        pending = self.search([("state", "=", "pending_payment")])
        for auction in pending:
            if auction._is_current_order_paid():
                auction._mark_paid()
            elif auction.payment_deadline and now > auction.payment_deadline:
                auction._handle_non_payment()

    def _close_auction(self):
        """Al cerrar: avisa a los perdedores y adjudica al mejor postor."""
        self.ensure_one()
        self._award_to_next_bidder()

    def _award_to_next_bidder(self):
        """Adjudica a la mejor puja activa sobre la reserva; si no hay, declara desierta."""
        self.ensure_one()
        next_bid = self.bid_ids.filtered(
            lambda b: not b.rejected and b.amount >= self.reserve_price
        ).sorted(lambda b: (b.amount, b.id), reverse=True)[:1]

        if not next_bid:
            self.write({"state": "unsold", "current_winner_bid_id": False,
                        "winner_id": False})
            self._notify_losers()
            return

        order = self._create_winner_order(next_bid)
        self.write({
            "state": "pending_payment",
            "current_winner_bid_id": next_bid.id,
            "winner_id": next_bid.partner_id.id,
            "sale_order_id": order.id,
            "payment_deadline": fields.Datetime.now()
            + timedelta(hours=self.payment_deadline_hours or 24),
        })
        self._send_winner_email()

    def _create_winner_order(self, bid):
        """Crea y CONFIRMA el pedido del ganador, generando el link de pago del portal."""
        self.ensure_one()
        variant = self.product_id.product_variant_id
        order = self.env["sale.order"].create(
            {
                "partner_id": bid.partner_id.id,
                "origin": self.name,
                "order_line": [
                    (0, 0, {
                        "product_id": variant.id,
                        "product_uom_qty": 1,
                        "price_unit": bid.amount,
                        "name": _("Adjudicación subasta: %s") % self.product_id.name,
                    })
                ],
            }
        )
        order.action_confirm()           # pasa a pedido en firme -> habilita el pago
        order._portal_ensure_token()     # asegura el token del enlace de portal
        return order

    # ------------------------------------------------------------------
    # Pago / reasignación
    # ------------------------------------------------------------------
    def _is_current_order_paid(self):
        self.ensure_one()
        order = self.sale_order_id
        if not order:
            return False
        return any(
            t.state in ("done", "authorized") for t in order.transaction_ids
        )

    def _mark_paid(self):
        self.ensure_one()
        if self.current_winner_bid_id:
            self.current_winner_bid_id.rejected = False
        self.write({"state": "sold"})
        self._notify_losers()

    def _handle_non_payment(self):
        """El ganador no pagó a tiempo: descarta su puja, cancela su pedido y reasigna."""
        self.ensure_one()
        if self.current_winner_bid_id:
            self.current_winner_bid_id.rejected = True
        if self.sale_order_id:
            self.sale_order_id._action_cancel()
            self.sale_order_id = False
        self.message_post(
            body=_("El ganador no pagó dentro del plazo. Reasignando al siguiente postor.")
        )
        self._award_to_next_bidder()

    # ------------------------------------------------------------------
    # Emails
    # ------------------------------------------------------------------
    def _send_winner_email(self):
        self.ensure_one()
        template = self.env.ref(
            "oulalab_auction.mail_template_auction_winner", raise_if_not_found=False
        )
        if template and self.winner_id:
            template.send_mail(self.id, force_send=True)

    def _notify_losers(self):
        """Avisa a cada postor que no resultó adjudicado (una sola vez)."""
        self.ensure_one()
        template = self.env.ref(
            "oulalab_auction.mail_template_auction_loser", raise_if_not_found=False
        )
        if not template:
            return
        winner = self.current_winner_bid_id.partner_id if self.current_winner_bid_id else self.env["res.partner"]
        losers = self.bid_ids.mapped("partner_id") - winner
        for partner in losers:
            if not partner.email:
                continue
            template.send_mail(
                self.id, force_send=True,
                email_values={"email_to": partner.email},
            )

    def action_view_order(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.sale_order_id.id,
            "view_mode": "form",
        }
