{
    "name": "OulaLab Auction (Liquidación de prendas)",
    "version": "19.0.1.0.0",
    "category": "Website/Website",
    "summary": "Subasta de prendas retiradas del alquiler, con preferencia para socios OulaLab.",
    "author": "OulaLab",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale_management",
        "product",
        "website",
    ],
    "data": [
        "security/auction_security.xml",
        "security/ir.model.access.csv",
        "data/auction_cron.xml",
        "views/liquidation_auction_views.xml",
        "views/auction_bid_views.xml",
        "views/auction_menus.xml",
        "templates/auction_list.xml",
        "templates/auction_detail.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "oulalab_auction/static/src/scss/auction_portal.scss",
            "oulalab_auction/static/src/js/auction_timer.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
