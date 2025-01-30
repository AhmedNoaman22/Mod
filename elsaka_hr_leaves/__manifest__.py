# -*- coding: utf-8 -*-
{
    'name': 'Elsaka Leave Extension',
    'category': 'Human Resources',
    'description': """
    """,
    'author': 'Rightechs Solution',
    'website': 'rightechs.net',
    'depends': ['base', 'hr_holidays', 'mail', 'analytic','elsaka_hr_leaves_rules'],
    'data': [
        'data/hr_holidays_data.xml',
        'views/hr_holidays_view.xml',
		'wizard/update_company_view.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'price': 240.00,
    'currency': 'EUR',
    'licence': 'Affero GPL-3',
}
