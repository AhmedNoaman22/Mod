# -*- coding: utf-8 -*-
{
    'name': "rt_timesheet_overtime",

    'summary': "rt_timesheet_overtime module for overtime",

    'description': """
Long description of module's purpose
    """,

    'author': "Rightechs Solutions",
    'website': "https://www.rightechs.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr', 'analytic', 'hr_timesheet', 'timesheet_grid', 'hr_hourly_cost', 'rt_buget_phase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_time_views.xml'
        '',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode

    'demo': [
        'demo/demo.xml',
    ],
}

