# -*- coding: utf-8 -*-
{
    'name': "RT Budget",

    'summary': "RT Budget",

    'description': """
        RT Budget
    """,

    'author': "Rightechs Solutions",
    'website': "https://rightechs.net/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'hr','analytic'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/project.xml',
        'views/hr_department.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
}
