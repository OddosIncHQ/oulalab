import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Comunas a las que OulaLab despacha. Para habilitar otra, agrégala aquí.
AUCTION_COMMUNES = [
    ("lo_barnechea", "Lo Barnechea"),
    ("las_condes", "Las Condes"),
    ("vitacura", "Vitacura"),
]


def validate_rut(rut):
    """Valida un RUT chileno (formato + dígito verificador, módulo 11).
    Devuelve el RUT normalizado 'cuerpo-DV' si es válido, o None."""
    if not rut:
        return None
    clean = rut.replace(".", "").replace("-", "").replace(" ", "").upper()
    if len(clean) < 2 or not clean[:-1].isdigit():
        return None
    body, dv = clean[:-1], clean[-1]
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    rest = 11 - (total % 11)
    expected = "0" if rest == 11 else "K" if rest == 10 else str(rest)
    return "%s-%s" % (body, dv) if expected == dv else None


class ResPartner(models.Model):
    _inherit = "res.partner"

    auction_delivery_mode = fields.Selection(
        [("pickup", "Retiro en showroom"), ("delivery", "Despacho a domicilio")],
        string="Entrega (subastas)",
        help="Cómo recibe el adjudicatario la prenda ganada en subasta.",
    )
    auction_commune = fields.Selection(
        AUCTION_COMMUNES,
        string="Comuna de despacho",
        help="Solo se despacha a estas comunas; fuera de ellas, retiro en showroom.",
    )

    def _auction_delivery_ready(self):
        """¿El postor completó RUT + una modalidad de entrega válida para pujar?"""
        self.ensure_one()
        if not self.vat:  # RUT obligatorio para todo pujador
            return False
        if self.auction_delivery_mode == "pickup":
            return True
        if self.auction_delivery_mode == "delivery":
            return bool(self.auction_commune and self.street)
        return False

    @api.model
    def _auction_verify_address(self, street, commune_label):
        """Corrobora una dirección con Google Geocoding.
        Devuelve (ok, motivo). Si no hay API key configurada, no bloquea."""
        key = self.env["ir.config_parameter"].sudo().get_param(
            "oulalab_auction.google_maps_api_key"
        )
        if not key:
            return True, None  # sin key: se acepta sin corroborar
        address = "%s, %s, Chile" % (street, commune_label)
        try:
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": key, "region": "cl"},
                timeout=5,
            )
            data = resp.json()
        except Exception as e:  # red/timeout: no bloquear la puja
            _logger.warning("Geocoding OulaLab falló: %s", e)
            return True, None
        if data.get("status") != "OK" or not data.get("results"):
            return False, "No pudimos encontrar esa dirección. Revísala."
        formatted = data["results"][0].get("formatted_address", "").lower()
        if commune_label.lower() not in formatted:
            return False, (
                "La dirección no parece estar en %s. "
                "Verifícala o elige retiro en showroom." % commune_label
            )
        return True, None

    is_oulalab_member = fields.Boolean(
        string="Socio OulaLab",
        compute="_compute_is_oulalab_member",
        store=True,
        readonly=False,
        help="Suscriptor con plan de alquiler ACTIVO. Recibe acceso anticipado "
        "(preview) y menor incremento mínimo de puja. Se calcula solo, pero "
        "puedes forzarlo a mano.",
    )
    auction_source = fields.Selection(
        [("portal", "Cuenta en Odoo"), ("guest", "Dejó sus datos (sin cuenta)")],
        string="Origen en subastas",
        compute="_compute_auction_source",
        store=True,
        help="Cómo llegó el postor: con cuenta de portal en Odoo o dejando sus datos.",
    )

    def _member_depends(self):
        # Solo depende de subscription_state si el módulo de suscripciones
        # (sale_subscription) está instalado; si no, ese campo no existe y
        # Odoo rechaza el @depends al cargar/actualizar el módulo.
        deps = ["sale_order_ids.state"]
        if "subscription_state" in self.env["sale.order"]._fields:
            deps.append("sale_order_ids.subscription_state")
        return deps

    @api.depends(lambda self: self._member_depends())
    def _compute_is_oulalab_member(self):
        # Socio = tiene una suscripción de alquiler ACTIVA.
        # En Odoo 19 la suscripción activa es subscription_state == '3_progress'.
        # Ajusta aquí si tu operación usa otro criterio de "plan activo".
        for partner in self:
            partner.is_oulalab_member = any(
                getattr(o, "subscription_state", False) == "3_progress"
                for o in partner.sale_order_ids
            )

    @api.depends("user_ids")
    def _compute_auction_source(self):
        for partner in self:
            partner.auction_source = "portal" if partner.user_ids else "guest"

    auction_bid_ids = fields.One2many(
        "auction.bid", "partner_id", string="Pujas en subastas"
    )
    auction_bid_count = fields.Integer(
        string="N.º de pujas", compute="_compute_auction_bid_count"
    )

    def _compute_auction_bid_count(self):
        for partner in self:
            partner.auction_bid_count = len(partner.auction_bid_ids)
