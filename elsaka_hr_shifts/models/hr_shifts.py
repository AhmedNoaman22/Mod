# import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil import parser
import time

class hr_shifts(models.Model):
    _name = "hr.shifts"
    _description = "HR Shifts"


    @api.onchange('to_hours')
    @api.depends('from_hours','to_hours')
    def _get_total_hours(self):
        # if self.from_hours and self.to_hours and self.from_hours > self.to_hours:
        #     raise UserError(_("From Time can not be grater than To Time" ))

        str_fromhours = str(self.from_hours)
        str_tohours = str(self.to_hours)

        fromhr = str_fromhours.split('.')[0]
        frommin = str_fromhours.split('.')[1]
        tohr = str_tohours.split('.')[0]
        tomin = str_tohours.split('.')[1]

        if len(frommin) == 1:
            frommin = frommin + '0'
        if len(tomin) == 1:
            tomin = tomin + '0'

        if int(fromhr) >= 24:
            self.from_hours = False
            raise UserError(_("From Time Hours can not be equal or greater than 24." ))
        if int(tohr) >= 24:
            self.to_hours = False
            raise UserError(_("To Time Hours can not be equal or greater than 24." ))
        if frommin >= '60':
            self.from_hours = False
            raise UserError(_("From Time Minits can not be equal or greater than 60." ))
        if tomin >= '60':
            self.to_hours = False
            raise UserError(_("To Time Minits can not be equal or greater than 60." ))

        if self.from_hours and self.to_hours:
            total_working = self.convert_float_to_time(self.from_hours, self.to_hours)
            total_working = self.revise_time(total_working)
            self.total_working_hours = total_working

    name = fields.Char('Shift', required=True)
    from_hours = fields.Float('From Hours', required=True)
    to_hours = fields.Float('To Hours',required=True)
    rest_days = fields.Many2many('rest.days','rest_shift_rel','shift_id','rest_id',string='Rest Days', required=True)
    flexible_hours = fields.Float('Flexible Hours')
    total_working_hours = fields.Float(string='Total Working Hours')
    break_hours = fields.Float(string='Break Hours')
    rest_period_ids = fields.Many2many('rest.period','shift_rest_period_rel','shift_id','rest_period_id','Rest Periods')
    is_ramadan = fields.Boolean('Is ramadan?', default=lambda *a: False)

    @api.onchange('flexible_hours')
    def onchange_flexible_hours(self):
        if self.flexible_hours:
            str_flexible_hours = str(self.flexible_hours)

            flex_hrs = str_flexible_hours.split('.')[0]
            flex_mins = str_flexible_hours.split('.')[1]

            if len(flex_mins) == 1:
                flex_mins = flex_mins + '0'

            if int(flex_hrs) >= 24:
                self.flexible_hours = False
                raise UserError(_("Hours can not be equal or greater than 24." ))
            if flex_mins >= '60':
                self.flexible_hours = False
                raise UserError(_("Minits can not be equal or greater than 60." ))

    def convert_float_to_time(self, s1, s2):
        s1_str0 = len(str(s1).split('.')[0]) == 1 and '0'+str(s1).split('.')[0] or str(s1).split('.')[0]
        s1_str1 = len(str(s1).split('.')[1]) == 1 and str(s1).split('.')[1]+'0' or str(s1).split('.')[1]
        s2_str0 = len(str(s2).split('.')[0]) == 1 and '0'+str(s2).split('.')[0] or str(s2).split('.')[0]
        s2_str1 = len(str(s2).split('.')[1]) == 1 and str(s2).split('.')[1]+'0' or str(s2).split('.')[1]
        s1_str = s1_str0 + '.' + s1_str1
        s2_str = s2_str0 + '.' + s2_str1
        s1 = s1_str.split('.')[0] + ':' + s1_str.split('.')[1] + ':00'
        s2 = s2_str.split('.')[0] + ':' + s2_str.split('.')[1] + ':00'
        FMT = '%H:%M:%S'
        tdelta = str(datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT))
        tdelta = tdelta.split(':')[0] + '.' + tdelta.split(':')[1]
        return float(tdelta)

    def revise_time(self, float_val):
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

class rest_period(models.Model):
    _name = 'rest.period'
    _description = "Rest Period"

    name = fields.Char('Rest Period Name',required=True)
    from_period = fields.Float('From', required=True)
    to_period = fields.Float('To',required=True)

    @api.onchange('from_period', 'to_period')
    def onchange_periods(self):
        if self.from_period:
            str_from_period = str(self.from_period)

            flex_hrs = str_from_period.split('.')[0]
            flex_mins = str_from_period.split('.')[1]

            if len(flex_mins) == 1:
                flex_mins = flex_mins + '0'
            if int(flex_hrs) >= 24:
                self.from_period = False
                raise UserError(_("Hours can not be equal or greater than 24." ))
            if flex_mins >= '60':
                self.from_period = False
                raise UserError(_("Minits can not be equal or greater than 60." ))

        if self.to_period:
            str_to_period = str(self.to_period)

            flex_hrs = str_to_period.split('.')[0]
            flex_mins = str_to_period.split('.')[1]

            if len(flex_mins) == 1:
                flex_mins = flex_mins + '0'

            if int(flex_hrs) >= 24:
                self.to_period = False
                raise UserError(_("Hours can not be equal or greater than 24." ))
            if flex_mins >= '60':
                self.to_period = False
                raise UserError(_("Minits can not be equal or greater than 60." ))

        if self.from_period and self.to_period and self.to_period < self.from_period:
            raise UserError(_("From Time can not be grater than To Time" ))

    @api.depends('name', 'from_period', 'to_period')
    def name_get(self):
        res = []
        for period in self:
            name = period.name
            name = ' '.join([name, str(period.from_period)])
            name = ' to '.join([name, str(period.to_period)])
            res.append((period.id, name))
        return res


class rest_days(models.Model):
    _name = "rest.days"
    _description = "Rest Days"

    name= fields.Char('Name')

class assign_shift(models.Model):
    _name = 'assign.shift'
    _description = "Assign Shifts"

    name = fields.Char('Name', required=True)
    mode = fields.Selection([('employee','By Employee'),('department','By Department'),('tag','By Tag')], string='Mode', required=True)
    employee_id = fields.Many2many('hr.employee','emp_assign_rel', 'assign_id','employee_id', string='Employee')
    tag_id = fields.Many2many('hr.employee.category', 'tag_assign_rel','assign_id','tag_id', string='Tags')
    department_id = fields.Many2many('hr.department', 'dep_assign_rel','assign_id','department_id', string='Departments')
    company_id = fields.Many2many('res.company', 'comp_assign_rel','assign_id','company_id', string='Companys')
    line_ids = fields.One2many('assign.shift.line','assign_shift_id', 'Shifts')

    @api.constrains('employee_id','line_ids')
    def check_line_ids(self):
        for employee_id in self.employee_id:
            for shift in self.search([('id','!=',self.id)]):
                if employee_id.id in shift.employee_id.ids:
                    for rec in self.line_ids:
                        for line in shift.line_ids:
                            if rec.start_from > line.start_from and rec.start_from < line.to_date:
                                    raise UserError(_("This employee's shift is already defined in this duration" ))


class assign_shift_line(models.Model):
    _name = 'assign.shift.line'
    _description = "Assign Shifts Line"
    _rec_name = 'shift_id'

    assign_shift_id = fields.Many2one('assign.shift','Assign Shift')
    shift_id = fields.Many2one('hr.shifts', 'Shifts')
    rest_days = fields.Many2many('rest.days','rest_assign_rel','assign_id','rest_id',string='Rest Days')
    flexible_hours = fields.Float('Flexible Hours')
    rest_period = fields.Many2many('rest.period','assign_shift_line_rest_period_rel',
                                   'assign_shift_line_id','rest_period_id',string='Rest Period')
    start_from = fields.Date('Start From')
    to_date = fields.Date('End To')
    is_ramadan = fields.Boolean('Is Ramadan?', related='shift_id.is_ramadan', store=True)

    @api.onchange('shift_id')
    def onchange_shift_id(self):
        self.rest_days = self.shift_id.rest_days
        self.rest_period = self.shift_id.rest_period_ids
        self.flexible_hours = self.shift_id.flexible_hours

class hr_attendance(models.Model):
    _inherit = "hr.attendance"

    def get_employee_shift(self, employee_id, date_from, date_to):
        employee_pool = self.env['hr.employee']
        assign_shift_line_pool = self.env['assign.shift.line']

        #First employee shift to check
        assign_shift_line_ids = assign_shift_line_pool.search([
                                                ('start_from','<=', date_from),
                                                ('to_date','>=', date_to),
                                                ('assign_shift_id.mode','=','employee'),
                                                ('assign_shift_id.employee_id.id','in',[employee_id])])
        employee = employee_pool.browse(employee_id)
        if not assign_shift_line_ids:
            #Second check Department Shift
            if employee.department_id:
                assign_shift_line_ids = assign_shift_line_pool.search([
                    ('start_from','<=', date_from),
                    ('to_date','>=', date_to),
                    ('assign_shift_id.mode','=','department'),
                    ('assign_shift_id.department_id.id','in',[employee.department_id.id])])
        if not assign_shift_line_ids:
            #Third check Department Shift
            category_ids = [x.id for x in employee.category_ids]
            if employee.category_ids:
                assign_shift_line_ids = assign_shift_line_pool.search([
                    ('start_from','<=',date_from),
                    ('to_date','>=',date_to),
                    ('assign_shift_id.mode','=','tag'),
                    ('assign_shift_id.tag_id.id','in',category_ids)])
        return assign_shift_line_ids
