from operator import index

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    total_attendance_hour = fields.Float(string='Total Attendance Hour')
    total_time_spent = fields.Float(string='Total Time Spent', compute="_compute_total_time_spent_in_day",
                                    index=True)
    remaining_hour = fields.Float(string='Remaining Hour', compute="_compute_remaining_hour",
                                  index=True)

    @api.depends('date')
    def _compute_total_time_spent_in_day(self):
        for record in self:
            if record.date:
                current_user_employee = self.env.user.employee_id
                if not current_user_employee:
                    record.total_time_spent = 0
                    continue

                start_of_day = datetime.combine(record.date, datetime.min.time())
                end_of_day = datetime.combine(record.date, datetime.max.time())

                timesheets = self.env['account.analytic.line'].search([
                    ('date', '>=', fields.Date.to_string(start_of_day)),
                    ('date', '<=', fields.Date.to_string(end_of_day)),
                    ('employee_id', '=', current_user_employee.id)
                ])

                total_time_spent = 0.0
                for timesheet in timesheets:
                    total_time_spent += timesheet.unit_amount

                record.total_time_spent = total_time_spent

    def return_total_time_spent_in_day(self, date2):
        for record in self:
            if record.date:
                print('=========== record', self._origin.id)

                current_user_employee = self.env.user.employee_id
                if not current_user_employee:
                    record.total_time_spent = 0
                    continue

                start_of_day = datetime.combine(date2, datetime.min.time())
                end_of_day = datetime.combine(date2, datetime.max.time())

                timesheets = self.env['account.analytic.line'].search([
                    ('date', '>=', fields.Date.to_string(start_of_day)),
                    ('date', '<=', fields.Date.to_string(end_of_day)),
                    ('employee_id', '=', current_user_employee.id),
                    ('id', '!=', self._origin.id)
                ])

                print('=========== timesheets ===========', timesheets)

                total_time_spent = 0.0
                for timesheet in timesheets:
                    total_time_spent += timesheet.unit_amount

                return total_time_spent

    @api.onchange('date')
    def _compute_total_hours(self):
        for record in self:
            if record.date:
                print('========= enter here ===========')
                print('========= record.date ===========', record.date)

                current_user_employee = self.env.user.employee_id

                if not current_user_employee:
                    record.total_attendance_hour = 0
                    continue

                start_of_day = datetime.combine(record.date, datetime.min.time())
                end_of_day = datetime.combine(record.date, datetime.max.time())

                attendances = self.env['hr.attendance'].search([
                    ('check_in', '>=', fields.Datetime.to_string(start_of_day)),
                    ('check_in', '<=', fields.Datetime.to_string(end_of_day)),
                    ('employee_id', '=', current_user_employee.id)
                ])
                total_seconds = 0
                for attendance in attendances:
                    if attendance.check_in and attendance.check_out:
                        print('========== attendance.worked_hours', attendance.worked_hours)
                        total_seconds += attendance.worked_hours
                record.total_attendance_hour = total_seconds

    @api.depends('total_attendance_hour', 'total_time_spent')
    def _compute_remaining_hour(self):
        for record in self:
            record.remaining_hour = record.total_attendance_hour - record.total_time_spent

    # @api.onchange('unit_amount')
    # def _check_time_spent(self):
    #     for record in self:
    #         if record.unit_amount > record.remaining_hour:
    #             print('========== YOU CAN TIME GREATER THAN REMAINING =======')
    #             raise UserError(_('Time Spent Greater Than Remaining'))

    @api.onchange('unit_amount')
    def _check_time_spent(self):
        for record in self:
            val = record.return_total_time_spent_in_day(record.date)
            if val:
                new_val = val + record.unit_amount
                if new_val > record.total_attendance_hour:
                    raise UserError(_('Time Spent Greater Than Remaining'))
            else:
                new_val = record.unit_amount
                if new_val > record.total_attendance_hour:
                    raise UserError(_('Time Spent Greater Than Remaining'))

    # @api.model
    # def create(self, vals):
    #     res = super(AccountAnalyticLine, self).create(vals)
    #     for record in self:
    #         if record.unit_amount > record.remaining_hour:
    #             raise UserError(_('Time Spent Greater Than Remaining'))
    #     return res

    # def write(self, vals):
    #     res = super(AccountAnalyticLine, self).write(vals)
    #     for record in self:
    #         if vals.get("unit_amount"):
    #             unit_amount = vals.get("unit_amount")
    #             if unit_amount > record.remaining_hour:
    #                 raise UserError(_('Time Spent Greater Than Remaining'))
    #     return res
