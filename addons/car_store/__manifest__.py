{
    'name': 'Car Store',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'darshaka',
    'category': 'Website',
    'depends': ['base','website'],
    'description': "First web page",
    'data': [
        'views/main.xml',
        'views/hello_world.xml',
        'views/inventory.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'car_store/static/src/js/main.js',
            'car_store/static/src/js/components/product_inventory.js',
        ],
    },
    'sequence': 20,
    'application': True,
    'auto_install': False,
}