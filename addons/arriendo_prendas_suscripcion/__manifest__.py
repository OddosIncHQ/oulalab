# -*- coding: utf-8 -*-
{
    'name': 'Arriendo de Prendas por Suscripción',
    'version': '1.0',
    'summary': 'Gestión de arriendo de prendas bajo modelo de suscripción',
    'description': """
        Módulo para la administración de arriendo de prendas mediante suscripciones.
        Incluye gestión de productos, stock, suscripciones, portal para clientes y vistas personalizadas.
    """,
    'author': 'Tu Nombre o Empresa',
    'website': 'https://tusitio.com',
    'category': 'Sales/Subscription',
    'depends': ['base', 'product', 'stock', 'sale', 'website', 'portal', 'sale_subscription'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/suscripcion_views.xml',
        'views/arriendo_prenda_linea_views.xml',
        'views/stock_picking_views.xml',
        'views/product_views.xml',
        'data/cron_jobs.xml',
        'templates/portal_template.xml',
        'templates/catalogo_arriendo_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'arriendo_prendas_suscripcion/static/src/css/arriendo_styles.css',
            'arriendo_prendas_suscripcion/static/src/js/arriendo_scripts.js',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
