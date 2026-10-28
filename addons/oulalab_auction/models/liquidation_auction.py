import base64
import logging
import re
from datetime import datetime, time, timedelta

import pytz

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

# Reglas de cobro (v57)
MIN_PAYMENT_HOURS = 24        # plazo mínimo efectivo, aunque el registro diga menos
PENDING_GRACE_HOURS = 24      # margen extra si hay un pago en línea "pendiente"
REMINDER_HOURS_BEFORE = 6     # recordatorio antes de vencer
QUIET_START, QUIET_END = 21, 9  # el plazo no vence entre 21:00 y 09:00 (hora Chile)
QUIET_MOVE_TO = 12            # si cae en ese rango, se mueve a las 12:00
AUCTION_TZ = "America/Santiago"


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

    # URLs externas de imágenes (hasta 10) para el carrusel del portal.
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
        string="Precio mínimo",
        required=True,
        currency_field="currency_id",
        help="Oferta mínima aceptable. Bajo este monto la subasta se declara desierta.",
    )
    retail_price = fields.Monetary(
        string="Precio retail de referencia",
        currency_field="currency_id",
        help="Precio de venta retail del producto, solo como referencia para el público.",
    )
    min_increment = fields.Monetary(
        string="Incremento mínimo fijo",
        currency_field="currency_id",
        default=1000.0,
        help="Piso absoluto del salto entre ofertas (además del porcentaje).",
    )
    member_increment_pct = fields.Float(
        string="Incremento socio (%)",
        default=2.0,
        help="Los socios pueden superar la oferta actual con un salto porcentual menor.",
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
        help="Ventana en la que SOLO los socios OulaLab pueden subastar.",
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
        help="Si entra una oferta dentro de estos minutos finales, el cierre se extiende "
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
    # Ofertas / resultado
    # ------------------------------------------------------------------
    bid_ids = fields.One2many("auction.bid", "auction_id", string="Ofertas")
    bid_count = fields.Integer(compute="_compute_bid_stats", store=True)
    highest_bid_id = fields.Many2one("auction.bid", compute="_compute_bid_stats", store=True)
    highest_amount = fields.Monetary(
        currency_field="currency_id", compute="_compute_bid_stats", store=True
    )
    winner_id = fields.Many2one("res.partner", string="Adjudicatario", readonly=True)
    sale_order_id = fields.Many2one("sale.order", string="Pedido generado", readonly=True)
    current_winner_bid_id = fields.Many2one(
        "auction.bid", string="Oferta adjudicada", readonly=True
    )
    payment_deadline_hours = fields.Integer(
        string="Plazo de pago (horas)",
        default=24,
        help="Horas que tiene el ganador para pagar antes de reasignar al siguiente postor. "
        "Mínimo efectivo 24 h; si el vencimiento cae entre 21:00 y 09:00 (hora Chile) "
        "se mueve a las 12:00.",
    )
    payment_deadline = fields.Datetime(string="Vence el pago", readonly=True)
    payment_reminder_sent = fields.Boolean(
        string="Recordatorio de pago enviado", readonly=True, copy=False
    )
    payment_url = fields.Char(compute="_compute_payment_url")

    def _compute_payment_url(self):
        for rec in self:
            if rec.sale_order_id:
                rec.payment_url = rec.get_base_url() + rec.sale_order_id.get_portal_url()
            else:
                rec.payment_url = False

    # ==================================================================
    # Catálogo (filtros): marca, tipo de prenda y ocasión vienen del producto
    brand = fields.Char(related="product_id.x_studio_marca", string="Marca", store=True)
    size = fields.Char(compute="_compute_size", string="Talla")
    barcode = fields.Char(related="product_id.barcode", string="Código de barras")
    categ = fields.Many2one(related="product_id.categ_id", string="Tipo de prenda", store=True)
    occasion_ids = fields.Many2many(related="product_id.x_studio_ocasiones", string="Ocasión")

    # Título y descripción para el sitio web (no se muestra el nombre de la base de datos)
    web_title = fields.Char(compute="_compute_web_title", string="Título web")
    web_description = fields.Html(compute="_compute_web_title", string="Descripción web")

    def _compute_size(self):
        # x_studio_talla es un campo de selección en product.template: se lee como texto
        # (un related Char fallaba al cargar el registro).
        for rec in self:
            value = rec.product_id.x_studio_talla if rec.product_id else False
            rec.size = str(value) if value else False

    def _compute_web_title(self):
        for rec in self:
            seo = rec.product_id.seo_name if "seo_name" in rec.product_id._fields else False
            desc = rec.description or ""
            m = re.search(r"<strong>(.*?)</strong>", desc, re.S)
            if seo:
                rec.web_title = seo
                rec.web_description = desc
            elif m:
                rec.web_title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                rec.web_description = re.sub(r"<p>\s*<strong>.*?</strong>\s*</p>", "", desc, count=1, flags=re.S)
            else:
                rec.web_title = False
                rec.web_description = desc

    # Computes
    # ==================================================================
    @api.depends("product_id")
    def _compute_name(self):
        for rec in self:
            rec.name = _("Subasta: %s") % (rec.product_id.name or _("(sin prenda)"))

    winning_amount_untaxed = fields.Monetary(
        string="Oferta sin impuesto",
        currency_field="currency_id",
        compute="_compute_winning_untaxed",
        help="Oferta adjudicada descontando el impuesto del producto. Es el precio "
        "unitario del pedido; luego el impuesto se vuelve a aplicar en la línea.",
    )

    @api.depends("current_winner_bid_id.amount", "highest_amount", "product_id")
    def _compute_winning_untaxed(self):
        for rec in self:
            gross = (rec.current_winner_bid_id.amount
                     if rec.current_winner_bid_id else rec.highest_amount) or 0.0
            rec.winning_amount_untaxed = rec._untaxed_from_gross(gross)

    def _auction_warehouse(self, variant, company):
        """Almacén del pedido de subasta.

        Odoo solo aplica una regla de reabastecimiento si el almacén de la regla
        coincide con el del pedido. Usamos el almacén que suministra la ruta de
        subastas del producto; si no tiene, el almacén por defecto de la compañía.
        """
        route = variant.route_ids.filtered(
            lambda r: r.supplied_wh_id
            and (not r.company_id or r.company_id == company)
        )[:1]
        if route:
            return route.supplied_wh_id
        return self.env["stock.warehouse"].with_company(company).search(
            [("company_id", "=", company.id)], limit=1
        )

    def _auction_company(self):
        """Compañía de la venta: la del producto; si no tiene, la de sus
        impuestos; y solo como último recurso la compañía del usuario actual
        (el cron corre como OdooBot, cuya compañía puede ser otra)."""
        self.ensure_one()
        variant = self.product_id.product_variant_id
        return (
            self.product_id.company_id
            or variant.taxes_id[:1].company_id
            or self.env.company
        )

    def _auction_taxes(self):
        """Impuestos de venta del producto (taxes_id), filtrados por compañía."""
        self.ensure_one()
        variant = self.product_id.product_variant_id
        company = self._auction_company()
        return variant.taxes_id.filtered(
            lambda t: not t.company_id or t.company_id == company
        ) if variant else self.env["account.tax"]

    def _untaxed_from_gross(self, gross):
        """Neto a partir de un monto con impuesto incluido (la oferta es C/IVA),
        usando el impuesto registrado en el producto (taxes_id)."""
        self.ensure_one()
        if not gross:
            return 0.0
        taxes = self._auction_taxes()
        percent = sum(t.amount for t in taxes if t.amount_type == "percent")
        if percent:
            net = gross / (1.0 + percent / 100.0)
        else:
            net = gross
        return self.currency_id.round(net) if self.currency_id else round(net, 2)

    def _image_url_fields(self):
        return ["image_url_%d" % i for i in range(1, 11)]

    def _get_primary_image_url(self):
        """Foto representativa: la ÚLTIMA cargada, que por convención es la
        prenda sola. Si no hay URLs, la foto del producto de Alquiler."""
        self.ensure_one()
        for name in reversed(self._image_url_fields()):
            url = self[name]
            if url and url.strip():
                return url.strip()
        if self.product_id:
            return "%s/web/image/product.template/%s/image_1024" % (
                self.get_base_url(), self.product_id.id)
        return ""

    def _get_image_urls(self):
        """URLs para el carrusel: primero la prenda sola (la última cargada),
        después las de contexto en su orden original."""
        self.ensure_one()
        urls = [self[n].strip() for n in self._image_url_fields() if self[n] and self[n].strip()]
        if len(urls) > 1:
            urls = [urls[-1]] + urls[:-1]
        return urls

    # Datos del producto que enriquecen la ficha pública
    ai_description = fields.Text(compute="_compute_product_info", string="Descripción IA")
    care_tips = fields.Text(compute="_compute_product_info", string="Tips de cuidado")
    materials = fields.Char(compute="_compute_product_info", string="Materialidad")
    occasions = fields.Char(compute="_compute_product_info", string="Ocasiones")
    colorimetry = fields.Char(compute="_compute_product_info", string="Clasificación colorimétrica")
    ideal_weather = fields.Char(compute="_compute_product_info", string="Clima ideal")

    def _compute_product_info(self):
        """Lee los atributos de Studio del producto. Cada campo puede no existir
        en esta base, así que se consulta antes de leerlo."""
        mapping = {
            "ai_description": "x_studio_ia_description",
            "care_tips": "x_studio_tips_cuidado",
            "materials": "x_studio_materialidad",
            "occasions": "x_studio_ocasiones",
            "colorimetry": "x_studio_clasificacion_colorimetrica",
            "ideal_weather": "x_studio_clima_ideal",
        }
        for rec in self:
            product = rec.product_id
            for target, source in mapping.items():
                value = False
                if product and source in product._fields:
                    raw = product[source]
                    if raw:
                        field = product._fields[source]
                        if field.type in ("many2many", "one2many"):
                            value = ", ".join(raw.mapped("display_name"))
                        elif field.type == "many2one":
                            value = raw.display_name
                        elif field.type == "selection":
                            value = dict(field._description_selection(self.env)).get(raw, raw)
                        else:
                            value = raw
                rec[target] = value or False

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
        """Oferta mínima válida para ESTE partner.

        La preferencia de socio se materializa de dos formas:
          1) Ventana de preview (gestionada en place_bid / puede subastar antes).
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
        """(bool, motivo) — ¿puede este partner subastar en este instante?"""
        self.ensure_one()
        now = fields.Datetime.now()
        if self.state != "live":
            return False, _("La subasta no está en curso.")
        if now >= self.end_date:
            return False, _("La subasta ya cerró.")
        if not (partner and partner.auction_terms_ok):
            return False, _(
                "Para subastar debes aceptar los Términos y condiciones de subastas."
            )
        if not (partner and partner._auction_delivery_ready()):
            return False, _(
                "Antes de subastar, indica cómo quieres recibir la prenda: "
                "retiro en showroom o despacho a Lo Barnechea, Las Condes o Vitacura."
            )
        if not (partner and partner.is_oulalab_member) and now < self.public_start:
            return False, _(
                "Estás en la ventana exclusiva para socios OulaLab. "
                "La apertura pública es a las %s."
            ) % fields.Datetime.to_string(self.public_start)
        return True, ""

    # ==================================================================
    # Núcleo transaccional de oferta (concurrencia segura)
    # ==================================================================
    def place_bid(self, partner, amount):
        """Registra una oferta de forma atómica.

        Se bloquea la fila de la subasta (SELECT ... FOR UPDATE) para serializar
        ofertas concurrentes: dos usuarios subastando en el mismo milisegundo no pueden
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
                _("Tu oferta debe ser al menos %(min)s.")
                % {"min": self.currency_id.format(min_required)}
                if hasattr(self.currency_id, "format")
                else _("Tu oferta debe ser al menos %s.") % min_required
            )

        bid = self.env["auction.bid"].create(
            {
                "auction_id": self.id,
                "partner_id": partner.id,
                "amount": amount,
                "terms_version": partner.auction_terms_version,
            }
        )

        # 3) Anti-sniping (soft close): extiende el cierre si la oferta entra al final.
        now = fields.Datetime.now()
        remaining = (self.end_date - now).total_seconds()
        if remaining < (self.anti_sniping_minutes or 0) * 60:
            self.end_date = now + timedelta(minutes=self.anti_sniping_minutes)

        self.message_post(
            body=_("Nueva oferta: %(amt)s por %(name)s")
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
                raise UserError(_("No puedes cancelar una subasta con ofertas."))
            rec.state = "cancelled"

    def action_back_to_draft(self):
        """Vuelve a borrador SIN arrastrar un ciclo anterior.

        Una subasta que ya tuvo ofertas o adjudicación no se recicla: quedarían
        pujas rechazadas, ganador, pedido y plazo de otro ciclo. Para repetirla
        se duplica (las ofertas no se copian).
        """
        for rec in self:
            if rec.state in ("pending_payment", "sold"):
                raise UserError(_(
                    "La subasta %s está adjudicada o esperando pago; no puede volver a borrador."
                ) % rec.display_name)
            if rec.bid_ids:
                raise UserError(_(
                    "La subasta %s ya tiene ofertas. Para repetirla, duplícala "
                    "(Acción → Duplicar): la copia nace sin ofertas ni adjudicación."
                ) % rec.display_name)
        self.write({
            "state": "draft",
            "winner_id": False,
            "sale_order_id": False,
            "current_winner_bid_id": False,
            "payment_deadline": False,
            "payment_reminder_sent": False,
        })

    def action_open_product(self):
        """Abre la ficha del producto (plantilla) de la subasta."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.template",
            "res_id": self.product_id.id,
            "view_mode": "form",
            "target": "current",
        }

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
            try:
                with self.env.cr.savepoint():
                    auction._close_auction()
            except Exception:
                _logger.exception("Subasta %s: error al cerrar", auction.id)

        # Esperando pago: ¿pagó? ¿se venció el plazo?
        pending = self.search([("state", "=", "pending_payment")])
        for auction in pending:
            try:
                with self.env.cr.savepoint():
                    auction._check_payment_status(now)
            except Exception:
                _logger.exception("Subasta %s: error en control de pago", auction.id)

    def _check_payment_status(self, now):
        """Un paso del control de pago de una subasta 'Esperando pago'."""
        self.ensure_one()
        if self._is_current_order_paid():
            self._mark_paid()
            return
        deadline = self.payment_deadline
        if not deadline:
            return
        if now > deadline:
            # Pago en línea en curso: se espera un margen antes de cancelar.
            if self._has_pending_online_payment() and now <= deadline + timedelta(
                hours=PENDING_GRACE_HOURS
            ):
                return
            self._handle_non_payment()
            return
        if not self.payment_reminder_sent and now >= deadline - timedelta(
            hours=REMINDER_HOURS_BEFORE
        ):
            self._send_payment_reminder()

    def _close_auction(self):
        """Al cerrar: avisa a los perdedores y adjudica al mejor postor."""
        self.ensure_one()
        self._award_to_next_bidder()

    def _award_to_next_bidder(self):
        """Adjudica a la mejor oferta activa sobre la reserva; si no hay, declara desierta."""
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
        deadline = self._compute_payment_deadline()
        self.write({
            "state": "pending_payment",
            "current_winner_bid_id": next_bid.id,
            "winner_id": next_bid.partner_id.id,
            "sale_order_id": order.id,
            "payment_deadline": deadline,
            "payment_reminder_sent": False,
        })
        self.message_post(body=_(
            "Adjudicada a %(partner)s por $%(amount)s (pedido %(order)s). "
            "Vence el pago: %(deadline)s."
        ) % {
            "partner": next_bid.partner_id.display_name,
            "amount": "{:,.0f}".format(next_bid.amount).replace(",", "."),
            "order": order.name,
            "deadline": self._format_local(deadline),
        })
        self._send_winner_email()

    def _compute_payment_deadline(self, start=None):
        """Plazo de pago: mínimo 24 h y nunca vence de noche (hora Chile).

        Devuelve un datetime UTC naive, como guarda Odoo.
        """
        self.ensure_one()
        start = start or fields.Datetime.now()
        hours = max(self.payment_deadline_hours or 0, MIN_PAYMENT_HOURS)
        deadline_utc = start + timedelta(hours=hours)
        tz = pytz.timezone(AUCTION_TZ)
        local = pytz.utc.localize(deadline_utc).astimezone(tz)
        if local.hour >= QUIET_START or local.hour < QUIET_END:
            day = local.date() + timedelta(days=1) if local.hour >= QUIET_START else local.date()
            local = tz.localize(datetime.combine(day, time(QUIET_MOVE_TO, 0)))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _format_local(self, dt):
        if not dt:
            return ""
        local = pytz.utc.localize(dt).astimezone(pytz.timezone(AUCTION_TZ))
        return local.strftime("%d-%m-%Y %H:%M")

    def _create_winner_order(self, bid):
        """Crea el presupuesto del ganador listo para pagar en el portal.

        Queda como presupuesto ENVIADO con pago en línea obligatorio al 100 %.
        Así el portal muestra el botón "Aceptar y pagar" (Odoo solo lo muestra
        en presupuestos, nunca en pedidos ya confirmados). Al aprobarse el pago,
        Odoo confirma el pedido por sí solo y recién ahí se genera la entrega.
        """
        self.ensure_one()
        variant = self.product_id.product_variant_id
        taxes = self._auction_taxes()
        net = self._untaxed_from_gross(bid.amount)   # la oferta es C/IVA -> precio neto
        company = self._auction_company()
        SaleOrder = self.env["sale.order"].with_company(company)
        warehouse = self._auction_warehouse(variant, company)
        vals = {
            "company_id": company.id,
            "partner_id": bid.partner_id.id,
            "origin": self.name,
            # Vínculo permanente: sobrevive aunque la subasta suelte el pedido.
            "auction_origin_id": self.id,
            "warehouse_id": warehouse.id if warehouse else False,
            # Pago en línea obligatorio por el total: habilita el botón de pago.
            "require_payment": True,
            "prepayment_percent": 1.0,
            "require_signature": False,
            # Términos de subasta en el pedido (portal, PDF y correo de confirmación).
            "note": self._auction_order_note(),
            # El presupuesto no puede vencer antes que el plazo de pago.
            "validity_date": (
                fields.Datetime.now()
                + timedelta(hours=max(self.payment_deadline_hours or 0, MIN_PAYMENT_HOURS)
                            + PENDING_GRACE_HOURS + 24)
            ).date(),
            "order_line": [
                (0, 0, {
                    "product_id": variant.id,
                    "product_uom_qty": 1,
                    "price_unit": net,
                    "tax_ids": [(6, 0, taxes.ids)],
                    "name": _("Adjudicación subasta: %s") % self.product_id.name,
                })
            ],
        }
        # Venta única, NO suscripción: sin plantilla de presupuesto (la plantilla
        # por defecto de la compañía trae un plan recurrente) y sin plan recurrente.
        if "sale_order_template_id" in SaleOrder._fields:
            vals["sale_order_template_id"] = False
        if "plan_id" in SaleOrder._fields:
            vals["plan_id"] = False
        # Numeración propia de subastas (secuencia auction.order, prefijo LIQSUB-).
        # Si la compañía no la tiene, Odoo usa su numeración de ventas habitual.
        seq_name = self.env["ir.sequence"].with_company(company).next_by_code("auction.order")
        if seq_name:
            vals["name"] = seq_name
        order = SaleOrder.create(vals)
        # NO se confirma aquí: un pedido confirmado (state 'sale') no muestra
        # el botón de pago en el portal. Se marca como enviado y se confirma
        # automáticamente cuando Mercado Pago aprueba el pago.
        order.write({"state": "sent"})
        order._portal_ensure_token()     # asegura el token del enlace de portal
        return order

    def _auction_order_note(self):
        """Términos y condiciones que acompañan el pedido del ganador."""
        url = self.get_base_url() + "/auctions/terminos"
        return Markup(
            "<p><strong>Términos y condiciones de subastas OulaLab</strong>: "
            "<a href='%(url)s'>%(url)s</a></p>"
            "<p>Producto usado, proveniente del servicio de arriendo de OulaLab, "
            "vendido en el estado informado en la subasta (art. 14, Ley 19.496). "
            "Precio con IVA incluido. Tienes derecho a retracto dentro de 10 días "
            "desde que recibes la prenda, devolviéndola en el mismo estado en que "
            "la recibiste. Complementan los Términos y condiciones de uso de OulaLab "
            "(<a href='%(base)s/terms'>%(base)s/terms</a>). Consultas y reclamos: "
            "contactotyc@oulalab.com.</p>"
        ) % {"url": url, "base": self.get_base_url()}

    # ------------------------------------------------------------------
    # Pago / reasignación
    # ------------------------------------------------------------------
    def _is_current_order_paid(self):
        """Pagado = transacción aprobada, o pedido ya confirmado.

        Un pedido confirmado a mano (p. ej. pago por transferencia) cuenta como
        pagado: el cron nunca debe cancelar una venta ya confirmada.
        """
        self.ensure_one()
        order = self.sale_order_id
        if not order:
            return False
        if order.state == "sale":
            return True
        return any(
            t.state in ("done", "authorized") for t in order.transaction_ids
        )

    def _has_pending_online_payment(self):
        """Pago en línea iniciado y aún sin respuesta (no cuenta transferencias)."""
        self.ensure_one()
        order = self.sale_order_id
        return bool(order) and any(
            t.state == "pending" and t.provider_id.code != "custom"
            for t in order.transaction_ids
        )

    def _mark_paid(self):
        self.ensure_one()
        # Respaldo: si el pago llegó pero el pedido sigue como presupuesto
        # (p. ej. falló la confirmación automática), se confirma aquí.
        order = self.sale_order_id
        if order and order.state in ("draft", "sent"):
            order.with_context(auction_skip_sync=True).action_confirm()
        if self.current_winner_bid_id:
            self.current_winner_bid_id.rejected = False
        self.write({"state": "sold"})
        self._notify_losers()

    def _handle_non_payment(self):
        """El ganador no pagó a tiempo: descarta su oferta, cancela su pedido y reasigna."""
        self.ensure_one()
        # Última verificación: si el pedido ya está confirmado o pagado, es venta.
        if self._is_current_order_paid():
            self._mark_paid()
            return
        bid = self.current_winner_bid_id
        order = self.sale_order_id
        if bid:
            bid.rejected = True
        if order:
            order._action_cancel()
            self.sale_order_id = False
        self.message_post(body=_(
            "%(partner)s no pagó dentro del plazo (oferta $%(amount)s, pedido %(order)s "
            "cancelado). Reasignando al siguiente postor."
        ) % {
            "partner": bid.partner_id.display_name if bid else "-",
            "amount": "{:,.0f}".format(bid.amount).replace(",", ".") if bid else "0",
            "order": order.name if order else "-",
        })
        self._award_to_next_bidder()

    def _restore_award_from_order(self, order):
        """Pedido confirmado DESPUÉS de que la subasta quedó desierta por no pago.

        Restituye la adjudicación si la subasta sigue libre y la puja del cliente
        existe. Si la prenda ya se reasignó a otro postor, no toca nada y avisa.
        """
        self.ensure_one()
        if self.state == "sold" and self.sale_order_id == order:
            return
        bid = self.bid_ids.filtered(
            lambda b: b.partner_id == order.partner_id
        ).sorted(lambda b: (b.amount, b.id), reverse=True)[:1]
        if self.state == "unsold" and not self.sale_order_id and bid:
            bid.rejected = False
            self.write({
                "state": "sold",
                "sale_order_id": order.id,
                "winner_id": order.partner_id.id,
                "current_winner_bid_id": bid.id,
            })
            self.message_post(body=_(
                "Pedido %s confirmado después del vencimiento: se restituye la adjudicación."
            ) % order.name)
            return
        warning = _(
            "Atención: el pedido %(order)s se confirmó, pero la subasta %(auction)s está "
            "en estado '%(state)s' con pedido %(current)s. Revisar a mano: posible doble venta."
        ) % {
            "order": order.name,
            "auction": self.display_name,
            "state": dict(self._fields["state"].selection).get(self.state),
            "current": self.sale_order_id.name or "-",
        }
        self.message_post(body=warning)
        order.message_post(body=warning)
        _logger.warning(warning)

    # ------------------------------------------------------------------
    # Emails
    # ------------------------------------------------------------------
    def _send_payment_reminder(self):
        """Recordatorio único al ganador, unas horas antes del vencimiento."""
        self.ensure_one()
        template = self.env.ref(
            "oulalab_auction.mail_template_auction_payment_reminder", raise_if_not_found=False
        )
        if template and self.sale_order_id:
            template.send_mail(self.sale_order_id.id, force_send=True)
            self.message_post(body=_("Recordatorio de pago enviado a %s.")
                              % self.winner_id.display_name)
        self.payment_reminder_sent = True

    def _send_winner_email(self):
        """Confirmación de la orden al ganador (plantilla sobre sale.order)."""
        self.ensure_one()
        template = self.env.ref(
            "oulalab_auction.mail_template_auction_winner_order", raise_if_not_found=False
        )
        if not (template and self.sale_order_id):
            return
        # Adjunta el comprobante de subasta (informe propio), no el documento de
        # pedido de venta, que el negocio usa para las suscripciones de arriendo.
        attachment_ids = []
        report = self.env.ref(
            "oulalab_auction.action_report_auction_receipt", raise_if_not_found=False
        )
        if report:
            try:
                pdf, _ = report.sudo()._render_qweb_pdf(
                    "oulalab_auction.report_auction_receipt", res_ids=self.ids
                )
                name = "Comprobante %s.pdf" % (self.sale_order_id.name or self.name)
                attachment = self.env["ir.attachment"].sudo().create({
                    "name": name,
                    "type": "binary",
                    "datas": base64.b64encode(pdf),
                    "res_model": "liquidation.auction",
                    "res_id": self.id,
                    "mimetype": "application/pdf",
                })
                attachment_ids.append(attachment.id)
            except Exception:
                _logger.exception("No se pudo generar el comprobante de la subasta %s", self.id)
        template.send_mail(
            self.sale_order_id.id, force_send=True,
            email_values={"attachment_ids": [(6, 0, attachment_ids)]} if attachment_ids else None,
        )

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
