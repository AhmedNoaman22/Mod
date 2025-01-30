from odoo import api, fields, models, _
from odoo.exceptions import UserError


class hr_contract(models.Model):
    _inherit = "hr.contract"

    gross = fields.Monetary('Gross', digits=(16, 2), required=True, help="Employee's monthly gross wage.")
    basic_insurance = fields.Float('Basic Insurance')
    variable_insurance = fields.Float('Variable Insurance')
    holiday_start_date = fields.Date('Holiday Start Date')

    @api.constrains('employee_id', 'date_start', 'date_end')
    def check_contract(self):
        contract_ids = self.search([('employee_id', '=', self.employee_id.id),
                                    ('state', '=', 'open'),
                                    ('id', '!=', self.id)])
        if contract_ids:
            raise UserError(_('There is already open contract defined for this employee'))

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if not self.employee_id:
            return {'value': {'job_id': False}}
        emp_obj = self.employee_id
        job_id = False
        department_id = False
        if emp_obj.job_id:
            job_id = emp_obj.job_id.id
        if emp_obj.department_id:
            department_id = emp_obj.department_id.id
        return {'value': {'job_id': job_id, 'department_id': department_id}}

    # @api.onchange('wage')
    # def onchange_wage(self):
    #     res = {}
    #     if self.wage:
    #         res.update({'gross': float(self.wage)})
    #     return {'value': res}


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    can_be_taken = fields.Boolean('Can be Taken Before Holiday Date?')


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    @api.constrains('holiday_status_id', 'employee_id', 'date_from')
    def check_holiday_status(self):
        if not self.name:
            self.name = self.holiday_status_id.name
        if self.holiday_status_id.can_be_taken:
            return True

        emp_pool = self.env['hr.employee']
        contract_pool = self.env['hr.contract']
        employee_ids = []
        if self.holiday_type == 'employee':
            contract_ids = contract_pool.search([
                ('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])

            if not contract_ids:
                raise UserError(_('Please first define active contract of selected employee!'))
            if not contract_ids[0].holiday_start_date:
                raise UserError(_('Please first define holiday start date in active contract of selected employee!'))
            if self.date_from.strftime("%Y-%m-%d") <= contract_ids[0].holiday_start_date.strftime("%Y-%m-%d"):
                print('*********************** ', self.date_from.strftime("%Y-%m-%d"),
                      contract_ids[0].holiday_start_date.strftime("%Y-%m-%d"), contract_ids[0])
                raise UserError(_('You can not take this leave before holiday start date as define in your contract!'))
        elif self.holiday_type == 'category':
            employee_ids = emp_pool.search([('category_ids', 'in', [self.category_id.id]),
                                            ('state', '=', 'active')])
        elif self.holiday_type == 'department' and self.department_id:
            employee_ids = emp_pool.search([('department_id', '=', self.department_id.id),
                                            ('state', '=', 'active')])
        elif self.holiday_type == 'company':
            employee_ids = emp_pool.search([('company_id', '=', self.company_id.id),
                                            ('state', '=', 'active')])
        else:
            return True
        for employee in employee_ids:
            contract_ids = contract_pool.search([
                ('employee_id', '=', employee.id), ('state', '=', 'active')])
            if not contract_ids:
                raise UserError(_('Any of employees has no active contract!'))
            if not contract_ids[0].holiday_start_date:
                raise UserError(_('Any of employees contract has not holiday start date set in his/her contract!'))
            if self.date_from <= contract_ids[0].holiday_start_date:
                raise UserError(
                    _('Any of employees can not take leave before holiday start date defined as per his/her contract!'))
