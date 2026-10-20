import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    @api.model
    def _oulalab_bind_home_override(self):
        """Engancha la portada de subastas a la vista que el sitio dibuja de verdad.

        El identificador del módulo es `website.homepage`, pero el sitio de
        Oulalab Chile usa una vista propia con la clave `website.home`. Sin este
        ajuste la portada no se aplica, y hacerlo a mano en la base se pierde en
        cada actualización del módulo, que reinstala la vista desde el código.
        """
        override = self.env.ref(
            "oulalab_auction.website_homepage_auctions", raise_if_not_found=False
        )
        if not override:
            return

        # Portada realmente usada por cada sitio: su propia vista `website.home`.
        homes = self.search([("key", "=", "website.home"), ("website_id", "!=", False)])
        target = homes.filtered(lambda v: v.website_id.domain)[:1] or homes[:1]
        if not target:
            # Sin vista propia, la herencia por defecto del módulo ya sirve.
            return

        if override.inherit_id != target or not override.active:
            override.write({"inherit_id": target.id, "active": True})
            _logger.info(
                "oulalab_auction: portada enganchada a la vista %s (sitio %s)",
                target.id,
                target.website_id.name,
            )
