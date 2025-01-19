# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
import time
import datetime as DT

class hr_holidays_status_rules(models.Model):
    _name = "hr.holidays.status.rules"
    _description = "Holidays Status Rules"

    max_or_min_times = fields.Selection([('max','Max'),('min','Min'),('total','Total')], string='Max or Min times')
    no = fields.Float('No.')
    unit = fields.Selection([('request','Request'),('minutes','Minutes'),('hours','Hours'),('day','Day')],string="Unit")
    per = fields.Selection([('request','Request'),('day','Day'),('weekly','Weekly'),('monthly','Monthly')],string="Per")
    holiday_status_id = fields.Many2one('hr.leave.type', 'Leave Type')

class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    leave_rule = fields.Selection([('null_value','Null'),('all','All'),('groups','Groups')], string='Leave Rule', default="null_value")
    rule_ids = fields.One2many('hr.holidays.status.rules','holiday_status_id', string='Rules')

class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('holiday_status_id','date_from','date_to','from_time','to_time')
    def check_leave_rules(self):
        if self.holiday_status_id.leave_rule == 'all':
            self.get_rules(self.holiday_status_id.rule_ids)
        if self.holiday_status_id.leave_rule=='groups':
            if len(self.holiday_status_id.group_rule_ids) > 1:
                group_rules_ids = self.rearrange_rule(self.holiday_status_id.group_rule_ids)
            else:
                group_rules_ids = self.holiday_status_id.group_rule_ids

            for line in group_rules_ids:
                if line.mode=='employee' and self.employee_id.id in \
                            [x.id for x in line.employee_id]:
                    self.get_rules(line.rule_ids)
                if line.mode=='department' and self.employee_id.department_id \
                            and self.employee_id.department_id.id in \
                            [x.id for x in line.department_id]:
                    self.get_rules(line.rule_ids)
                if line.mode=='tag':
                    for tag_id in self.employee_id.category_ids:
                        if tag_id.id in [x.id for x in line.tag_id]:
                            self.get_rules(line.rule_ids)

    def rearrange_rule(self, group_rule_ids):
        """ Set group rule ids such to determine the priority by 
        Employee, Department & then Tags """
        emp = []
        dep = []
        tags = []
        for x in group_rule_ids:
            if x.mode == 'employee':
                emp.append(x)
            if x.mode == 'department':
                dep.append(x)
            if x.mode == 'tag':
                tags.append(x)
        group_rules_ids = emp + dep + tags
        return group_rules_ids

    def get_rules(self, rule_ids):
        for rule in rule_ids:
            no = rule.no
            if rule.max_or_min_times=='total':
                if rule.unit == 'day':
                    if rule.per == 'request':
                        if self.number_of_days_temp > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))
                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        total_days = 0
                        for holiday in holidays:
                            total_days += holiday.number_of_days_temp
                        if total_days > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        total_days = 0
                        for holiday in holidays:
                            total_days += holiday.number_of_days_temp
                        if total_days > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))

                if rule.unit=='request':
                    if rule.per =='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        if len(holidays.ids) > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([
                                   ('holiday_status_id','=',self.holiday_status_id.id),
                                   ('employee_id','=',self.employee_id.id),
                                   ('date_from','>=',str(month_start)),
                                   ('date_from','<=',str(month_end)),
                                   ('id','!=', self.id),
                                   ])
                        if len(holidays.ids) >= rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))
                    if rule.per=='day':
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('date_from','=',self.date_from),('employee_id','=',self.employee_id.id)])
                        if len(holidays.ids) > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))

                if rule.unit=='minutes':
                    total_hours = self.convert_float_to_time(self.from_time, self.to_time)
                    total_hours= self.revise_shift_ends(total_hours)
                    total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                    if total_mins < 10:
                        total_mins = int(str(total_mins) + '0')
                    if rule.per=='request':
#                         no = rule.no / 60
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(rule.no,rule.unit))

                    if rule.per=='day':
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(rule.no,rule.unit))

                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
#                         no = rule.no / 60
                        total_hours = self.revise_shift_ends(total_hours)
                        total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                        if total_mins < 10:
                            total_mins = int(str(total_mins) + '0')
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(rule.no,rule.unit))

                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
#                         no = rule.no / 60
                        total_hours = self.revise_shift_ends(total_hours)
                        total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                        if total_mins < 10:
                            total_mins = int(str(total_mins) + '0')
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(rule.no,rule.unit))

                if rule.unit=='hours':
                    if rule.per=='request':
                        if self.total_hours > no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))
                    if rule.per=='day':
                        if self.total_hours > no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))
                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
                        if total_hours > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
                        if total_hours > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))




            if rule.max_or_min_times=='min':
                if rule.unit == 'day':
                    if rule.per == 'request':
                        if self.number_of_days_temp < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([
                               ('holiday_status_id','=',self.holiday_status_id.id),
                               ('employee_id','=',self.employee_id.id),
                               ('date_from','>=',str(week_ago)),
                               ('date_from','<=',self.date_from)])
                        total_days = 0
                        for holiday in holidays:
                            total_days += holiday.number_of_days_temp
                        if total_days < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([
                               ('holiday_status_id','=',self.holiday_status_id.id),
                               ('employee_id','=',self.employee_id.id),
                               ('date_from','>=',str(month_start)),
                               ('date_from','<=',str(month_end))])
                        total_days = 0
                        for holiday in holidays:
                            total_days += holiday.number_of_days_temp
                        if total_days > rule.no:
                            raise UserError(_("You can take leave total %s %s!")%(no,rule.unit))

                if rule.unit=='minutes':
                    total_hours = self.convert_float_to_time(self.from_time, self.to_time)
                    total_hours= self.revise_shift_ends(total_hours)
                    hrs_str = str(total_hours).split('.')[0]
                    mins_str = str(total_hours).split('.')[1]
                    if len(hrs_str) == 1:
                        hrs_str = '0' + str(total_hours).split('.')[0]
                    if len(mins_str) == 1:
                        mins_str = str(total_hours).split('.')[1] + '0'
                    total_mins = int(hrs_str) * 60 + int(mins_str)
                    if rule.per=='request':
                        if total_mins < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(rule.no,rule.unit))

                    if rule.per=='day':
                        if total_mins < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(rule.no,rule.unit))

                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([
                               ('holiday_status_id','=',self.holiday_status_id.id),
                               ('employee_id','=',self.employee_id.id),
                               ('date_from','>=',str(week_ago)),
                               ('date_from','<=',self.date_from)])
                        total_hours = 0.0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
#                         no = rule.no / 60
                        total_hours = self.revise_shift_ends(total_hours)
                        total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                        if total_mins < 10:
                            total_mins = int(str(total_mins) + '0')
                        if total_mins < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(rule.no,rule.unit))

                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([
                               ('holiday_status_id','=',self.holiday_status_id.id),
                               ('employee_id','=',self.employee_id.id),
                               ('date_from','>=',str(month_start)),
                               ('date_from','<=',str(month_end))])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
#                         no = rule.no / 60
                        total_hours = self.revise_shift_ends(total_hours)
                        total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                        if total_mins < 10:
                            total_mins = int(str(total_mins) + '0')
                        if total_mins < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(rule.no,rule.unit))

                if rule.unit=='request':
                    if rule.per =='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        if len(holidays.ids) < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        if len(holidays.ids) < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per=='day':
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('date_from','=',self.date_from),('employee_id','=',self.employee_id.id)])
                        if len(holidays.ids) < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                if rule.unit=='hours':
                    if rule.per=='request':
                        if self.total_hours < no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per=='day':
                        if self.total_hours < no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
                        if total_hours < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
                        if total_hours < rule.no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))



            if rule.max_or_min_times=='max':
                if rule.unit == 'day':
                    if rule.per == 'request':
                        if self.number_of_days_temp > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        total_days = 0
                        for holiday in holidays:
                            total_days += holiday.number_of_days_temp
                        if total_days > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        total_days = 0
                        for holiday in holidays:
                            total_days += holiday.number_of_days_temp
                        if total_days > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))

                if rule.unit=='minutes':
                    total_hours = self.convert_float_to_time(self.from_time, self.to_time)
                    total_hours= self.revise_shift_ends(total_hours)
                    total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                    if total_mins < 10:
                        total_mins = int(str(total_mins) + '0')
                    if rule.per=='request':
#                         no = rule.no / 60
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(rule.no,rule.unit))

                    if rule.per=='day':
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(rule.no,rule.unit))

                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
#                         no = rule.no / 60
                        total_hours = self.revise_shift_ends(total_hours)
                        total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                        if total_mins < 10:
                            total_mins = int(str(total_mins) + '0')
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(rule.no,rule.unit))

                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
#                         no = rule.no / 60
                        total_hours = self.revise_shift_ends(total_hours)
                        total_mins = (int(str(total_hours).split('.')[0]) * 60) + int(str(total_hours).split('.')[1])
                        if total_mins < 10:
                            total_mins = int(str(total_mins) + '0')
                        if total_mins > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(rule.no,rule.unit))

                if rule.unit=='request':
                    if rule.per =='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        if len(holidays.ids) > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        if len(holidays.ids) > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
                    if rule.per=='day':
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('date_from','=',self.date_from),('employee_id','=',self.employee_id.id)])
                        if len(holidays.ids) > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
                if rule.unit=='hours':
                    if rule.per=='request':
                        if self.total_hours > no:
                            raise UserError(_("You can take leave minimum %s %s!")%(no,rule.unit))
                    if rule.per=='day':
                        if self.total_hours > no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
                    if rule.per=='weekly':
                        week_ago = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(week_ago)),('date_from','<=',self.date_from)])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
                        if total_hours > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
                    if rule.per =='monthly':
                        month_start = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=1)).strftime('%Y-%m-%d')
                        month_end = (datetime.strptime(str(self.date_from), "%Y-%m-%d %H:%M:%S") + relativedelta(day=31)).strftime('%Y-%m-%d')
                        holidays = self.env['hr.leave'].search([('holiday_status_id','=',self.holiday_status_id.id),('employee_id','=',self.employee_id.id),('date_from','>=',str(month_start)),('date_from','<=',str(month_end))])
                        total_hours = 0
                        for holiday in holidays:
                            total_hours += holiday.total_hours
                        if total_hours > rule.no:
                            raise UserError(_("You can take leave maximum %s %s!")%(no,rule.unit))
        return True

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
                mins = '0'+str(mins)
        else:
            return float_val
        float_val = float(str(hours) + '.' + str(mins))
        return float_val