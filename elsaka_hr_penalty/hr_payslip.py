# import datetime
from odoo import api, fields, models, _, Command
from collections import defaultdict
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import pytz
from odoo import tools
from odoo.exceptions import UserError


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

    def compute_sheet(self):
        res = super().compute_sheet()
        self._compute_input_line_ids()
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
        late_deduction = 0.0
        target_deduction = 0.0
        employee_delay_line_pool = self.env['employee.delay.line']
        employee_delay_pool = self.env['employee.delay']
        for payslip in self:
            employee_delay_line_ids = employee_delay_line_pool.search([
                ('employee_delay_id.employee_id', '=', payslip.employee_id.id),
                ('employee_delay_id.date_from', '>=', payslip.date_from),
                ('employee_delay_id.date_to', '<=', payslip.date_to),
                ('employee_delay_id.state', '=', 'approved'),
                ('waive', '=', False)])
            print('employee_delay_line_ids ', employee_delay_line_ids)
            employee_delay_ids = employee_delay_pool.search([
                ('employee_id', '=', payslip.employee_id.id),
                ('date_from', '>=', payslip.date_from),
                ('date_to', '<=', payslip.date_to),
                ('state', '=', 'approved')])
            print('employee_delay_ids ', employee_delay_ids)

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
            for ed in employee_delay_ids:
                target_deduction += ed.target_deduction

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
                    late_deduction += edl.deduction

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

                elif line.code == 'TARGETDEDUCTION':
                    # line.amount = count_leaves_days
                    vals['amount'] = target_deduction

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



class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'


    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime('%B %Y')
            else:
                batch_name = _('From %(from_date)s to %(end_date)s', from_date=format_date(self.env, from_date), end_date=format_date(self.env, end_date))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': batch_name,
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        #Prevent a payslip_run from having multiple payslips for the same employee
        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        if not employees:
            payslip_run.slip_ids.write({'state': 'verify'})
            payslip_run.state = 'verify'
            return success_result

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)
        contracts.generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end + relativedelta(days=1)),
            ('date_stop', '>=', payslip_run.date_start + relativedelta(days=-1)),
            ('employee_id', 'in', employees.ids),
        ])
        for slip in payslip_run.slip_ids:
            slip_tz = pytz.timezone(slip.contract_id.resource_calendar_id.tz)
            utc = pytz.timezone('UTC')
            date_from = slip_tz.localize(datetime.combine(slip.date_from, time.min)).astimezone(utc).replace(tzinfo=None)
            date_to = slip_tz.localize(datetime.combine(slip.date_to, time.max)).astimezone(utc).replace(tzinfo=None)
            payslip_work_entries = work_entries.filtered_domain([
                ('contract_id', '=', slip.contract_id.id),
                ('date_stop', '<=', date_to),
                ('date_start', '>=', date_from),
            ])
            payslip_work_entries._check_undefined_slots(slip.date_from, slip.date_to)


        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s (%s)" % (s[0], s[1], s[2].employee_id.name) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Some work entries could not be validated.'),
                        'message': _('Time intervals to look for:%s', time_intervals_str),
                        'sticky': False,
                    }
                }


        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []
        for contract in self._filter_contracts(contracts):
            values = dict(default_values, **{
                'name': _('New Payslip'),
                'employee_id': contract.employee_id.id,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            })
            payslips_vals.append(values)
        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips._compute_name()
        payslips.compute_sheet()
        payslips._compute_input_line_ids()
        payslips.get_input_lines()
        # print("compute sheet done")
        payslip_run.slip_ids.write({'state': 'verify'})
        payslip_run.state = 'verify'

        return success_result
