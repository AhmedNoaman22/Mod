# -*- coding: utf-8 -*-
{
    'name': "Rt Analytic Indirect Amount",

    'summary': "rt_analytic_indirect_amount module for indirect amount of budget",

    'description': """  
                rt_analytic_indirect_amount module for indirect amount of custom budget of total cost in every task fo budget_line
    """,

    'author': "Rightechs Solutions",
    'website': "https://www.rightechs.net",

    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'analytic', 'rt_budget', 'rt_buget_phase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/analytic_line_views.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

