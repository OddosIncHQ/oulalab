"""v58: canal de liquidación en pedidos y código de la prenda en el nombre de la subasta."""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE sale_order
           SET liquidation_channel = 'auction'
         WHERE auction_origin_id IS NOT NULL
           AND liquidation_channel IS NULL
    """)
    orders = cr.rowcount

    env = api.Environment(cr, SUPERUSER_ID, {})
    auctions = env["liquidation.auction"].with_context(active_test=False).search([])
    env.add_to_compute(auctions._fields["name"], auctions)
    env.flush_all()
    _logger.info("oulalab_auction v58: %s pedidos marcados como subasta, %s subastas renombradas",
                 orders, len(auctions))
