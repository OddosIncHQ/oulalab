# -*- coding: utf-8 -*-
{
    'name': 'Arriendos por Suscripción',
    'version': '1.3.1',
    'summary': 'Aplicación para la gestión integral del modelo de arriendo de prendas.',
    'author': 'Tu Nombre/Empresa',
    'category': 'Sales/Subscription',
    'depends': [
        'sale_subscription',
        'stock',
        'product',
        'website',
        'portal',
        'mail', # <-- DEPENDENCIA AÑADIDA
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_jobs.xml',
        'views/arriendo_prenda_linea_views.xml',
        'views/suscripcion_views.xml',
        'views/stock_picking_views.xml',
        'views/product_views.xml',
        'views/menu_views.xml',
        'templates/portal_template.xml',
        'templates/catalogo_arriendo_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'arriendo_prendas_suscripcion/static/src/css/arriendo_styles.css',
            'arriendo_prendas_suscripcion/static/src/js/arriendo_scripts.js',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'web_icon': 'arriendo_prendas_suscripcion,static/description/icon.png',
    'post_init_hook': 'post_init_hook',
}
