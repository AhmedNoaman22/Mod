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
    'name': 'Elsaka HR Penalty KSA',
    'version': '17.0',
    'category': 'Human Resources',
    'description': """ Human Resources for penalty on employee
    """,
    'author': 'Ahmed Elsaka',
    'website': 'https://www.elsaka.com',
    'depends': ['hr_attendance', 'hr', 'hr_contract', 'elsaka_hr_contract', 'elsaka_hr_shifts', 'elsaka_hr_leaves',
                'hr_payroll','hr_attendance','hr_timesheet', 'hr_payroll'],
    'data': [
        'hr_penalty_view.xml',
        'data.xml',
		'wizard/batch_deduction_view.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'data/salary_rule_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
