# -*- coding: utf-8 -*-
{
    'name': "RT Timesheet Grid Inactive",
    'summary': "RT Timesheet Grid Inactive",
    'description': """
        RT Timesheet Grid Inactive
    """,
    'author': "Rightechs Solutions",
    'website': "https://rightechs.net/",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base'],
    'assets': {
        'web.assets_backend': [
            'rt_timesheet_grid_inactive/static/src/css/style.scss',  # Include SCSS
        ],
    },

    'data': [
        # 'views/views.xml',
        # 'views/templates.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],
}
