# import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import time
import pytz
import math
from dateutil import rrule
from collections import Counter
from operator import itemgetter
from collections import OrderedDict
from datetime import date

MONTH_LIST = [('1', '1 Month'), ('2', '2 Month'), ('3', '3 Month'), ('4', '4 Month'),
              ('5', '5 Month'), ('6', '6 Month'), ('7', '7 Month'), ('8', '8 Month'),
              ('9', '9 Month'), ('10', '10 Month'), ('11', '11 Month'), ('12', '12 Month')]

def subtract_patch(start, end):
    ''' Two float number as float need to be subtracted and return float number
            as valid time float'''
    diff = 0.0
    import datetime as dt
    if start <= end:
        start = str(start)
        end = str(end)
        if len(start.split('.')[0]) == 1:
            start1 = '0' + start.split('.')[0]
        else:
            start1 = start.split('.')[0]
        if len(start.split('.')[1]) == 1:
            start2 = start.split('.')[1] + '0'
        else:
            start2 = start.split('.')[1]

        start = start1 + '.' + start2

        if len(end.split('.')[0]) == 1:
            end1 = '0' + end.split('.')[0]
        else:
            end1 = end.split('.')[0]
        if len(end.split('.')[1]) == 1:
            end2 = end.split('.')[1] + '0'
        else:
            end2 = end.split('.')[1]
        end = end1 + '.' + end2

        mins = float(end.split('.')[1]) < float(start.split('.')[1])
        hrs = float(end.split('.')[0]) - float(start.split('.')[0])
        if float(end.split('.')[1]) < float(start.split('.')[1]):
            mins = (60.0 - float(start.split('.')[1]))
            hrs -= 1.0
        else:
            mins = float(end.split('.')[1]) - float(start.split('.')[1])

        hrs = int(hrs)
        mins = int(mins)
        if len(str(hrs)) == 1:
            hrs = '0' + str(hrs)
        if len(str(mins)) == 1:
            mins = '0' + str(mins)
        diff = float(str(hrs) + '.' + str(mins))
    return diff


import logging
_logger = logging.getLogger(__name__)


class month_line(models.Model):
    _name = 'month.line'

    _rec_name = 'date_from'
    _order = 'date_from ASC'

    name = fields.Selection(MONTH_LIST, string="Month")
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    working_hours = fields.Float('Total Target Hours')
    per_hour = fields.Float('Per Hour', help="Per hour as per Gross Wages of Employee")

    contract_id = fields.Many2one('hr.contract', 'Contract')

    @api.onchange('date_from', 'date_to')
    def onchange_date(self):
        if self.date_from and self.date_to and self.date_from >= self.date_to:
            raise UserError(_('%s can not be bigger then %s.' % (self.date_to, self.date_from)))


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    special_month = fields.Boolean('Special Months')
    month_line = fields.One2many('month.line', 'contract_id', 'Month Line')
    target_dedcution_hours = fields.Integer('Target Dedcution Hours', default=lambda *a: 0)
    target_dedcution_rate = fields.Float('Target Dedcution Rate', default=lambda *a: 0)

    def calculate_working_hours(self):
        emp_delay_pool = self.env['employee.delay']
        patch_delay_cal_pool = self.env['patch.delay.cal']
        assign_shift_line_pool = self.env['assign.shift.line']
        month_line_pool = self.env['month.line']
        date_format = "%Y-%m-%d"
        for this in self:
            for month_line in this.month_line:
                date_list = emp_delay_pool.generate_date_dic(month_line.date_from, month_line.date_to, date_format)
                working_hours = 0.0
                per_hour = 0.0
                for date in date_list:

                    assign_shift_ids = patch_delay_cal_pool.get_employee_shift(this.employee_id.id, date, date)
                    if not assign_shift_ids:
                        raise UserError(_('No shifts found for employee %s.' % (this.employee_id.name)))
                    assign_shift = assign_shift_ids[0]

                    # REST DAYS TO SKIPPED
                    rest_days_list = [x.name for x in assign_shift.rest_days]
                    if datetime.strptime(str(date), date_format).strftime('%A') in rest_days_list:
                        continue

                    working_hours += assign_shift.shift_id.total_working_hours - assign_shift.shift_id.break_hours
                per_hour = this.gross and this.gross / working_hours or per_hour
                month_line.write({'working_hours': working_hours, 'per_hour': per_hour})
        return True


class hr_penalty(models.Model):
    _name = 'hr.penalty'

    name = fields.Char('Penalty Name', required=True)
    mode = fields.Selection(
        [('employee', 'By Employee'), ('department', 'By Department'), ('tag', 'By Tag'), ('company', 'By Company')],
        string='Mode', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    tag_ids = fields.Many2many('hr.employee.category', 'penalty_rule_tag_rel',
                               'penalty_id', 'tag_id', 'Tags')
    department_ids = fields.Many2many('hr.department', 'penalty_rule_department_rel',
                                      'penalty_rule_id', 'department_id', 'Department')
    company_id = fields.Many2one('res.company', 'Company')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    penalty_lines = fields.One2many('hr.penalty.line', 'penalty_id', 'Penalty')
    absent_penalty = fields.Float('Absent Penalty')
    unpaid_leave_penalty = fields.Float('Unpaid Leave Penalty')
    no_sign_in = fields.Float('No sign in')
    no_sign_out = fields.Float('No sign out')
    absent_time = fields.Selection([('hours', 'Hours'), ('days', 'Days')], 'Absent Time')
    unpaid_time = fields.Selection([('hours', 'Hours'), ('days', 'Days')], 'Unpaid Time')
    no_sign_in_time = fields.Selection([('hours', 'Hours'), ('days', 'Days')], 'Absent Time')
    no_sign_out_time = fields.Selection([('hours', 'Hours'), ('days', 'Days')], 'Absent Time')
    absent_penalty_lines = fields.One2many('hr.penalty.absent.line', 'penalty_id', 'Penalty')
    additional_flexible_line = fields.One2many('additional.flexible.hours', 'penalty_id',
                                               'Additional Flexible Line')


class hr_penalty_line(models.Model):
    _name = 'hr.penalty.line'

    penalty_id = fields.Many2one('hr.penalty', 'Penalty')
    late_early = fields.Selection([('late', 'Late'), ('early', 'Early')], 'Late/Early', required=True)
    action = fields.Selection(
        [('sign_in', 'Sign In'), ('sign_out', 'Sign Out'), ('break_in', 'Break in'), ('break_out', 'Break out')],
        'Action', required=True)
    from_min = fields.Integer('From(minutes)')
    to_min = fields.Integer('To(minutes)')
    penalty_type = fields.Selection([('same_delay', 'Same Delay'), ('fixed', 'Fixed')], string="Penalty Type")
    multiple = fields.Float('Multiple', default=lambda *a: 1.0)
    deduction = fields.Float('Deduction(Hours)')
    first_time = fields.Float('First Time')
    second_time = fields.Float('Second Time')
    third_time = fields.Float('Third Time')
    fourth_time = fields.Float('Fourth Time')

    @api.onchange('penalty_type')
    def onchange_penalty_type(self):
        if self.penalty_type:
            if self.penalty_type != 'same_delay':
                self.multiple = 0.0



class additional_flexible_hours(models.Model):
    _name = 'additional.flexible.hours'
    _description = "Additional Flexible Hours"
    _order = 'from_time'

    from_time = fields.Float('From Time')
    to_time = fields.Float('To Time')
    flex_hours = fields.Float('Additional Flexible Hours')
    penalty_id = fields.Many2one('hr.penalty', 'Penalty')

    @api.onchange('from_time', 'to_time')
    def oncahnge_time(self):
        if self.from_time and self.to_time and self.from_time > self.to_time:
            raise Warning(_("From Time can not be grater than To Time"))

        str_fromtime = str(self.from_time)
        str_totime = str(self.to_time)

        fromhr = str_fromtime.split('.')[0]
        frommin = str_fromtime.split('.')[1]
        tohr = str_totime.split('.')[0]
        tomin = str_totime.split('.')[1]

        if len(frommin) == 1:
            frommin = frommin + '0'
        if len(tomin) == 1:
            tomin = tomin + '0'

        if int(fromhr) >= 24:
            self.from_time = False
            raise UserError(_("From Time Hours can not be equal or greater than 24."))
        if int(tohr) >= 24:
            self.to_time = False
            raise UserError(_("To Time Hours can not be equal or greater than 24."))
        if int(frommin) >= 60:
            self.from_time = False
            raise UserError(_("From Time Minutes can not be equal or greater than 60."))
        if int(tomin) >= 60:
            self.to_time = False
            raise UserError(_("To Time Minutes can not be equal or greater than 60."))



class hr_attendance(models.Model):
    _inherit = 'hr.attendance'

    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    store=True, related="employee_id.department_id")


class hr_penalty_absent_line(models.Model):
    _name = 'hr.penalty.absent.line'

    first_time = fields.Float('First Time', required=1)
    second_time = fields.Float('Second Time', required=1)
    third_time = fields.Float('Third Time', required=1)
    fourth_time = fields.Float('Fourth Time', required=1)
    penalty_id = fields.Many2one('hr.penalty', 'Penalty')


class patch_delay_cal(models.Model):
    _name = 'patch.delay.cal'

    _rec_name = 'description'

    description = fields.Char('Description')
    company = fields.Many2one('res.company')
    approval = fields.Many2one('hr.employee', required=True)
    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    employee_ids = fields.Many2many('hr.employee', 'employee_id', 'emp_patch_rel', 'patch_id', 'Employees')

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'company': lambda self, cr, uid, c: self.pool.get('res.company'). \
            _company_default_get(cr, uid, 'hr.employee', context=c),
    }

    # @api.multi
    def calculate_delay(self):
        contract_pool = self.env['hr.contract']
        employee_delay_pool = self.env['employee.delay']
        for this in self:

            if not this.employee_ids:
                raise UserError(_('No employee is selected. Select at least one employee to calculate Delay.'))

            # CHECK ALL EMPLOYEES CONTRACT EXISTS OR NOT
            emp_without_contract = []
            for emp in this.employee_ids:
                domain = [('state', 'in', ['draft', 'open']), ('employee_id', '=', emp.id)]
                contract_ids = contract_pool.search(domain, order='id DESC')
                if contract_ids:
                    contract = contract_ids[0]
                    if not contract.date_end:
                        date_end = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                    else:
                        date_end = datetime.strptime(this.date_to, '%Y-%m-%d').date()

                    # print(f"date_end ===== {date_end}")
                    # print(f"contract date ===== {contract.date_start}")
                    if contract.date_start <= date_end:
                        pass
                    else:
                        contract_ids = []

                if not contract_ids:
                    emp_without_contract.append(emp)

            if emp_without_contract:
                emp_without = ', '.join([x.name for x in emp_without_contract])
                raise UserError(_('Below employees contract not found from the selection.\n%s' % (emp_without)))

            if not emp.department_id:
                raise UserError(_('No department configured for Employee: %s. Please Configure.' % (emp.name)))

            # check employee shift
            for employee in this.employee_ids:
                shift_exists = self.get_employee_shift(employee.id,
                                                       this.date_from, this.date_to)
                if not shift_exists:
                    raise UserError(_('Employee %s has no assigned shifts in period from %s To %s.' % (
                        employee.name, this.date_from, this.date_to)))

            for employee in this.employee_ids:
                # CREATE ALL EMPLOYEES DELAY & LINES
                emp_delay_data = {
                    'employee_id': employee.id,
                    'department_id': employee.department_id and employee.department_id.id or False,
                    'date_from': this.date_from,
                    'date_to': this.date_to,
                }
                employee_delay_id = employee_delay_pool.create(emp_delay_data)

                # CALL CALCULATION METHOD FOR EACH EMPLOYEE
                employee_delay_pool.with_context(employee_delay_ids=[employee_delay_id.id]).calc_delay()

    def get_employee_shift(self, employee_id, date_from, date_to):
        employee_pool = self.env['hr.employee']
        employee = employee_pool.browse(employee_id)
        # CHECK EMPLOYEE SHIFT IS CREATED OR NOT
        assign_shift_line_pool = self.env['assign.shift.line']
        # First employee shift to check
        assign_shift_line_ids = assign_shift_line_pool.search([
            ('start_from', '<=', date_from),
            ('to_date', '>=', date_to),
            ('assign_shift_id.mode', '=', 'employee'),
            ('assign_shift_id.employee_id.id', 'in', [employee_id])])
        if not assign_shift_line_ids:
            # Second check Department Shift
            if employee.department_id:
                assign_shift_line_ids = assign_shift_line_pool.search([
                    ('start_from', '<=', date_from),
                    ('to_date', '>=', date_to),
                    ('assign_shift_id.mode', '=', 'department'),
                    ('assign_shift_id.department_id.id', 'in', [employee.department_id.id])])

        if not assign_shift_line_ids:
            # Third check Department Shift
            # Second check Department Shift
            category_ids = [x.id for x in employee.category_ids]
            if employee.category_ids:
                assign_shift_line_ids = assign_shift_line_pool.search([
                    ('start_from', '<=', date_from),
                    ('to_date', '>=', date_to),
                    ('assign_shift_id.mode', '=', 'tag'),
                    ('assign_shift_id.tag_id.id', 'in', category_ids)])
        return assign_shift_line_ids


########### Employee Delay Line Class #########
class employee_delay_line(models.Model):
    _name = 'employee.delay.line'

    employee_delay_id = fields.Many2one("employee.delay", "Employee Delay")

    date = fields.Date('Date')
    time_diff = fields.Float('Late/Early Time Diff')
    type = fields.Selection([('late_signin', 'Late Sign-In'),
                             ('late_signout', 'Early Sign-Out'),
                             ('no_signin', 'No Sign-In'),
                             ('no_signout', 'No Sign-Out'),
                             ('absent', 'Absent Penalty'),
                             ('unpaid_leave', 'Unpaid Leave Penalty'),
                             ('leaves', 'Leaves'),
                             ('rest_day', 'Rest Day'),
                             ('no_delay', 'No Delay'),
                             ('early_breakin', 'Early Break-In'),
                             ('late_breakout', 'Late Break-Out'), ],
                            string="Type")
    permission = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Permission")
    permission_hours = fields.Float('Permission Hours')
    deduction = fields.Float('Deduction')
    ded_applied = fields.Float('Deduction Applied')
    waive = fields.Boolean('Waive')
    worked_hours = fields.Float('Worked Hours')
    working = fields.Float('Working')
    note = fields.Text('Notes')
    actual_delay = fields.Float('Actual Delay')
    dont_show = fields.Boolean('Dont show toggle button')
    count = fields.Float('Count')
    penalty_line_id = fields.Many2one('hr.penalty.line', 'Penalty')

    copied_worked = fields.Boolean('Worked Hours Copied', defualt=lambda *a: False)
    working_original = fields.Float('Working Original', help="working value to hold in background")

    first_signin = fields.Char("First Sign-In")
    last_signout = fields.Char("Last Sign-out")
    allowed_nextday = fields.Float("Allowed Next Day")
    odd_action = fields.Boolean('Odd Action', help="Checked if found odd action of sign-in and/or sign-out.")
    travel_alw = fields.Float("Travel Allowance")


    def action_waive(self):
        if self.waive:
            self.waive = False
        else:
            self.waive = True


########### Employee Delay Class #########
class employee_delay(models.Model):
    _name = 'employee.delay'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread']

    # # @api.multi
    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #     if 'state' in init_values and self.state == 'draft':
    #         return 'elsaka_hr_penalty.mt_delay_draft'
    #     elif 'state' in init_values and self.state == '1approve':
    #         return 'elsaka_hr_penalty.mt_delay_1approve'
    #     elif 'state' in init_values and self.state == '2approve':
    #         return 'elsaka_hr_penalty.mt_delay_2approve'
    #     elif 'state' in init_values and self.state == 'approved':
    #         return 'elsaka_hr_penalty.mt_delay_approved'
    #     elif 'state' in init_values and self.state == 'refuse':
    #         return 'elsaka_hr_penalty.mt_delay_refuse'
    #     return super(employee_delay, self)._track_subtype(init_values)

    # @api.one
    @api.depends('employee_id','employee_delay_line.deduction', 'employee_delay_line.time_diff', 'employee_delay_line.waive', 'state', 'employee_delay_line.working', 'employee_delay_line.worked_hours')
    def _calc_all(self):
        worked_dict = {}
        working_dict = {}
        for delay in self:
            deduction = 0.0
            waive = 0.0
            absent = 0.0
            total_actual_delay = 0.0
            total_absent_hours = 0.0
            total_worked_hours = 0.0
            total_working = 0.0
            total_permission_hours = 0.0
            total_late_signin = 0.0
            total_early_signout = 0.0
            total_travel_alw = 0.0
            total_leaves_amount = 0.0
            count_leaves_days = 0.0
            total_res_days_amount = 0.0
            count_rest_days = 0.0
            total_attendance_days_amount = 0.0
            count_attendance_days = 0.0
            day_rate = 0.0
            contract = delay.get_employee_contract(delay.employee_id)
            first_leave_date = ''
            count = 0.0
            if contract and contract.gross:
                # print(f'contract.gross ====== {contract.gross}')
                day_rate = round(contract.gross / 30, 2)
            # print(f'len(delay.employee_delay_line) ========= {len(delay.employee_delay_line)}')
            permission_list = []
            late_signin = []
            early_signout = []
            travel_list = []
            for delay_line in delay.employee_delay_line:
                # print(f'day_rate ======= {day_rate}')
                if delay_line.type == 'leaves' and not delay_line.deduction:
                    if count == 0.0:
                        first_leave_date += str(delay_line.date)
                        total_leaves_amount += day_rate
                        count_leaves_days += 1
                        count += 1
                    else:
                        total_leaves_amount += day_rate
                        count_leaves_days += 1

                if delay_line.type == 'rest_day':
                    if first_leave_date:
                        convert_first_leave_date = datetime.strptime(first_leave_date, '%Y-%m-%d').date()
                        if delay_line.date < convert_first_leave_date:
                            total_res_days_amount += day_rate
                            count_rest_days += 1
                    else:
                        total_res_days_amount += day_rate
                        count_rest_days += 1

                if delay_line.type not in ['rest_day', 'leaves', 'absent', 'unpaid_leave']:
                    total_attendance_days_amount += day_rate
                    count_attendance_days += 1

                if delay_line.date not in worked_dict.keys():
                    worked_dict[delay_line.date] = delay_line.worked_hours

                if delay_line.date not in working_dict.keys():
                    working_dict[delay_line.date] = delay_line.working

                if delay.state == 'approved':
                    delay_line.write({'dont_show': True})

                if delay_line.type in ['late_signin', 'late_signout']:
                    if delay_line.type == 'late_signin' and not delay_line.waive:
                        late_signin.append(delay_line.time_diff)
                    elif delay_line.type == 'late_signout' and not delay_line.waive:
                        early_signout.append(delay_line.time_diff)
                    # total_actual_delay += delay_line.time_diff

                permission_list.append(delay_line.permission_hours)
                travel_list.append(delay_line.travel_alw)

                deduction += delay_line.deduction
                if delay_line.waive:
                    waive += delay_line.deduction
                    continue
                if delay_line.type == 'absent':
                    absent += delay_line.deduction
                    total_absent_hours += delay_line.ded_applied
                    continue


                if delay_line.type in ['late_signin', 'late_signout']:
                    total_actual_delay += delay_line.time_diff

            total_worked_hours = float(sum(worked_dict.values()))
            total_worked_hours = delay.revise_shift_ends(total_worked_hours)

            total_working = float(sum(working_dict.values()))
            total_working = delay.revise_shift_ends(total_working)
            total_target_hours = delay.get_target_working_hours(delay.employee_id.id,
                                                               delay.date_from, delay.date_to)
            total_target_hours = delay.convert_time_to_float(total_target_hours)
            total_permission_hours = delay.add_time(permission_list)
            total_late_signin = delay.add_time(late_signin)
            total_early_signout = delay.add_time(early_signout)

            delay.total_late_deduction = deduction - absent
            delay.total_waived_deduction = waive
            delay.total_absent_deduction = absent
            delay.total_actual_delay = total_actual_delay
            delay.total_worked_hours = total_worked_hours
            delay.total_working = total_working

            # if contract:
            #     if total_target_hours >= contract.target_dedcution_hours:
            #         delay.total_target_hours = subtract_patch(float(contract.target_dedcution_hours), total_target_hours)
            #     else:
            #         delay.total_target_hours = subtract_patch(total_target_hours, float(contract.target_dedcution_hours))
            delay.total_target_hours = total_target_hours
            delay.total_permission_hours = total_permission_hours
            delay.total_late_signin = total_late_signin
            delay.total_early_signout = total_early_signout

            # if delay.total_working >= delay.total_target_hours:
            #     delay.target_deduction = 0.0
            # else:
            #     per_hour_rate = delay.get_employee_per_hour_rate(delay.employee_id,
            #                                                     delay.date_from, delay.date_to, delay.has_ramadan)
            #     # per_hour_rate = contract.wage and total_target_hours and (contract.wage / total_target_hours) or 0.0
            #     temp_target_dedcution = float(contract.target_dedcution_rate) or 1
            #     target_subtracted_working = subtract_patch(delay.total_working, delay.total_target_hours)  # SMALL FIRST
            #     print(f"per_hour_rate ====== {per_hour_rate}")
            #     print(f"temp_target_dedcution ====== {temp_target_dedcution}")
            #     print(f"target_subtract_working ====== {target_subtracted_working}")
            #     delay.target_deduction = target_subtracted_working * per_hour_rate * temp_target_dedcution
            # per_hour_rate = delay.get_employee_per_hour_rate(delay.employee_id, delay.date_from, delay.date_to, delay.has_ramadan)
            if delay.employee_id:
                per_hour_rate = delay.get_employee_per_hour_rate(delay.employee_id, delay.date_from, delay.date_to, delay.has_ramadan)
            else:
                per_hour_rate = 0.0
            # print(f' Per_hour_rate ======> {per_hour_rate}')
            total_hours_deduction = total_target_hours - total_worked_hours
            if total_hours_deduction < 0.0:
                total_hours_deduction = 0.0
            else:
                total_hours_deduction = total_hours_deduction
            # print(f' total_hours_deduction ======> {total_hours_deduction}')
            # # total_absent_hours = sum(delay.employee_delay_line.filtered(lambda r: r.type != 'absent').mapped('ded_applied'))
            # print(f' total_absent_hours ======> {total_absent_hours}')
            delay.total_hours_deduction = total_hours_deduction
            delay.target_deduction = total_hours_deduction * per_hour_rate
            delay.total_deduction = (deduction - waive) + delay.target_deduction

            print(f"per_hour_rate ====== {per_hour_rate}")
            print(f"total_hours_deduction ====== {total_hours_deduction}")
            print(f"target_deduction ====== {delay.target_deduction}")

            delay.total_leaves_amount = total_leaves_amount
            delay.count_leaves_days = count_leaves_days
            delay.total_rest_days_amount = total_res_days_amount
            delay.count_rest_days = count_rest_days
            delay.total_attendance_days_amount = total_attendance_days_amount
            delay.count_attendance_days = count_attendance_days

    @api.depends('date_from', 'date_to')
    def _has_ramadan(self):
        assign_shift_line_pool = self.env['assign.shift.line']
        patch_delay_cal_pool = self.env['patch.delay.cal']
        date_list = self.generate_date_dic(self.date_from, self.date_to, "%Y-%m-%d")
        has_ramadan = False
        for date in date_list:
            shift_line_ids = patch_delay_cal_pool.get_employee_shift(self.employee_id.id, date, date)
            # print(f"shift linesss ===== {shift_line_ids}")
            if shift_line_ids:
                shift_line = shift_line_ids[0]
                # print(f"shift linesss ===== {shift_line}")
                if shift_line.shift_id.is_ramadan:
                    has_ramadan = True
        self.has_ramadan = has_ramadan

    employee_id = fields.Many2one('hr.employee', 'Employees', required=True)
    department_id = fields.Many2one('hr.department', 'Department')
    date_from = fields.Date('Date From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date To', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))

    employee_delay_line = fields.One2many('employee.delay.line', 'employee_delay_id', 'Employee Delay Line')

    has_ramadan = fields.Boolean(compute='_has_ramadan', string='Has Ramadan?', store=True)
    total_late_deduction = fields.Float(compute=_calc_all, string='Total Late Deduction', store=True)
    total_target_hours = fields.Float(compute=_calc_all, string='Total Target Hours', store=True)
    total_actual_delay = fields.Float(compute=_calc_all, string='Total Actual Delay', store=True,
                                      help="Actual Delay Without Unpaid")
    total_worked_hours = fields.Float(compute=_calc_all, string='Total Worked Hours', store=True,
                                      help="Worked Hours Total")
    total_working = fields.Float(compute=_calc_all, string='Total Working', store=True,
                                 help="Working Total")
    total_waived_deduction = fields.Float(compute=_calc_all, string='Total Waived Deduction', store=True)
    total_absent_deduction = fields.Float(compute=_calc_all, string='Total Absent Deduction', store=True)
    target_deduction = fields.Float(compute=_calc_all, string='Target Deduction', store=True)
    total_deduction = fields.Float(compute=_calc_all, string='Total Deduction', store=True)
    total_permission_hours = fields.Float(compute=_calc_all, string='Total Permission Hours', store=True)
    total_late_signin = fields.Float(compute=_calc_all, string='Total Late Sign-In', store=True)
    total_early_signout = fields.Float(compute=_calc_all, string='Total Early Sign-Out', store=True)
    total_hours_deduction = fields.Float(compute=_calc_all, string='Total Hour Deduction', store=True)

    total_leaves_amount = fields.Float(compute=_calc_all, string='Total Leaves Amount', store=True)
    count_leaves_days = fields.Float(compute=_calc_all, string='Total Leave Days', store=True)
    total_rest_days_amount = fields.Float(compute=_calc_all, string='Total Rest Leaves', store=True)
    count_rest_days = fields.Float(compute=_calc_all, string='Total Rest Days', store=True)
    total_attendance_days_amount = fields.Float(compute=_calc_all, string='Total Attendance Amount', store=True)
    count_attendance_days = fields.Float(compute=_calc_all, string='Total Attendance Days', store=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('1approve', 'First Approve'),
                              ('2approve', 'Second Approve'),
                              ('approved', 'Approved'),
                              ('refuse', 'Refused')],
                             string="State", default=lambda *a: 'draft', track_visibility='onchange')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id and self.employee_id.department_id.id or False
            self.get_employee_contract(self.employee_id)
        else:
            self.department_id = False

    def action_first_approve(self):
        self.write({'state': '1approve'})

    def action_second_approve(self):
        self.state = '2approve'

    def action_approved(self):
        self.state = 'approved'

    def action_refuse(self):
        self.state = 'refuse'

    def action_reset(self):
        self.state = 'draft'

    def convert_datetime_to_tz(self, date):
        tz = "tz" in self.env.context and self.env.context.get('tz') or 'UTC' if self.env.context else "UTC"
        local_timezone = pytz.timezone(tz)
        utc_time = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
        converted_date = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone).strftime("%Y-%m-%d %H:%M:%S")
        return converted_date

    def get_employee_contract(self, employee_id):
        contract_pool = self.env['hr.contract']
        contract_ids = contract_pool.search([('employee_id', '=', employee_id.id),
                                             ('state', 'in', ['open'])])
        # if not contract_ids:
        #     raise UserError(_('Employee Contract Not Found.'))
        if contract_ids:
            return contract_ids[0]

    @api.model
    def create(self, values):
        # Overlapping the dates to restrict the user
        delay_ids1 = self.search([('employee_id', '=', values['employee_id']),
                                  ('date_from', '<=', values['date_from']),
                                  ('date_to', '>=', values['date_from'])])
        delay_ids2 = self.search([('employee_id', '=', values['employee_id']),
                                  ('date_from', '<=', values['date_to']),
                                  ('date_to', '>=', values['date_to'])])
        delay_ids = delay_ids1 + delay_ids2
        if delay_ids:
            raise UserError(_('Delay Calculation with Employee is overlapping of selected period.'))
        return super(employee_delay, self).create(values)

    def get_working_hours(self,key, employee_id, shift_line, value=[],
                          rest_day=False, holiday=False, no_in_out=False):
        att_pool = self.env['hr.attendance']
        shift_hours = shift_line and shift_line.shift_id and shift_line.shift_id.total_working_hours or 0.0

        # REST DAY
        if rest_day:
            working = self.calc_worked_hours_revised(att_pool, key, employee_id)
            return working

        if not holiday:
            if not value:
                # (ABSENT) NO holiday No Attendance
                working = shift_hours
                return working

        if not no_in_out:
            # NO SIGN IN OR SIGN OUT
            working = shift_hours and shift_hours / 2 or 0.0
            return working

    def get_penalty_rule(self, this, key):
        penalty_rule_pool = self.env['hr.penalty']
        domain_date = [('date_from', '<=', key), ('date_to', '>=', key)]
        penalty_rule_ids = penalty_rule_pool.search([
            ('employee_id', 'in', [this.employee_id.id]),
            ('mode', '=', 'employee')] + domain_date, order="id DESC")
        if not penalty_rule_ids:
            penalty_rule_ids = penalty_rule_pool.search([
                ('department_ids', 'in', [this.department_id.id]),
                ('mode', '=', 'department')] + domain_date, order="id DESC")
        if not penalty_rule_ids:
            tag_ids = [x.id for x in this.employee_id.category_ids]
            penalty_rule_ids = penalty_rule_pool.search([
                ('tag_id', 'in', tag_ids),
                ('mode', '=', 'tag')] + domain_date, order="id DESC")
        if not penalty_rule_ids:
            raise UserError(_('Warning! No Penalty Rule found.'))
        penalty_rule = penalty_rule_ids[0]
        # print(f'penalty_rule =========== {penalty_rule}')
        return penalty_rule

    def calc_delay(self):

        if 'employee_delay_ids' in self.env.context:
            employee_delay_ids = self.env.context.get('employee_delay_ids')
        else:
            employee_delay_ids = self.ids
        employee_delay_line_pool = self.env['employee.delay.line']
        attendance_pool = self.env['hr.attendance']
        patch_delay_cal_pool = self.env['patch.delay.cal']
        assing_shift_line_pool = self.env['assign.shift.line']
        penalty_rule_pool = self.env['hr.penalty']

        for this in self.browse(employee_delay_ids):
            # special_dates = []
            # FLUSH THE DATA & RECALCULATE
            if this.employee_delay_line:
                this.employee_delay_line.unlink()
                # line_ids = [x.id for x in this.employee_delay_line]
                # employee_delay_line_pool.unlink(line_ids)

            date_format = "%Y-%m-%d"
            date_list = self.generate_date_dic(this.date_from, this.date_to, date_format)
            datewise_data = dict((x, []) for x in date_list)
            # Penalty Rule
            penalty_rule = penalty_rule_pool.search([
                ('employee_id', '=', this.employee_id.id),
                ('mode', '=', 'employee')])
            if not penalty_rule:
                penalty_rule = penalty_rule_pool.search([
                    ('department_ids', 'in', [this.employee_id.department_id.id]),
                    ('mode', '=', 'department')])
            if not penalty_rule:
                tag_ids = [x.id for x in this.employee_id.category_ids]
                penalty_rule = penalty_rule_pool.search([
                    ('tag_ids', 'in', tag_ids),
                    ('mode', '=', 'tag')], order="id DESC")
            if not penalty_rule:
                raise UserError(_('No Penalty Rule found.'))


            for key, value in datewise_data.items():
                attendance_ids = attendance_pool.search([
                    ('employee_id', '=', this.employee_id.id),
                    ('check_in', '>=', key + ' 00:00:01'),
                    ('check_in', '<=', key + ' 23:59:59')]
                    , order="check_in ASC")
                attendance_ids = [x.id for x in attendance_ids]
                datewise_data.update({key: attendance_ids})
            datewise_data = OrderedDict(sorted(datewise_data.items(), key=itemgetter(0)))
            # print "DATEWISE DICTIONARY : ========> ",datewise_data

            count = 0
            absent_count = 0
            # per_hour = self.get_employee_per_hour_rate(this.employee_id,
            #                                            this.date_from, this.date_to, this.has_ramadan)

            # Employee Delay Line Data
            for key, value in datewise_data.items():
                # print "\n\nKEY : VALUE ======================================================> ",key,value

                penalty_rule = self.get_penalty_rule(this, key)

                # shift data
                assign_shift_line_ids = patch_delay_cal_pool.get_employee_shift(this.employee_id.id, key, key)
                if not assign_shift_line_ids:
                    raise UserError(_('Employee %s has no assigned shifts in period from %s To %s.' % (
                        this.employee_id.name, this.date_from, this.date_to)))
                # print(f"shift line Ids ======= {assign_shift_line_ids}")
                shift_line = assign_shift_line_ids
                #                 print "SHIFT APPLIED: =============> ",shift_line.shift_id.id,shift_line.shift_id.name
                # flixable_hours = sum(assign_shift_line_ids.mapped("flexible_hours"))
                # sum(assign_shift_line_ids.mapped("from_hours"))
                # flexible_hours = sum(assign_shift_line_ids.mapped("flexible_hours"))
                # from_hours = sum(assign_shift_line_ids.mapped("from_hours"))
                # shift_starts = float(from_hours + flexible_hours)
                flexible_hours = 0.0
                from_hours = 0.0
                for rec in shift_line:
                    flexible_hours += rec.shift_id.flexible_hours
                    from_hours += rec.shift_id.from_hours
                shift_starts = float(from_hours + flexible_hours)
                # shift_starts = float(shift_line.shift_id.from_hours + shift_line.shift_id.flexible_hours)
                shift_starts = self.revise_shift_ends(shift_starts)
                # print(f"shift start ====> {shift_starts}")

                # GETTIG PER HOUR FROM SPECIAL MONTHS AND GROSS WAGE
                per_hour = 0.0
                contract = self.get_employee_contract(this.employee_id)
                if contract:
                    if contract.special_month:
                        month_line_pool = self.env['month.line']
                        month_line_ids = month_line_pool.search([
                            ('contract_id.employee_id', '=', this.employee_id.id),
                            ('contract_id.state', 'in', ['draft', 'open']),
                            ('contract_id.special_month', '=', True),
                            ('date_from', '<=', key),
                            ('date_to', '>=', key)])
                        if not month_line_ids:
                            raise UserError(_("No Special Month Configured found for employee %s's Contract of date %s." % (
                                this.employee_id.name, key)))
                        per_hour = month_line_ids[0].per_hour
                    else:
                        # per_hour = contract.gross and (contract.gross / (22 * shift_line.shift_id.total_working_hours))
                        # or 0.0#Assuming 22 day of a month
                        per_hour = contract.gross and (contract.gross /
                                                       (
                                                               22 * (
                                                               shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours))) or 0.0  # Assuming 22 day of a month
                else:
                    per_hour = 0.0

                next_day_data = self.get_next_day_allowed_time(attendance_pool,
                                                               this, key, penalty_rule)
                first_signin = next_day_data[2]
                last_signout = next_day_data[0]
                allowed_nextday = next_day_data[1]
                # print(f"first sign in ==== {first_signin}")
                # print(f"last sign last_signout ==== {last_signout}")
                # print(f"allowed next day ==== {allowed_nextday}")

                shift_ends = shift_line.shift_id.to_hours
                worked_hours = 0.0
                note = ''
                working = 0.0
                half_time = 0.0
                deduction = 0.0
                permission = 'no'
                permission_hrs = 0.0
                ded_applied = 0.0
                actual_delay = 0.0
                public_leave = False
                half_leave = False
                halfday_leave_unpaid = 0.0
                per_unpaid = False
                travel_alw = 0.0

                # REST DAYS TO SKIPPED
                rest_days_list = [x.name for x in shift_line.rest_days]
                if datetime.strptime(str(key), date_format).strftime('%A') in rest_days_list:
                    working = self.get_working_hours(key, this.employee_id.id,
                                                     shift_line, value=value, rest_day=True, holiday=False,
                                                     no_in_out=True)
                    if value:
                        worked_hours = working
                        working = 0.0

                    self.create_line(key, 0.0, 'rest_day', False,
                                     permission, permission_hrs, actual_delay, ded_applied,
                                     deduction, worked_hours, note, working, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                    continue


                # IF NO ATRENDANCE DATA FOUND
                if not value:
                    leave_data = self.check_approved_leave(this.employee_id.id, key)
                    holiday_ids = leave_data['holiday_ids']
                    special_dates = leave_data['date_list']
                    # print(f'key ======== {key}')
                    # print(f'special_dates ======== {special_dates}')
                    # print(f'holiday_ids ======== {holiday_ids}')
                    if not holiday_ids and key not in special_dates:
                        type = 'absent'
                        actual_delay = shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours
                        for line in penalty_rule:
                            ded_applied = line.absent_penalty
                        absent_count += 1
                        ded_applied = self.check_penalty_absent_rule_line(penalty_rule, absent_count)
                        if not ded_applied:
                            ded_applied = penalty_rule.absent_penalty
                        deduction = ded_applied * per_hour
                        self.create_line(key, 0.0,
                                         type, False, permission, permission_hrs, actual_delay,
                                         ded_applied, deduction, worked_hours, note, working, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                        continue

                    for leave in holiday_ids:
                        if leave_data['date_list']:
                            note = leave.holiday_status_id.name
                            for element in leave_data['date_list']:
                                type = 'leaves'
                                worked_hours = not leave.holiday_status_id.unpaid and (
                                        shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours) or 0.0
                                working = worked_hours
                                ded_applied = leave.holiday_status_id.unpaid and penalty_rule.unpaid_leave_penalty or 0.0
                                deduction = ded_applied * per_hour
                                actual_delay = leave.holiday_status_id.unpaid and (
                                        shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours) or 0.0
                                if element == key:
                                    self.create_line(element, 0.0,
                                                     type, False, permission, permission_hrs, actual_delay,
                                                     ded_applied, deduction, worked_hours, note, working,
                                                     0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                            continue

                        # CHECK IF UNPAID LEAVE
                        if leave.holiday_status_id.unpaid and not leave.holiday_status_id.appear_time_field:
                            if key not in leave_data['date_list']:
                                type = 'unpaid_leave'
                                actual_delay = leave.holiday_status_id.unpaid and (
                                        shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours) or 0.0
                                ded_applied = penalty_rule.unpaid_leave_penalty
                                deduction = ded_applied * per_hour
                                self.create_line(key, 0.0,
                                                 type, False, permission, permission_hrs, actual_delay, ded_applied,
                                                 deduction, worked_hours, note, working, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                    continue

                # CHECK PERMISSION EXISTS OR NOT
                permission_ids = []
                holiday_ids = self.check_permission_leave(
                    this.employee_id.id, key)
                for leave in holiday_ids:
                    fromtime = self.revise_shift_ends(leave.from_time)
                    totime = self.revise_shift_ends(leave.to_time)
                    ph = self.convert_float_to_time(fromtime, totime)
                    ph = self.revise_shift_ends(ph)
                    permission_hrs += ph
                    permission = 'yes'
                    per_unpaid = leave.holiday_status_id.unpaid
                    pph = not leave.holiday_status_id.unpaid and leave.total_hours or 0.0
                    permission_ids.append({'leave': leave, 'permi': per_unpaid, 'pph': pph})

                sign_in = ''
                sign_out = ''
                if len(value) == 1:
                    att = attendance_pool.browse(value[0])
                    #                     sign_in = att['check_in']
                    if att and att.check_in:
                        sign_in = self.convert_datetime_to_tz(att.check_in)
                        #                     sign_out = att['check_out']
                    if att and att.check_out:
                        sign_out = self.convert_datetime_to_tz(att.check_out)
                else:
                    value = attendance_pool.search([('id', 'in', value)], order='check_in ASC')
                    att = value[0]
                    # DETERMINE FIRST SIGN IN
                    #                     sign_in = att.check_in
                    if att and att.check_in:
                        sign_in = self.convert_datetime_to_tz(att.check_in)

                    # DETERMINE LAST SIGN OUT
                    att = value[-1]
                    #                     sign_out = att.check_out
                    if att and att.check_out:
                        sign_out = self.convert_datetime_to_tz(att.check_out)

                # check attendance with Leave
                leave_data = self.check_approved_leave(this.employee_id.id, key)
                leave_ids = leave_data['holiday_ids']
                #                 print "leave_ids: =============> ",leave_ids
                for leave in leave_ids:
                    # PUBLIC LEAVE
                    if leave.holiday_status_id.public_leave or \
                            not leave.half_day and \
                            not leave.holiday_status_id.appear_time_field and \
                            not leave.holiday_status_id.unpaid:
                        note = 'Available On %s (Overtime)' % (leave.holiday_status_id.name)
                        worked_hours = self.calc_worked_hours_revised(attendance_pool, key,
                                                                      this.employee_id.id)
                        working = shift_line.shift_id.total_working_hours
                        self.create_line(key, 0.0, 'leaves',
                                         'no', 0.0, 0.0, 0.0, 0.0, 0.0, worked_hours, note, working,
                                         0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                        public_leave = True
                        continue
                    if leave.request_unit_half and not leave.holiday_status_id.unpaid and \
                            not leave.holiday_status_id.appear_time_field:
                        half_time = float(
                            (shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours) / 2)
                        if half_time:
                            half_time = self.convert_float_to_time_as_float1(half_time)
                            if leave.half_day_type == 'first_half':
                                shift_starts = shift_starts + half_time
                                shift_starts = self.revise_shift_ends(shift_starts)
                                note = "First Half Leave"
                            else:
                                note = "Second Half Leave"
                                shift_ends = shift_ends - half_time
                                shift_ends = self.revise_shift_ends(shift_ends)
                        # print "shift_start:shift_ends ===========> ",shift_starts,shift_ends


                if public_leave:
                    continue

                loop = False
                signin_penalty = 0.0
                signout_penalty = 0.0
                if sign_in:
                    singin_time = self.get_float_time(sign_in)
                    if shift_starts < singin_time:
                        #                         signin_penalty = float(singin_time - shift_starts)
                        #                         if int(str(signin_penalty).split('.')[1]) >= 6:
                        # print "1... shift_starts, singin_time: ======>",shift_starts, singin_time
                        signin_penalty = self.convert_float_to_time(shift_starts, singin_time)
                        # print "signin_penalty: ==============> ",signout_penalty

                        if shift_line.shift_id.flexible_hours:
                            shift_ends = float(shift_ends + shift_line.shift_id.flexible_hours)
                            shift_ends = self.revise_shift_ends(shift_ends)
                        else:
                            if shift_line.shift_id.flexible_hours:
                                shift_ends = float(shift_ends + (shift_starts - singin_time))
                    else:
                        if not leave_ids:
                            if singin_time > shift_line.shift_id.from_hours and \
                                    shift_line.shift_id.flexible_hours:
                                shift_ends = float(
                                    shift_ends + self.convert_float_to_time(shift_line.shift_id.from_hours,
                                                                            singin_time))
                                shift_ends = self.revise_shift_ends(shift_ends)
                        else:
                            shift_without_flex = self.convert_float_to_time(shift_line.shift_id.flexible_hours,
                                                                            shift_starts)
                            shift_without_flex = self.revise_shift_ends(shift_without_flex)
                            if shift_line.shift_id.flexible_hours and shift_without_flex < singin_time:
                                shift_ends = float(
                                    shift_ends + self.convert_float_to_time(shift_without_flex, singin_time))
                                shift_ends = self.revise_shift_ends(shift_ends)
                else:
                    # No sign in penalty
                    ded_applied = penalty_rule.no_sign_in
                    type = 'no_signin'
                    deduction = ded_applied * per_hour
                    self.create_line(key, 0.0, type, False,
                                     permission, permission_hrs, actual_delay, ded_applied,
                                     deduction, worked_hours, note, working,
                                     0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                    continue

                if sign_out:
                    singout_time = self.get_float_time(sign_out)
                    if singout_time < shift_ends:
                        #                         signout_penalty = float(shift_ends - singout_time)
                        #                         if int(str(signout_penalty).split('.')[1]) >= 6:
                        signout_penalty = self.convert_float_to_time(singout_time, shift_ends)
                        # print "signout_penalty: ==============> ",signout_penalty
                else:
                    # No sign out penalty
                    ded_applied = penalty_rule.no_sign_out
                    type = 'no_signout'
                    deduction = ded_applied * per_hour
                    self.create_line(key, 0.0, type,
                                     False, permission, permission_hrs, actual_delay, ded_applied,
                                     deduction, worked_hours, note, working, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                    continue

                    # WORKED HOURS
                if sign_in and sign_out:
                    #                     worked_hours = self.calc_worked_hours(sign_out, sign_in)
                    worked_hours = self.calc_worked_hours_revised(
                        attendance_pool, key, this.employee_id.id)
                    if permission == 'yes':
                        worked_hours += permission_hrs
                        worked_hours = self.revise_shift_ends(worked_hours)
                    if leave_ids:
                        worked_hours += half_time
                        worked_hours = self.revise_shift_ends(worked_hours)

                    if worked_hours > (shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours):
                        working = shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours
                    else:
                        working = worked_hours

                # print "sign_in,sign_out : =======> ",sign_in,sign_out
                # print "singin_time,singout_time : =======> ",singin_time,singout_time
                # print "shift_starts, shift_ends : =======> ",shift_starts, shift_ends
                # print "signin_penalty,signout_penalty: =========> ",signin_penalty,signout_penalty
                # if shift_line.shift_id.rest_period_ids and not half_leave:
                #     # print "0. ****** WORKED : WORKING : -------> ", worked_hours,working
                #     working = self.consider_break_time(this.employee_id.id, key,
                #                                        shift_line.shift_id.rest_period_ids, working)
                #     # print 'BREAK ================> working-0001 ', working
                #     # print "\n1. AFTER WORKING *** WORKED : WORKING : -------> ", worked_hours,working
                #     worked_hours = self.consider_break_time(this.employee_id.id, key,
                #                                             shift_line.shift_id.rest_period_ids, worked_hours)
                #     # print 'BREAK ================> worked_hours-0001 ', worked_hours
                #     # print "2. AFTER WORKING *** WORKED : WORKING : -------> ", worked_hours, working
                #     if working and singout_time > shift_ends and working and singin_time < shift_line.shift_id.from_hours:
                #         temp = self.convert_float_to_time(shift_ends, singout_time)
                #         temp = self.revise_shift_ends(temp)
                #         temp1 = self.convert_float_to_time(singin_time, shift_line.shift_id.from_hours)
                #         temp1 = self.revise_shift_ends(temp1)
                #         temp = temp + temp1
                #         temp = self.revise_shift_ends(temp)
                #         if temp < worked_hours:
                #             working = self.convert_float_to_time(temp, worked_hours)
                #             working = self.revise_shift_ends(working)
                #     else:
                #         if working and singout_time > shift_ends:
                #             if worked_hours >= 9.0 and working >= 9.0:
                #                 working = 9.0
                #             else:
                #                 extra_hours = self.get_extra_hours_shift_end(attendance_pool, key, this.employee_id,
                #                                                              shift_ends, shift_line)
                #                 #                                 temp = self.convert_float_to_time(shift_ends, singout_time)
                #                 #                                 temp = self.revise_shift_ends(temp)
                #                 if extra_hours < worked_hours:
                #                     working = self.convert_float_to_time(extra_hours, worked_hours)
                #                     working = self.revise_shift_ends(working)
                #                 # print "temp,worked_hours,workingDDDDDDDDDDDDDDDDDDDDDDDDDDDD", extra_hours,worked_hours,working
                #
                #         if working and singin_time < shift_line.shift_id.from_hours:
                #             temp = self.convert_float_to_time(singin_time, shift_line.shift_id.from_hours)
                #             temp = self.revise_shift_ends(temp)
                #             if temp < worked_hours:
                #                 working = self.convert_float_to_time(temp, worked_hours)
                #                 working = self.revise_shift_ends(working)

                # WHEN PERMISSION: REWISE SIGN IN PENALTY ONLY
                for element in permission_ids:
                    pp = element['leave']
                    per_from = pp.from_time or 0.0
                    per_to = pp.to_time or 0.0
                    halftime = self.convert_float_to_time_as_float(
                        (shift_starts) + (shift_line.shift_id.total_working_hours / 2))
                    if shift_line.shift_id.is_ramadan:
                        halftime = self.add_time(
                            [shift_line.shift_id.from_hours, (shift_line.shift_id.total_working_hours / 2)])
                    if per_from and per_to:
                        if per_from <= halftime:
                            if per_from <= shift_starts:
                                if per_to <= singin_time:
                                    signin_penalty = self.convert_float_to_time(per_to, singin_time)
                                    signin_penalty = self.revise_shift_ends(signin_penalty)
                                    # print "signin_penalty + Permission: =============>",signin_penalty
                                else:
                                    signin_penalty = 0.0
                            else:
                                if per_from >= singin_time:
                                    pass
                                else:
                                    total_hours = self.convert_float_to_time(per_from, per_to)
                                    total_hours = self.revise_shift_ends(total_hours)
                                    if total_hours <= signin_penalty:
                                        signin_penalty = self.convert_float_to_time(total_hours, signin_penalty)
                                        signin_penalty = self.revise_shift_ends(signin_penalty)
                        else:
                            if per_from <= shift_ends:
                                if per_from >= singout_time and per_to <= shift_ends:
                                    signout_penalty = self.convert_float_to_time(per_to, shift_ends)
                                    #                                     signout_penalty = self.convert_float_to_time(singout_time,per_from)
                                    signout_penalty = self.revise_shift_ends(signout_penalty)
                                    # print "Revised Permission - signout_penalty: ==================> ",signout_penalty
                                else:
                                    signout_penalty = 0.0

                # APPLY BREAK DEDUCTION
                if shift_line.shift_id.rest_period_ids:
                    self.apply_break_deduction(key, value, shift_line.shift_id, penalty_rule, per_hour)

                if not signin_penalty and not signout_penalty:
                    time_diff = 0.0
                    if halfday_leave_unpaid:
                        ded_applied = self.convert_time_to_float(halfday_leave_unpaid)
                    type = 'no_delay'
                    deduction = time_diff * per_hour
                    self.create_line(key, time_diff, type, False,
                                     permission, permission_hrs, actual_delay, ded_applied,
                                     deduction, worked_hours, note, working, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                    # print "1. : time_diff===========> ",time_diff
                elif signin_penalty and not signout_penalty:
                    time_diff = signin_penalty
                    time_diff = self.consider_addition_flexible_hours(this, key, time_diff)
                    # print(f"time_diff ====== {time_diff}")
                    actual_delay = time_diff
                    type = 'late_signin'
                    count += 1
                    ded_applied, penalty = self.check_penalty_rule_line(penalty_rule, time_diff, 'sign_in', this)
                    # print(f"dep_applied===={ded_applied}")
                    deduction = ded_applied * per_hour
                    self.create_line(key, time_diff, type, penalty,
                                     permission, permission_hrs, actual_delay, ded_applied,
                                     deduction, worked_hours, note, working, count, last_signout, allowed_nextday, first_signin, travel_alw)
                    # print "2. : signoin_penalty===========> ",time_diff
                    if halfday_leave_unpaid:
                        ded_applied = self.convert_time_to_float(halfday_leave_unpaid)
                        deduction = ded_applied * per_hour
                        note = "Half Day Leave"
                        self.create_line(key, 0.0, 'leaves', penalty,
                                         permission, permission_hrs, 0.0, ded_applied, deduction,
                                         0.0, note, 0.0, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)

                elif not signin_penalty and signout_penalty:
                    # str(int(signout_penalty)) + '.' + str(10 - int(str(signout_penalty).split('.')[1]))
                    time_diff = signout_penalty
                    actual_delay = time_diff
                    type = 'late_signout'
                    ded_applied, penalty = self.check_penalty_rule_line(penalty_rule, time_diff, 'sign_out', this)
                    if permission == 'yes':
                        if permission_hrs < time_diff:
                            actual_delay = self.convert_float_to_time(permission_hrs, time_diff)
                            actual_delay = self.revise_shift_ends(actual_delay)
                            ded_applied = self.check_penalty_rule_line(penalty_rule, actual_delay, 'sign_out')
                            # print "actual_delay: ==============> ",actual_delay
                        else:
                            actual_delay = 0.0

                            # change penalty rule now from actual delay not on time diff
                            # print "permission_hrs, ded_applied: =============> ",permission_hrs, ded_applied
                            # ded_applied, penalty = self.check_penalty_rule_line(penalty_rule, actual_delay, 'sign_out',
                            #                                                     this)

                        # print "ded_applied,actual_delay: =============> ",ded_applied,actual_delay
                        if permission_hrs < actual_delay:
                            ded_applied = self.convert_float_to_time(permission_hrs, actual_delay)
                            # print "1111ded_applied: =============> ",ded_applied
                        else:
                            # print "ded_applied, permission_hrs: ===========> ",ded_applied, permission_hrs
                            ded_applied = self.convert_float_to_time(actual_delay, permission_hrs)

                        ded_applied = self.convert_time_to_float(ded_applied)

                    deduction = ded_applied * per_hour
                    self.create_line(key, time_diff, type, penalty,
                                     permission, permission_hrs, actual_delay, ded_applied,
                                     deduction, worked_hours, note, working, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                    # print "3. : signout_penalty===========> ",time_diff
                    if halfday_leave_unpaid:
                        ded_applied = self.convert_time_to_float(halfday_leave_unpaid)
                        deduction = ded_applied * per_hour
                        note = "Half Day Leave"
                        self.create_line(key, 0.0, 'leaves', penalty,
                                         permission, permission_hrs, 0.0, ded_applied, deduction,
                                         0.0, note, 0.0, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)
                    # print "3. : signout_penalty===========> ", time_diff
                else:
                    loop = True
                    time_diff_lst = {'signin': signin_penalty, 'signout': signout_penalty}
                    count += 1
                    for k, v in time_diff_lst.items():
                        time_diff = k == 'signin' and signin_penalty or signout_penalty
                        if k == 'signin':
                            time_diff = self.consider_addition_flexible_hours(this, key, time_diff)
                        print(time_diff)

                        actual_delay = time_diff
                        type = k == 'signin' and 'late_signin' or 'late_signout'
                        action = k == 'signin' and 'sign_in' or 'sign_out'
                        ded_applied, penalty = self.check_penalty_rule_line(penalty_rule, time_diff, action, this)
                        deduction = ded_applied * per_hour
                        self.create_line(key, time_diff, type, penalty,
                                         permission, permission_hrs, actual_delay, ded_applied,
                                         deduction, worked_hours, note, working, count, last_signout, allowed_nextday, first_signin, travel_alw)
                        # print "4. : ===========> ",k,time_diff
                        # print "4. : ===========> ", k, time_diff
                    if halfday_leave_unpaid:
                        ded_applied = self.convert_time_to_float(halfday_leave_unpaid)
                        deduction = round(ded_applied * per_hour, 2)
                        note = "Half Day Leave"
                        self.create_line(key, 0.0, 'leaves',
                                         permission, permission_hrs, 0.0, ded_applied, deduction,
                                         worked_hours, note, working, 0.0, last_signout, allowed_nextday, first_signin, travel_alw)

        return True



    def apply_break_deduction(self, key, value, shift, penalty_rule, per_hour):
        #         print "key, value: ==========> ",key, value
        attendance_pool = self.env['hr.attendance']

        if len(value) == 1 or not shift.rest_period_ids:
            return True
        elif len(value) >= 2:
            value = attendance_pool.search([('id', 'in', [x.id for x in value])], order='check_in ASC')
            for index in range(0, len(value)):
                flag = False
                if index + 1 == len(value):
                    continue
                break_in = self.get_float_time(value[index].check_out)
                break_out = self.get_float_time(value[index + 1].check_in)

                for rest_period in shift.rest_period_ids:
                    rest_start = rest_period.from_period
                    rest_end = rest_period.to_period
                    if rest_start >= break_in and rest_start <= break_out or rest_end >= break_in and rest_end <= break_out:
                        flag = True
                        #                         print "rest_start,break_in: ===========> ",rest_start,rest_end,break_in,break_out
                        if rest_start > break_in:
                            break_in_penalty = self.convert_float_to_time(break_in, rest_start)
                            break_in_penalty = self.revise_shift_ends(break_in_penalty)
                            #                             print "break_in_penalty: ===========> ",break_in_penalty
                            type = 'early_breakin'
                            action = 'break_in'
                            ded_applied, penalty = self.check_penalty_rule_line(penalty_rule, break_in_penalty, action,
                                                                                self)
                            deduction = ded_applied * per_hour
                            self.create_line(key, break_in_penalty, type, penalty, 'no', 0.0,
                                             break_in_penalty, ded_applied, deduction)
                        if rest_end < break_out:
                            break_out_penalty = self.convert_float_to_time(rest_end, break_out)
                            break_out_penalty = self.revise_shift_ends(break_out_penalty)
                            #                             print "break_out_penalty: ===========> ",break_out_penalty
                            type = 'late_breakout'
                            action = 'break_out'
                            ded_applied, penalty = self.check_penalty_rule_line(penalty_rule, break_out_penalty, action,
                                                                                self)

                            deduction = ded_applied * per_hour
                            self.create_line(key, break_out_penalty, type, penalty, 'no', 0.0,
                                             break_out_penalty, ded_applied, deduction)
                    if not flag:
                        #                     print "break_in, break_out: ==========> ",break_in, break_out
                        break_in_penalty = self.convert_float_to_time(break_in, break_out)
                        break_in_penalty = self.revise_shift_ends(break_in_penalty)
                        type = 'early_breakin'
                        action = 'break_in'
                        ded_applied, penalty = self.check_penalty_rule_line(penalty_rule, break_in_penalty, action, self)
                        deduction = ded_applied * per_hour
                        self.create_line(key, break_in_penalty, type, penalty, 'no', 0.0,
                                         break_in_penalty, ded_applied, deduction)
    def add_time(self, x):
        ''' WHERE X is list of time as float '''
        if not x: return 0.0
        y = []
        for element in x:
            hours = str(element).split('.')[0]
            mins = str(element).split('.')[1]
            if len(hours) == 1:
                hours = '0' + hours
            if len(mins) == 1:
                mins = mins + '0'
            element = str(hours) + '.' + str(mins)
            y.append(element)

        timeList = [str(x).replace('.', ':') + ':00' for x in y]

        totalSecs = 0
        for tm in timeList:
            timeParts = [int(s) for s in tm.split(':')]
            totalSecs += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
        totalSecs, sec = divmod(totalSecs, 60)
        hr, min = divmod(totalSecs, 60)
        res = "%d.%02d" % (hr, min)
        #         print "TIME TOTAL: =======================> ",res
        return float(res)


    def revise_shift_ends(self, float_val):
        hours = str(float_val).split('.')[0]
        mins = str(float_val).split('.')[1]
        if len(mins) == 1:
            mins = mins + '0'
        if int(mins) == 60:
            hours = int(hours) + 1
            mins = 0
        elif int(mins) > 60:
            hours = int(hours) + 1
            mins = int(mins) - 60
            if mins < 10:
                mins = '0' + str(mins)
        else:
            return float_val
        float_val = float(str(hours) + '.' + str(mins))
        return float_val

    def check_penalty_rule_line(self, penalty_rule, time_diff, action, this):
        deduction_hour = 0.0
        penalty_line_pool = self.env['hr.penalty.line']
        edl_line_pool = self.env['employee.delay.line']
        if action in ['sign_in', 'break_out']:
            el_temp = 'late'
        else:
            el_temp = 'early'
        hours = int(str(time_diff).split('.')[0])
        minits = str(time_diff).split('.')[1]
        minits = len(minits) == 1 and minits + '0' or minits
        if hours:
            minits = str((hours * 60) + (int(minits)))
        else:
            minits = str(time_diff).split('.')[1]

        minits = len(str(minits)) == 1 and str(minits) + '0' or minits
        penalty_id = False
        for line in penalty_rule:
            penalty_id = line
        penalty_line_ids = penalty_line_pool.search([
            ('penalty_id', '=', penalty_id.id),
            ('action', '=', action),
            ('late_early', '=', el_temp),
            ('from_min', '<=', int(minits)),
            ('to_min', '>=', int(minits))])
        if not penalty_line_ids:
            penalty_line_ids = penalty_line_pool.search([
                ('penalty_id', '=', penalty_id.id),
                ('late_early', '=', el_temp)], order='to_min DESC')
            if not penalty_line_ids:
                raise UserError(_('No Penalty Rule Line found.'))

        penalty_line_ids = penalty_line_ids[0]
        # penalty_line_id = self.get_edl_penalty_line_id(penalty_rule,time_diff,action)
        edl_line_ids = edl_line_pool.search([('penalty_line_id', '=', penalty_line_ids.id),
                                             ('employee_delay_id', '=', this.id)])
        if penalty_line_ids:
            if penalty_line_ids.penalty_type == 'same_delay' or not penalty_line_ids.penalty_type:
                _logger.info(f'penalty_line_ids.penalty_type ====== {penalty_line_ids.penalty_type}')
                _logger.info(f'time_diff ================= {time_diff}')
                _logger.info(f'edl_line_ids ====== {len(edl_line_ids)}')
                if time_diff and not edl_line_ids:
                    if time_diff and not edl_line_ids:
                        deduction_hour = penalty_line_ids.first_time
                elif time_diff and edl_line_ids and len(edl_line_ids) == 1:
                    deduction_hour = penalty_line_ids.second_time
                elif time_diff and edl_line_ids and len(edl_line_ids) == 2:
                    deduction_hour = penalty_line_ids.third_time
                elif time_diff and edl_line_ids and len(edl_line_ids) >= 3:
                    deduction_hour = penalty_line_ids.fourth_time
                else:
                    deduction_hour = penalty_line_ids.deduction

            # deduction_hour = float(deduction_hour)
            elif penalty_line_ids.penalty_type == 'fixed':
                deduction_hour = penalty_line_ids.deduction
        _logger.info(f'deduction_hour ====== {deduction_hour}')
        return deduction_hour, penalty_line_ids

    # def check_penalty_rule_line(self, penalty_rule, time_diff, action):
    #     penalty_line_pool = self.env['hr.penalty.line']
    #     if action in ['sign_in', 'break_out']:
    #         el_temp = 'late'
    #     else:
    #         el_temp = 'early'
    #     hours = int(str(time_diff).split('.')[0])
    #     minits = str(time_diff).split('.')[1]
    #     minits = len(minits) == 1 and minits + '0' or minits
    #     if hours:
    #         minits = str((hours * 60) + (int(minits)))
    #     else:
    #         minits = str(time_diff).split('.')[1]
    #
    #     minits = len(str(minits)) == 1 and str(minits) + '0' or minits
    #     penalty_id = False
    #     for line in penalty_rule:
    #         penalty_id = line
    #     penalty_line_ids = penalty_line_pool.search([
    #         ('penalty_id', '=', penalty_id.id),
    #         ('action', '=', action),
    #         ('late_early', '=', el_temp),
    #         ('from_min', '<=', int(minits)),
    #         ('to_min', '>=', int(minits))])
    #     if not penalty_line_ids:
    #         penalty_line_ids = penalty_line_pool.search([
    #             ('penalty_id', '=', penalty_id.id),
    #             ('late_early', '=', el_temp)], order='to_min DESC')
    #         print('penalty_line_ids ************ ', penalty_line_ids)
    #         if not penalty_line_ids:
    #             raise UserError(_('No Penalty Rule Line found.'))
    #
    #     penalty_line_ids = penalty_line_ids[0]
    #     if penalty_line_ids.penalty_type == 'same_delay':
    #         hours = int(int(minits) / 60)
    #         minits = int(minits) - (hours * 60)
    #         print('MINUTS ', minits)
    #
    #         temp = str((minits * 100) / 60)
    #         print('***** DEDUCTION1111 ****** ', hours, '  ', temp)
    #         if len(temp) == 1:
    #             temp = '0%s' % temp
    #         print('***** DEDUCTION ****** ', type(hours), '  ', type(temp))
    #         deduction_hour = float(str(hours) + '.' + temp.replace('.', ''))
    #         # deduction_hour = float(deduction_hour)
    #     else:
    #         deduction_hour = penalty_line_ids.deduction
    #     return deduction_hour

    def check_penalty_absent_rule_line(self, penalty_rule, count):
        deduction_hour = 0.0
        penalty_absent_line_pool = self.env['hr.penalty.absent.line']

        for line in penalty_rule:
            penalty_id = line
        absent_line_ids = penalty_absent_line_pool.search([
            ('penalty_id', '=', penalty_id.id)])
        if absent_line_ids:
            absent_line_ids = absent_line_ids[0]
            # print('penalty_linnnnnnnnnes ==== ',absent_line_ids.penalty_id.name)
            if count == 1:
                deduction_hour = absent_line_ids.first_time
            elif count == 2:
                deduction_hour = absent_line_ids.second_time
            elif count == 3:
                deduction_hour = absent_line_ids.third_time
            elif count >= 4:
                deduction_hour = absent_line_ids.fourth_time

            return deduction_hour

    def convert_time_to_float(self, timeasfloat):
        hours = str(timeasfloat).split('.')[0]
        minits = str(timeasfloat).split('.')[1]
        if len(minits) == 1:
            minits = '%s0' % minits
        minits = str(int(minits) / 60)
        float_val = float(hours) + float(minits)
        return float_val

    def convert_float_to_time_as_float(self, float_val):
        str_float_val = str(float_val)
        hrs = str_float_val.split('.')[0]
        mins = str_float_val.split('.')[1]

        if len(mins) == 1:
            mins = mins + '0'
        mins = str((int(mins) * 60) / 100)
        mins = len(mins) == 1 and mins + '0' or mins
        print('mins ============== ', float(hrs), float(mins))

        result = str(hrs) + '.' + str(mins)
        print('result = ', type(hrs), type(mins), '==== ', result, type(result))
        return float(result)

    def consider_addition_flexible_hours(self, this, key, time_diff):
        employee_delay_line_pool = self.env['employee.delay.line']
        # GET PREVIOUS DATA DATA
        allowed_time = self.get_previous_day_allowed_time(employee_delay_line_pool, this.id, key)

        if allowed_time and time_diff:
            if time_diff >= allowed_time:
                time_diff = self.convert_float_to_time(allowed_time, time_diff)
                time_diff = self.revise_shift_ends(time_diff)
            else:
                time_diff = 0.0
        return time_diff

    def convert_float_to_time_as_float1(self, float_val):
        if float_val == 2.5:
            float_val = 2.30
        if float_val == 2.25:
            float_val = 2.15

        if float_val == 3.5:
            float_val = 3.30
        if float_val == 3.25:
            float_val = 3.15

        if float_val == 4.5:
            float_val = 4.30
        if float_val == 4.25:
            float_val = 4.15

        if float_val == 5.5:
            float_val = 5.30
        if float_val == 5.25:
            float_val = 5.15

        if float_val == 6.5:
            float_val = 6.30
        if float_val == 6.25:
            float_val = 6.15

        if float_val == 7.5:
            float_val = 7.30
        if float_val == 7.25:
            float_val = 7.15

        if float_val == 8.5:
            float_val = 8.30
        if float_val == 9.5:
            float_val = 9.30
        if float_val == 10.5:
            float_val = 10.30
        if float_val == 11.5:
            float_val = 11.30
        if float_val == 12.5:
            float_val = 12.30
        if float_val == 13.5:
            float_val = 13.30
        if float_val == 14.5:
            float_val = 14.30
        if float_val == 15.5:
            float_val = 15.30
        return float_val

    def create_line(self, date, time_diff, type, penalty,
                    permisssion='no', permission_hours=0.0, actual_delay=0.0,
                    ded_applied=0.0, deduction=0.0, worked_hours=0.0, note=False, working=0.0, count=0.0,
                    last_signout='00:00:00', allowed_nextday=0.0, first_signin='00:00:00', travel_alw=0.0):
        employee_delay_line_pool = self.env['employee.delay.line']
        _logger.info(f'create_line penalty ============= {penalty}')
        employee_delay_line_data = {
            'employee_delay_id': self.id,
            'date': date,
            'time_diff': time_diff,
            'type': type,
            'permission': permisssion,
            'permission_hours': permission_hours,
            'actual_delay': actual_delay,
            'ded_applied': ded_applied,
            'deduction': deduction,
            'worked_hours': worked_hours,
            'working': working,
            'note': note,
            'count': count,
            'last_signout': last_signout,
            'allowed_nextday': allowed_nextday,
            'first_signin': first_signin,
            'odd_action': self.create_line_hook(self.id, date),
            'travel_alw': travel_alw,
            'penalty_line_id': penalty and penalty.id or False,
        }
        edl_id = employee_delay_line_pool.create(employee_delay_line_data)
        return edl_id

    def create_line_hook(self, employee_delay_id, key):
        att_pool = self.env['hr.attendance']
        odd_action = True
        employee_delay = self.browse(employee_delay_id)
        employee_id = employee_delay.employee_id.id
        in_att_ids = att_pool.search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', key + ' 00:00:00'),
            ('check_in', '<=', key + ' 23:59:59')], order="check_in ASC")
        out_att_ids = att_pool.search([
            ('employee_id', '=', employee_id),
            ('check_out', '>=', key + ' 00:00:00'),
            ('check_out', '<=', key + ' 23:59:59')], order="check_out ASC")
        if len(in_att_ids) == len(out_att_ids):
            odd_action = False
        return odd_action

    def get_previous_day_allowed_time(self, employee_delay_line_pool, employee_delay_id, date):
        import datetime
        allowed_time = 0.0
        date_strptime = (datetime.datetime.strptime(date.split(' ')[0], '%Y-%m-%d'))
        day_before = (date_strptime + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
        previous_day_ids = employee_delay_line_pool.search([('employee_delay_id', '=', employee_delay_id),
                                                            ('date', '=', day_before)])
        # print(f" previous days ids ======= {previous_day_ids.allowed_nextday}")
        if previous_day_ids:
            # allowed_time = employee_delay_line_pool.browse(previous_day_ids[0]).allowed_nextday
            allowed_time = sum(previous_day_ids.mapped("allowed_nextday"))
            # print(f" allowed_time ======= {allowed_time}")
        return allowed_time


    def get_next_day_allowed_time(self, attendance_pool, this, key,
                                  penalty_rule):
        first_signin = "00:00:00"
        last_signout = "00:00:00"
        allowed_nextday = 0.0
        last_att_ids = attendance_pool.search([
            ('employee_id', '=', this.employee_id.id),
            ('check_out', '>=', key + ' 00:00:01'),
            ('check_out', '<=', key + ' 23:59:59')], order="check_out DESC")
        # print(f"Last Attendance === > {last_att_ids}")
        first_att_ids = attendance_pool.search([
            ('employee_id', '=', this.employee_id.id),
            ('check_in', '>=', key + ' 00:00:01'),
            ('check_in', '<=', key + ' 23:59:59')], order="check_in ASC")
        # time_zone = context.has_key("tz") and context['tz'] or "Africa/Cairo" if context else "Africa/Cairo"
        # print(f"First Attendance === > {first_att_ids}")
        if first_att_ids:
            sign_date = first_att_ids[0].check_in
            # print(f"First sign_date === > {sign_date}")
            sign_date = self.convert_datetime_to_tz(sign_date)
            first_signin = sign_date.split(' ')[1]
        if last_att_ids:
            temp_date = last_att_ids[0].check_out
            temp_date = self.convert_datetime_to_tz(temp_date)
            last_signout = temp_date.split(' ')[1]
            temp_lastout = float(last_signout[:5].replace(':', '.'))
            flex_pool = self.env["additional.flexible.hours"]
            flex_ids = flex_pool.search([('penalty_id', '=', penalty_rule.id),
                                                  ('from_time', '<=', temp_lastout),
                                                  ('to_time', '>=', temp_lastout)])
            if flex_ids:
                allowed_nextday = flex_ids[0].flex_hours
        return [last_signout, allowed_nextday, first_signin]

    def get_float_time(self, str_date):
        return float(str(str_date).split(' ')[1][:5].replace(':', '.'))

    def check_approved_leave(self, employee_id, date):
        import datetime
        date_list = []
        special_dates = []
        holiday_pool = self.env['hr.leave']
        holiday_ids = holiday_pool.search(
            [('employee_id', '=', employee_id),
             ('state', '=', 'validate'),
             ('date_from', '<=', date),
             ('date_to', '>=', date)], order="date_from ASC")
        # print(f'check_approved_leave.holiday_ids ================ {holiday_ids}')

        if holiday_ids:
            date_format = '%Y-%m-%d'
            next_day = (datetime.datetime.strptime(str(date), date_format) + \
                        datetime.timedelta(days=1)).strftime(date_format)
            date_list = self.generate_date_dic(holiday_ids[0].date_from.strftime(date_format).split(' ')[0],
                                               holiday_ids[0].date_to.strftime(date_format).split(' ')[0],
                                               date_format)  # context.update({'date_list': date_list})
            # print(f'check_approved_leave.date_list ===== {date_list}')
            special_dates = list(set(special_dates + date_list))
            # print(f'check_approved_leave.special_dates ================ {special_dates}')
        return {'holiday_ids': holiday_ids, 'date_list': date_list}

    def check_permission_leave(self, employee_id, date):
        import datetime
        holiday_pool = self.env['hr.leave']
        permission_ids = holiday_pool.search(
            [('employee_id', '=', employee_id),
             ('state', '=', 'validate'),
             ('date_from', '>=', date + ' 00:00:00'),
             ('date_from', '<=', date + ' 23:59:59'),
             ('holiday_status_id.appear_time_field', '=', True),
             ('holiday_status_id.unpaid', '=', False)], order="date_from ASC")
        return permission_ids

    def generate_date_dic(self, start_date, end_date, date_format):
        if start_date and end_date:
            import datetime
            start = datetime.datetime.strptime(str(start_date), date_format)
            end = datetime.datetime.strptime(str(end_date), date_format)
            date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days + 1)]
            date_list = []
            for date in date_generated:
                date_list.append(date.strftime(date_format))
        return date_list

    def get_target_working_hours(self, employee_id, date_from, date_to):
        assign_shift_line_pool = self.env['assign.shift.line']
        holiday_pool = self.env['hr.leave']
        patch_delay_cal_pool = self.env['patch.delay.cal']

        date_list = self.generate_date_dic(date_from, date_to, "%Y-%m-%d")
        shift_hours = 0.0
        shift_line_ids = patch_delay_cal_pool.get_employee_shift(employee_id, date_from, date_to)

        for shift_line in shift_line_ids:
            if shift_line.start_from <= date_from and shift_line.to_date >= date_to:
                date1 = date_from
                date2 = date_to
            elif shift_line.start_from <= date_from and shift_line.to_date <= date_to:
                if shift_line.start_from.split('-')[1] == date_from.split('-')[1]:
                    date1 = date_from
                    date2 = shift_line.to_date
                else:
                    continue
            elif shift_line.start_from >= date_from and shift_line.to_date <= date_to:
                date1 = shift_line.start_from
                date2 = shift_line.to_date
            elif shift_line.start_from >= date_from and shift_line.to_date >= date_to:
                date1 = shift_line.start_from
                date2 = date_to
            #             print "date1:date2 =======> ",date1,date2

            workingdays = 0
            leave = 0
            shift_hours = 0
            date_format = "%Y-%m-%d"
            from_date = datetime.strptime(str(date1), date_format)
            to_date = datetime.strptime(str(date2), date_format)

            # find employee's approved leave
            holiday_ids = holiday_pool.search(
                [('employee_id', '=', employee_id),
                 ('state', '=', 'validate'),
                 ('date_from', '>=', str(date_from) + ' 00:00:01'),
                 ('date_from', '<=', str(date_to) + ' 23:59:59')])
            if holiday_ids:
                for holiday in holiday_pool.browse(holiday_ids):
                    leave += holiday.number_of_days_temp

            day_data = self.count_weekdays(from_date, to_date)
            #             print "day_data: ========> ",day_data
            rest_days = [x.name for x in shift_line.rest_days]
            #             print "rest_days: ========> ",rest_days
            for k, v in day_data.items():
                if k not in rest_days:
                    workingdays += v
            #             print "workingdays: ==> ",workingdays,leave
            if 'substract_holidays' in self.env.context and self.env.context.get('substract_holidays'):
                leave = 0
            workingdays = workingdays - leave

            day_hours = shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours
            shift_hours += workingdays * day_hours
        #             print "shift_hours = workingdays * day_hours: ===> ",workingdays,day_hours
        return shift_hours

    def calc_worked_hours_revised(self, att_pool, key, employee_id):
        worked_hours = 0.0
        in_att_ids = att_pool.search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', key + ' 00:00:01'),
            ('check_in', '<=', key + ' 23:59:59')], order="check_in ASC")
        out_att_ids = att_pool.search([
            ('employee_id', '=', employee_id),
            ('check_out', '>=', key + ' 00:00:01'),
            ('check_out', '<=', key + ' 23:59:59')], order="check_out DESC")
        if len(in_att_ids) == len(out_att_ids):
            for x in range(0, len(in_att_ids)):
                date_format = '%Y-%m-%d %H:%M:%S'
                out_time = float(out_att_ids[x].check_out.strftime(date_format).split(' ')[1][:5].replace(':', '.'))
                in_time = float(in_att_ids[x].check_in.strftime(date_format).split(' ')[1][:5].replace(':', '.'))
                if in_time <= out_time:
                    time_diff = self.convert_float_to_time(in_time, out_time)
                    time_diff = self.revise_shift_ends(time_diff)
                    worked_hours += time_diff
        worked_hours = self.revise_shift_ends(worked_hours)
        return worked_hours

    def get_employee_per_hour_rate(self, employee_id, date_from, date_to,
                                   has_ramadan=False):
        patch_delay_cal_pool = self.env['patch.delay.cal']
        assign_shift_line_ids = patch_delay_cal_pool.get_employee_shift(employee_id.id, date_from, date_to)
        print(f"assign_shift_line_ids ====> {assign_shift_line_ids}")
        if not assign_shift_line_ids:
            raise UserError(_('Employee %s has no assigned shifts in period from %s To %s.' % (
                employee_id.name, date_from, date_to)))
        # print(f"shift line Ids ======= {assign_shift_line_ids}")
        shift_line = assign_shift_line_ids
        per_hour = 0.0
        contract = self.get_employee_contract(employee_id)
        if contract:
            if not has_ramadan:
                if contract.special_month:
                    month_line_pool = self.env['month.line']
                    month_line_ids = month_line_pool.search([
                        ('contract_id.employee_id', '=', employee_id.id),
                        ('contract_id.state', 'in', ['draft', 'open']),
                        ('contract_id.special_month', '=', True),
                        ('date_from', '<=', date_from),
                        ('date_to', '>=', date_to)])
                    if not month_line_ids:
                        raise UserError(_("No Special Month Configured found for employee %s's Contract of date %s." % (
                            employee_id.name, date_from)))
                    per_hour = month_line_ids[0].per_hour
                else:
                    # per_hour = contract.gross and (contract.gross / (22 * shift_line.shift_id.total_working_hours))
                    # or 0.0#Assuming 22 day of a month
                    per_hour = contract.gross and (contract.gross /
                                                   (
                                                           22 * (
                                                           shift_line.shift_id.total_working_hours - shift_line.shift_id.break_hours))) or 0.0  # Assuming 22 day of a month
            else:
                total_target = self.get_target_working_hours(employee_id.id,
                                                             date_from, date_to)
                per_hour = contract.wage and (contract.wage / total_target) or 0.0
        else:
            per_hour = 0.0
        return round(per_hour, 2)

    # def get_employee_per_hour_rate(self, employee_id, date_from, date_to,
    #                                has_ramadan=False):
    #
    #     per_hour = 0.0
    #     patch_delay_cal_pool = self.env['patch.delay.cal']
    #     assign_shift_line_pool = self.env['assign.shift.line']
    #
    #     date_list = self.generate_date_dic(date_from, date_to, "%Y-%m-%d")
    #     shift_hours = []
    #     for date in date_list:
    #         # print(f"date =====> {date}")
    #         shift_line_ids = patch_delay_cal_pool.get_employee_shift(employee_id.id, date, date)
    #         # print(f"shift_line_ids ====> {shift_line_ids}")
    #         if shift_line_ids:
    #             shift_line = shift_line_ids[0]
    #             shift_hours.append(shift_line.shift_id.total_working_hours)
    #
    #     total_hours = self.add_time(shift_hours)
    #     contract = self.get_employee_contract(employee_id)
    #     if contract:
    #         if not has_ramadan:
    #             per_hour = contract.wage and (contract.wage / 198) or 0.0
    #         else:
    #             total_target = self.get_target_working_hours(employee_id.id,
    #                                                          date_from, date_to)
    #             per_hour = contract.wage and (contract.wage / total_target) or 0.0
    #     else:
    #         per_hour = 0.0
    #     return round(per_hour, 2)

    def convert_float_to_time(self, s1, s2):
        from datetime import datetime
        #         print "s1, s2: ======> ",s1, s2,type(s1),type(s2)
        s1_str0 = len(str(s1).split('.')[0]) == 1 and '0' + str(s1).split('.')[0] or str(s1).split('.')[0]
        s1_str1 = len(str(s1).split('.')[1]) == 1 and str(s1).split('.')[1] + '0' or str(s1).split('.')[1]
        s2_str0 = len(str(s2).split('.')[0]) == 1 and '0' + str(s2).split('.')[0] or str(s2).split('.')[0]
        s2_str1 = len(str(s2).split('.')[1]) == 1 and str(s2).split('.')[1] + '0' or str(s2).split('.')[1]

        s1_str = s1_str0 + '.' + s1_str1
        s2_str = s2_str0 + '.' + s2_str1
        #         print "XXX: ====> ",s1_str0,s1_str1,s2_str0,s2_str1,s1_str,s2_str

        s1 = s1_str.split('.')[0] + ':' + s1_str.split('.')[1] + ':00'
        s2 = s2_str.split('.')[0] + ':' + s2_str.split('.')[1] + ':00'
        #         print "s1, s2: ============> ",s1, s2

        FMT = '%H:%M:%S'
        tdelta = str(datetime.strptime(str(s2), FMT) - datetime.strptime(str(s1), FMT))
        tdelta = tdelta.split(':')[0] + '.' + tdelta.split(':')[1]
        #         print "tdelta: =========> ",tdelta
        return float(tdelta)

    def count_weekdays(self, start_date, end_date):
        if start_date and end_date:
            rule = rrule.rrule(rrule.DAILY,
                               dtstart=start_date,
                               until=end_date)
            day_data = dict(Counter(d.strftime('%A') for d in rule))
        return day_data


class res_company(models.Model):
    _inherit = "res.company"
    altern_si_so = fields.Boolean('Altern Sign In-Out',
                                  help="""checked if Altern Sign In-Out constraint to be considered.\n
          Sign in (resp. Sign out) must follow Sign out (resp. Sign in)""")
