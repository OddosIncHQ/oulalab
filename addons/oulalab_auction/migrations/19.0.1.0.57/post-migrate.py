"""v57: vínculo permanente pedido -> subasta y plazo mínimo de pago."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # 1) Pedidos que hoy están vinculados a su subasta.
    cr.execute("""
        UPDATE sale_order so
           SET auction_origin_id = a.id
          FROM liquidation_auction a
         WHERE a.sale_order_id = so.id
           AND so.auction_origin_id IS NULL
    """)
    linked = cr.rowcount
    # 2) Pedidos desvinculados por no pago: por origen, solo si el nombre de la
    #    subasta es único (hay subastas con nombres repetidos).
    cr.execute("""
        UPDATE sale_order so
           SET auction_origin_id = a.id
          FROM liquidation_auction a
         WHERE so.auction_origin_id IS NULL
           AND so.origin = a.name
           AND (SELECT count(*) FROM liquidation_auction a2 WHERE a2.name = a.name) = 1
    """)
    by_origin = cr.rowcount
    # 3) Plazo mínimo de 24 h en subastas que aún no cierran.
    cr.execute("""
        UPDATE liquidation_auction
           SET payment_deadline_hours = 24
         WHERE coalesce(payment_deadline_hours, 0) < 24
           AND state IN ('draft', 'published', 'live')
    """)
    _logger.info("oulalab_auction v57: %s pedidos vinculados, %s por origen, %s plazos a 24 h",
                 linked, by_origin, cr.rowcount)
