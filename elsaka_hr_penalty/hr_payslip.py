# import datetime
from odoo import api, fields, models, _, Command
from datetime import datetime
import time
from odoo import tools


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    # @api.one
    @api.depends('employee_id')
    def _set_department_id(self):
        for payslip in self:
            if payslip.employee_id:
                payslip.department_id = payslip.employee_id.department_id

    department_id = fields.Many2one(string='Department', comodel_name='hr.department',
                                    store=True, compute='_set_department_id')

    @api.model
    def create(self, vals_list):
        res = super(hr_payslip, self).create(vals_list)
        print('res')
        return res

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        res = super()._compute_input_line_ids()
        for slip in self:
            print(f'input_line_ids ========= {slip.input_line_ids}')
            codes = ['ABSENT', 'UNPAID', 'LATESIGNIN', 'LATESIGNOUT', 'CLD', 'LDA', 'CRD', 'RDA',
                     'CATD', 'ATDA', 'TARGETDEDUCTION']
            lines_to_remove = slip.input_line_ids.filtered(
                lambda x: x.code in codes)
            slip.update({'input_line_ids': [Command.unlink(line.id) for line in lines_to_remove]})

            if slip.employee_id and slip.struct_id:
                input_line_ids = self.get_input_lines()
                if input_line_ids:
                    slip.update({'input_line_ids': input_line_ids})
                print(f'slip.input_line_ids =========== {slip.input_line_ids}')

        return res

    def get_input_lines(self):
        input_ids = [(5, 0, 0)]
        codes = ['ABSENT', 'UNPAID', 'LATESIGNIN', 'LATESIGNOUT', 'CLD', 'LDA', 'CRD', 'RDA',
                 'CATD', 'ATDA', 'TARGETDEDUCTION']
        input_line = self.env['hr.payslip.input.type'].search([('code', 'in', codes)])
        print('inpute_line ============= ', input_line)
        late_signin = 0.0
        late_signout = 0.0
        unpaid_leaves = 0.0
        absents = 0.0
        amount = 0.0
        target_deduction = 0.0
        employee_delay_line_pool = self.env['employee.delay.line']
        for payslip in self:
            employee_delay_line_ids = employee_delay_line_pool.search([
                ('employee_delay_id.employee_id', '=', payslip.employee_id.id),
                ('employee_delay_id.date_from', '>=', payslip.date_from),
                ('employee_delay_id.date_to', '<=', payslip.date_to),
                ('employee_delay_id.state', '=', 'approved'),
                ('waive', '=', False)])
            print('employee_delay_line_ids ', employee_delay_line_ids)

            total_leave_days_amount = 0.0
            count_leaves_days = 0.0

            total_rest_days_amount = 0.0
            count_rest_days = 0.0

            total_attendance_days_amount = 0.0
            count_attendance_days = 0.0
            if employee_delay_line_ids:
                total_leave_days_amount = employee_delay_line_ids[0].employee_delay_id.total_leaves_amount
                count_leaves_days = employee_delay_line_ids[0].employee_delay_id.count_leaves_days
                total_rest_days_amount = employee_delay_line_ids[0].employee_delay_id.total_rest_days_amount
                count_rest_days = employee_delay_line_ids[0].employee_delay_id.count_rest_days
                total_attendance_days_amount = employee_delay_line_ids[0].employee_delay_id.total_attendance_days_amount
                count_attendance_days = employee_delay_line_ids[0].employee_delay_id.count_attendance_days
            print(f'total_leave_days_amount ===== {total_leave_days_amount}')
            print(f'count_leaves_days ===== {count_leaves_days}')
            for edl in employee_delay_line_ids:
                if edl.type in ['late_signin', 'no_signin']:
                    late_signin += edl.deduction
                if edl.type in ['late_signout', 'no_signout']:
                    late_signout += edl.deduction
                if edl.type in ['unpaid_leave', 'leaves'] and edl.deduction:
                    unpaid_leaves += edl.deduction
                if edl.type in ['absent']:
                    absents += edl.deduction
                if edl.type in ['late_signin', 'late_signout']:
                    target_deduction += edl.deduction

            # mod = self.env['ir.model.data']
            input_line_ids = []
            for line in input_line:
                vals = {
                    'input_type_id': line.id,
                    'name': line.name,
                }
                if line.code == 'ABSENT':
                    vals['amount'] = absents
                elif line.code == 'UNPAID':
                    # line.amount = unpaid_leaves
                    vals['amount'] = unpaid_leaves
                elif line.code == 'LATESIGNIN':
                    # line.amount = late_signin
                    vals['amount'] = late_signin
                elif line.code == 'LATESIGNOUT':
                    # line.amount = late_signout
                    vals['amount'] = late_signout

                elif line.code == 'CLD':
                    # line.amount = count_leaves_days
                    vals['amount'] = count_leaves_days

                elif line.code == 'LDA':
                    # line.amount = total_leave_days_amount
                    vals['amount'] = total_leave_days_amount

                elif line.code == 'CRD':
                    # line.amount = count_rest_days
                    vals['amount'] = count_rest_days

                elif line.code == 'RDA':
                    # line.amount = total_rest_days_amount
                    vals['amount'] = total_rest_days_amount

                elif line.code == 'CATD':
                    # line.amount = count_attendance_days
                    vals['amount'] = count_attendance_days

                elif line.code == 'ATDA':
                    # line.amount = total_attendance_days_amount
                    vals['amount'] = total_attendance_days_amount
                print(f'vals =========== {vals}')
                input_line_ids.append((0, 0, vals))
            return input_line_ids
