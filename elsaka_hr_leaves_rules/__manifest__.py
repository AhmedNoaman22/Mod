# -*- coding: utf-8 -*-

{
    'name': 'Elsaka Leave Rule Features',
    'category': 'Human Resources',
    'description': """
    """,
    'author': 'Rightechs Solution',
    'website': 'rightechs.net',
    'depends': ['base', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_holidays_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'price': 100.00,
    'currency': 'EUR',
    'licence': 'Affero GPL-3',
}
