{
    'name': 'Car Store',
    'version': '19.0.2.0.0',
    'license': 'LGPL-3',
    'author': 'darshaka',
    'category': 'Website',
    'depends': ['base', 'website', 'website_sale'],
    'description': "Custom Product Page",
    'data': [
        'views/ssr_inventory.xml',
        'views/ssr_product.xml',
        'views/payment_view.xml'
    ],
    'sequence': 20,
    'application': True,
    'auto_install': False,
}
