# -*- coding: utf-8 -*-
{
    'name': 'Custom Product Theme',
    'version': '0.1',
    'license': 'LGPL-3',
    'category': 'Theme',
    'description': """Custom Theme for Products""",
    'author': 'darshaka',
    'depends': ['website',  'website_sale'],
    'data': [
        'views/snippets/product_view_snippet.xml',
        'views/snippets/options.xml',
        'views/snippets/templates.xml',
    ],
    'sequence': 10,
    'application': False,
    'auto_install': False,
}