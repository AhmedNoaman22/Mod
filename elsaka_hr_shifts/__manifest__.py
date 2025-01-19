# -*- coding: utf-8 -*-

{
    'name': 'Elsaka Shifts Management',
    'version': '17.0',
    'category': 'Human Resources',
    'description': """
The Human Resource Manager is asking:-
--------------------------------------
* How Can I Handle Employee’s Shifts Weekly By Using Default Odoo System?
* How Can I Define Different Weekends For Every Department Or Group Every Week or Month Or Shift?
* How Can I Define “Fixable Hours” Using Odoo System?
* How Can I Define “Break Time” For Every Shift By Default Odoo System?

Odoo Defulat Can’t Answer Above Question,
-----------------------------------------
BUT, Our “Elsaka_Shift_Managment” Can Answer It!
------------------------------------------------
    """,
    'author': "Rightechs Solution",
    'website': 'rightechs.net',
    'depends': ['base','hr', 'hr_attendance'],
    'data': [
        'data/rest_days.xml',
        'views/hr_shift_view.xml',
        'wizard/shift_excel.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'price': 110.0,
    'currency': 'EUR',
    'licence': 'Affero GPL-3',
}
