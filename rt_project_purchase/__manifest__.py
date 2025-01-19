# -*- coding: utf-8 -*-
{
    'name': "Rt Project Purchase",

    'summary': """Rt PRoject Purchase is a module to chooose the project \n
                from the purchase form view when creating the purchase order """,

    'description': """Rt PRoject Purchase is a module to chooose the project \n
                from the purchase form view when creating the purchase order """,

        'author': "Rightechs Solutions",
        'website': "https://www.rightechs.net",

        # for the full list
        'category': 'Project',
        'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase', 'sale', 'sale_project', 'project','sale_purchase_inter_company_rules'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
    ],
}

