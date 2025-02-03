# -*- coding: utf-8 -*-
{
    'name': "RT task department budget",

    'summary': "RT task department budget",

    'description': """
        RT task department budget
    """,

    'author': "Rightechs Solutions",
    'website': "https://www.rightechs.net",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/employee_task.xml',
        'views/hr_department.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
