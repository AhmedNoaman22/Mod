import datetime, time
import calendar
from odoo.tools.translate import _
from odoo.exceptions import UserError, AccessError, ValidationError
import math
from odoo import tools
from odoo import SUPERUSER_ID
from odoo import fields, api, models
import logging
from odoo.tools import float_compare, float_round, float_repr

_logger = logging.getLogger(__name__)

HOURS_PER_DAY = 8


def add_time(x):
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
    return float(res)


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    emergency = fields.Boolean('Emergency')
    appear_time_field = fields.Boolean('Appear Time Field')
    # unpaid = fields.Boolean('Unpaid')
    can_be_req_before = fields.Integer('Can be Requested before')
    can_be_req_after = fields.Integer('Can be Requested After')
    is_permission = fields.Boolean()
    no_deduction_applied = fields.Boolean()


class hr_employee(models.Model):
    _inherit = "hr.employee"

    monthly_permission = fields.Float('Total Monthly Permission')
    monthly_permission_taken = fields.Float('Total Permission Taken')
    remaining_permission = fields.Float('Remaining Monthly Permission')

    def action_permission_balance(self):
        domain = [('active', '=', True)]
        employee_ids = self.search(domain)
        for employee in employee_ids:
            ctx = self.env.context.copy()
            ctx['cron'] = True
            employee.with_context(ctx).calc_permission_balance()
        return True

    def calc_permission_balance(self):
        rule_pool = self.env['hr.holidays.status.rules']
        holiday_pool = self.env['hr.leave']
        DATE_FORMAT = "%Y-%m-%d"
        year = time.strftime("%Y")
        month = time.strftime("%m")
        last_day = calendar.monthrange(int(year), int(month))[1]
        month_start = year + '-' + month + '-' + '01'
        month_end = year + '-' + month + '-' + str(last_day)
        for employee in self:
            _logger.info("[Permission Balance Scheduler] Calculating Permission for %s" % (employee.name))
            # Total Montly Permissions Hour Based
            domain = [('max_or_min_times', '=', 'total'),
                      ('unit', '=', 'hours'),
                      ('per', '=', 'monthly'),
                      ('holiday_status_id.appear_time_field', '=', True)]
            rule_ids = rule_pool.search(domain)
            if rule_ids:
                total_permission = sum([x.no for x in rule_ids])
            else:
                total_permission = 0.0

            # Remaning Permission Hours
            domain = [('appear_time_field', '=', True),
                      ('state', 'in', ['confirm', 'validate1', 'validate']),
                      ('employee_id', '=', employee.id),
                      ('date_from', '>=', month_start + ' 00:00:01'),
                      ('date_to', '<=', month_end + ' 23:23:59'), ]
            holiday_ids = holiday_pool.search(domain)
            if holiday_ids:
                monthly_permission_taken = 0.0
                for holiday in holiday_ids:
                    if holiday.date_from.strftime(DATE_FORMAT).split(' ')[0].split('-')[0] == \
                            holiday.date_to.strftime(DATE_FORMAT).split(' ')[0].split('-')[0]:
                        monthly_permission_taken = add_time([monthly_permission_taken, holiday.total_hours])
                    else:
                        days = len(holiday_pool.generate_date_dic(holiday.date_from.strftime(DATE_FORMAT),
                                                                  holiday.date_to.strftime(DATE_FORMAT), DATE_FORMAT))
                        monthly_permission_taken += (holiday.total_hours * days)
                monthly_permission_taken = holiday_pool.revise_time(monthly_permission_taken)
            else:
                monthly_permission_taken = 0.0

            if total_permission > monthly_permission_taken:
                remaining_permission = total_permission - monthly_permission_taken
                remaining_permission = holiday_pool.convert_float_to_time(monthly_permission_taken, total_permission)
                remaining_permission = holiday_pool.revise_time(remaining_permission)
            else:
                remaining_permission = 0.0

            if 'cron' in self._context and self._context.get('cron'):
                employee.monthly_permission = total_permission
                employee.monthly_permission_taken = monthly_permission_taken
                employee.remaining_permission = remaining_permission
        return remaining_permission


class hr_leave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('date_from', 'date_to', 'employee_id', 'holiday_status_id')
    def _check_date(self):
        for holiday in self:
            if not holiday.holiday_status_id.appear_time_field:
                domain = [
                    ('date_from', '<=', holiday.date_to),
                    ('date_to', '>=', holiday.date_from),
                    ('employee_id', '=', holiday.employee_id.id),
                    ('id', '!=', holiday.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                ]
                nholidays = self.search_count(domain)
                if nholidays:
                    raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))

    holiday_type = fields.Selection([('employee', 'By Employee'),
                                     ('category', 'By Employee Tag'),
                                     ('company', 'Company'),
                                     ('department', 'By Department')],
                                    string='Allocation Mode',
                                    readonly=True, required=True,
                                    states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    remaining_permission = fields.Float(string='Remaining Permission')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.remaining_permission = False
        if self.employee_id:
            self.remaining_permission = self.employee_id.calc_permission_balance()

    def action_approve(self):
        res = super(hr_leave, self).action_approve()
        for holiday in self:
            # Own Leave should not be Validated by user
            if self._uid != SUPERUSER_ID and holiday.employee_id.user_id and holiday.employee_id.user_id.id == self._uid:
                raise UserError(_('Officer/Manager can not approve their own Leave request.'))
        return res

    def action_validate(self):
        res = super(hr_leave, self).action_validate()
        for record in self:
            if self._uid != SUPERUSER_ID and record.employee_id.user_id and record.employee_id.user_id.id == self._uid:
                raise UserError(_('Officer/Manager can not approve their own Leave request.'))
        return res

    def generate_date_dic(self, start_date, end_date, date_format):
        if start_date and end_date:
            import datetime
            start = datetime.datetime.strptime(start_date, date_format)
            end = datetime.datetime.strptime(end_date, date_format)
            if int((end - start).days) == 0:
                temp = (end - start).days + 2
            else:
                temp = (end - start).days + 1
            date_generated = [start + datetime.timedelta(days=x) for x in range(0, temp)]
            date_list = []
            for date in date_generated:
                date_list.append(date.strftime(date_format))
        return date_list


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    monthly_permission = fields.Float('Total Monthly Permission', readonly=True, )
    monthly_permission_taken = fields.Float('Total Permission Taken', readonly=True, )
    remaining_permission = fields.Float('Remaining Monthly Permission', readonly=True, )
