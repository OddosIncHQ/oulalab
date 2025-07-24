{
    'name': 'Arriendos por Suscripción', # Nombre de la App
    'version': '1.2.0',
    'summary': 'Aplicación para la gestión integral del modelo de arriendo de prendas.',
    'description': """
        Una aplicación completa para centralizar todas las operaciones de un negocio
        de arriendo de prendas por suscripción.
    """,
    'author': 'Tu Nombre/Empresa',
    'website': 'https://www.tusitio.com',
    'category': 'Sales/Subscription',
    'depends': [
        'sale_subscription',
        'stock',
        'product',
        'website',
        'portal',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_jobs.xml',
        
        # Vistas del Backend (el orden importa)
        'views/menu_views.xml', # ¡NUEVO! Este archivo centralizará los menús.
        'views/product_views.xml',
        'views/suscripcion_views.xml',
        'views/stock_picking_views.xml',
        'views/arriendo_prenda_linea_views.xml',
        
        # Plantillas del Frontend (Portal)
        'templates/portal_template.xml',
        'templates/catalogo_arriendo_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'arriendo_prendas_suscripcion/static/src/css/arriendo_styles.css',
            'arriendo_prendas_suscripcion/static/src/js/arriendo_scripts.js',
        ],
    },
    'application': True, # ¡Esta es la clave! Le dice a Odoo que es una app.
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'web_icon': 'arriendo_prendas_suscripcion,static/description/icon.png', # Asegura que el ícono se muestre
}
