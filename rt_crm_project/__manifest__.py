# -*- coding: utf-8 -*-
{
    'name': "RT crm project",

    'summary': "RT crm project",

    'description': """
        RT crm project
    """,

    'author': "Rightechs Solutions",
    'website': "https://rightechs.net/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale_crm', 'sale', 'sale_management', 'rt_project_purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/views.xml',
        # 'views/service.xml',
        # 'views/project_project.xml',
        # 'data/pdd_sequence.xml',
    ],
}
