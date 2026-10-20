from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    def auction_closing_soon(self, limit=3):
        """Subastas visibles con el cierre más próximo.

        Vive en el modelo y no dentro de la plantilla QWeb: en la portada no hay
        garantía de tener `request` ni `fields` en el contexto de renderizado.
        """
        return self.env["liquidation.auction"].sudo().search(
            [
                ("state", "in", ["published", "live"]),
                ("end_date", ">", fields.Datetime.now()),
            ],
            order="end_date asc",
            limit=limit,
        )
