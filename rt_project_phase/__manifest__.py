# -*- coding: utf-8 -*-
{
    'name': "Rt Project Phase",

    'summary': "Rt Project Phrase for get milestones in some form views",

    'description': """
        Rt Project Phrase for get milestones in some form views /n
        like Accounting account.move.line form , Inventory stock.move form, /n
        purchase.order.line form and sale.order.line for and project task form as per business needs 
    """,

    'author': "Rightechs Solutions",
    'website': "https://www.rightechs.net",

    'category': 'Project',
    'version': '1.0',

    'depends': [
        'base', 'project',
        'account', 'stock', 'sale_timesheet',
        'sale', 'sale_project', 'timesheet_grid',
        'purchase', 'account_accountant'],

    'data': [
        'security/ir.model.access.csv',
        'data/project_phase_sequence_data.xml',
        'views/project_phase_views.xml',
        'views/project_milestone_view.xml',
        'views/project_task_view.xml',
        'views/account_move_view.xml',
        'views/stock_move_view.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/project_project_view.xml',
        'views/account_banck_statement_line_view.xml',
    ],
}

