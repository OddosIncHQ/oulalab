{
    'name': 'Arriendo de Prendas por Suscripción',
    'version': '1.0.1',
    'summary': 'Gestión de arriendo de prendas bajo modelo de suscripción',
    'description': """
        Este módulo permite ofrecer productos (prendas) en modalidad de arriendo mediante suscripciones periódicas.
        Integra gestión de productos, stock, suscripciones y un portal web para clientes.
        La tienda en línea (`website_sale`) ha sido adaptada para soportar el modelo de arriendo en lugar de venta directa.
    """,
    'author': 'Tu Nombre o Empresa',
    'website': 'https://www.tusitio.com',
    'category': 'Sales/Subscription',
    'depends': [
        'base',
        'sale_subscription',
        'stock',
        'product',
        'website',
        'portal',
        'website_sale',
    ],
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
        'web.assets_frontend': [
            'arriendo_prendas_suscripcion/static/src/css/arriendo_styles.css',
            'arriendo_prendas_suscripcion/static/src/js/arriendo_scripts.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',  # ← Agregado aquí
}
