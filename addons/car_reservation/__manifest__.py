# -*- coding: utf-8 -*-
{
    'name': 'Car Reservation',
    'version': '1.1',
    'license': 'LGPL-3',
    'category': 'Theme',
    'description': """Custom Theme for Car Reservation""",
    'author': 'darshaka',
    'depends': ['website', 'website_sale', 'stock', 'payment', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/reservation_sequence.xml',
        'views/reserve_now_btn.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'car_reservation/static/src/js/test.js',  # <--- NEW
        ],
    },
    'sequence': 10,
    'application': True,
    'auto_install': False,
}
