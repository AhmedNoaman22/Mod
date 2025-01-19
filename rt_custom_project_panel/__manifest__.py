# -*- coding: utf-8 -*-
{
    'name': "RT Custom Project Panel",

    'summary': "RT Custom Project Panel",

    'description': """RT Custom Project Panel""",

    'author': "Rightechs Solutions",
    'website': "https://www.rightechs.net",

    'category': 'Project',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 'project',
        'account', 'stock', 'sale_timesheet',
        'sale', 'sale_project', 'timesheet_grid',
        'purchase', 'account_accountant'],

    # always loaded
    'assets': {
        'web.assets_backend': [
            'rt_custom_project_panel/static/src/components/project_right_side_panel/**/*',
        ],
    },
    "installable": True,
}

