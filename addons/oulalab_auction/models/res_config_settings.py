from odoo import _, fields, models
from odoo.exceptions import ValidationError

from .shop_item import SHOP_DEFAULTS


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    oulabag_product_id = fields.Many2one(
        "product.product", string="Producto OulaBag",
        config_parameter="oulalab_shop.oulabag_product_id",
        help="Producto que se agrega al pedido. Vacío = el OulaBag que crea el módulo.",
    )
    oulabag_price = fields.Integer(
        string="Precio OulaBag (IVA incl.)", default=SHOP_DEFAULTS["oulabag_price"],
        config_parameter="oulalab_shop.oulabag_price",
    )
    oulabag_reference_price = fields.Integer(
        string="Precio normal de referencia", default=SHOP_DEFAULTS["oulabag_reference_price"],
        config_parameter="oulalab_shop.oulabag_reference_price",
        help="Se muestra tachado junto al precio del OulaBag.",
    )
    oulabag_floor_price = fields.Integer(
        string="Precio mínimo permitido", default=SHOP_DEFAULTS["oulabag_floor_price"],
        config_parameter="oulalab_shop.oulabag_floor_price",
        help="Piso del precio del OulaBag: costo puesto en Chile más IVA. "
        "No se puede guardar un precio menor.",
    )
    oulabag_min_cart = fields.Integer(
        string="Compra mínima para ofrecerlo", default=SHOP_DEFAULTS["oulabag_min_cart"],
        config_parameter="oulalab_shop.oulabag_min_cart",
        help="Total en prendas (IVA incl.) desde el cual el checkout ofrece el OulaBag.",
    )
    shop_reservation_minutes = fields.Integer(
        string="Reserva para pagar (minutos)", default=SHOP_DEFAULTS["reservation_minutes"],
        config_parameter="oulalab_shop.reservation_minutes",
    )
    shop_pending_grace_minutes = fields.Integer(
        string="Margen si el pago está pendiente (minutos)",
        default=SHOP_DEFAULTS["pending_grace_minutes"],
        config_parameter="oulalab_shop.pending_grace_minutes",
    )
    shop_shipping_fee = fields.Integer(
        string="Costo de despacho (IVA incl.)", default=SHOP_DEFAULTS["shipping_fee"],
        config_parameter="oulalab_shop.shipping_fee",
        help="0 = despacho gratis en las comunas habilitadas.",
    )
    liquidation_customer_location_id = fields.Many2one(
        "stock.location", string="Ubicación de clientes (liquidación)",
        domain=[("usage", "=", "customer")],
        config_parameter="oulalab_shop.customer_location_id",
        help="Destino de las entregas de subastas y ventas directas. Vacío = el destino "
        "de la regla de entrega a clientes del almacén del pedido.",
    )

    def set_values(self):
        for rec in self:
            if rec.oulabag_price < rec.oulabag_floor_price:
                raise ValidationError(_(
                    "El precio del OulaBag ($%(p)s) no puede ser menor que el precio mínimo "
                    "permitido ($%(f)s)."
                ) % {"p": "{:,}".format(rec.oulabag_price).replace(",", "."),
                     "f": "{:,}".format(rec.oulabag_floor_price).replace(",", ".")})
            if rec.oulabag_min_cart < 0 or rec.shop_reservation_minutes < 15:
                raise ValidationError(_(
                    "Revisa la configuración: la compra mínima no puede ser negativa y la "
                    "reserva para pagar debe ser de al menos 15 minutos."))
        return super().set_values()
