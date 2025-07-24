# -*- coding: utf-8 -*-
{
    'name': 'Arriendos por Suscripción',
    'version': '1.3.0',
    'summary': 'Aplicación para la gestión integral del modelo de arriendo de prendas.',
    'author': 'Tu Nombre/Empresa',
    'category': 'Sales/Subscription',
    'depends': [
        'sale_subscription',
        'stock',
        'product',
        'website',
        'portal',
    ],
    'data': [
        # 1. Seguridad (SIEMPRE PRIMERO)
        'security/security.xml',
        'security/ir.model.access.csv',

        # 2. Datos
        'data/cron_jobs.xml',
        
        # 3. Vistas que definen acciones y componentes base
        'views/arriendo_prenda_linea_views.xml',
        'views/suscripcion_views.xml',
        'views/stock_picking_views.xml',
        'views/product_views.xml',
        
        # 4. Menús (que utilizan las acciones definidas en los archivos de arriba)
        'views/menu_views.xml',
        
        # 5. Plantillas del Portal
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
