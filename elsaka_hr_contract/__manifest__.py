# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today OpenERP SA (<http://www.openerp.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Elsaka Contract Features',
    'category': 'Human Resources',
    'description': """
    """,
    'author': 'Rightechs Solution',
    'website': 'rightechs.info',
    'depends': ['base', 'hr_contract', 'hr_holidays', 'hr_payroll'],
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'view/hr_contract_view.xml',
        'data/hr_payroll_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'price': 30.00,
    'currency': 'EUR',
    'licence': 'Affero GPL-3',
}
