{
    'name': 'Arriendos por Suscripción',
    'version': '1.2.1',
    'summary': 'Aplicación para la gestión integral del modelo de arriendo de prendas.',
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
        # 1. Seguridad (SIEMPRE PRIMERO)
        'security/security.xml',
        'security/ir.model.access.csv',

        # 2. Datos (como cron jobs)
        'data/cron_jobs.xml',
        
        # 3. Vistas del Backend y Menús
        # El archivo de menús debe ir primero para que las demás vistas se "ancoren" a él.
        'views/menu_views.xml',
        'views/arriendo_prenda_linea_views.xml',
        'views/suscripcion_views.xml',
        'views/stock_picking_views.xml',
        'views/product_views.xml',
        
        # 4. Plantillas del Frontend (Portal)
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
}
