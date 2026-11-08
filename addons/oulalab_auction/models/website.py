from odoo import api, fields, models


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

    @api.model
    def _oulalab_ensure_liquidation_menus(self):
        """Deja en el menú de cada sitio las dos secciones de liquidación:
        Subastas (/auctions) y Prendas en venta (/prendas). Si ya existen, no las toca."""
        Menu = self.env["website.menu"].sudo()
        wanted = [("/auctions", "Subastas", 40), ("/prendas", "Prendas en venta", 41)]
        for website in self.sudo().search([]):
            root = website.menu_id
            if not root:
                continue
            existing = set(Menu.search([("website_id", "=", website.id)]).mapped("url"))
            for url, name, seq in wanted:
                if url not in existing:
                    Menu.create({"name": name, "url": url, "parent_id": root.id,
                                 "website_id": website.id, "sequence": seq})

    def shop_featured(self, limit=4):
        """Prendas en venta para la portada (las más recientes)."""
        return self.env["liquidation.shop.item"].sudo().search(
            [("state", "=", "published")], order="published_date desc", limit=limit)
