# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    hour_cost = fields.Float(string='Hour Cost')
    multiplier_percentage = fields.Float(string='Multiplier (%) Percentage', copy=False, store=True)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # planning_time = fields.Float(string='Planning Time', readonly=True)
    department_line_ids = fields.One2many(comodel_name='department.line', inverse_name='task_id',
                                          string="Department Line")

    department_id = fields.Many2one(comodel_name='hr.department', string="Department")

    # lock_timesheet = fields.Boolean(string="Lock Timesheet")

    # @api.onchange('department_line_ids')
    # def calc_planning_time_for_task(self):
    #     for rec in self:
    #         lines = rec.department_line_ids
    #         amount = 0.0
    #         if lines:
    #             for line in lines:
    #                 amount += line.department_hour
    #         rec.planning_time = amount


class DepartmentLine(models.Model):
    _name = 'department.line'
    _description = 'department line'

    name = fields.Char(string='Name', required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string="Department", required=True)
    department_hour = fields.Float(string='Department Hour', required=True)
    task_id = fields.Many2one(comodel_name='project.task', string="Task")


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    # Added for recalculate amount of timesheet selected called in server action
    def recalculate(self):
        sudo_self = self.sudo()  # this creates only one env for all operation that required sudo()
        for timesheet in sudo_self:
            if timesheet.employee_id:
                cost = timesheet._hourly_cost()
                amount = -timesheet.unit_amount * cost
                amount_converted = timesheet.employee_id.currency_id._convert(
                    amount, timesheet.account_id.currency_id or timesheet.currency_id, self.env.company, timesheet.date)
                timesheet_record = self.env['account.analytic.line'].search([('id','=',timesheet.id)])
                timesheet_record.sudo().update({
                    'amount': amount_converted,
                })
                print(f"amount of timesheet ====> {timesheet_record.amount}")

    # def create(self, vals_list):
    #     res = super(AccountAnalyticLine, self).create(vals_list)
    #     print('=========== vals_list ', vals_list)
    #     if isinstance(vals_list, dict):
    #         if vals_list and vals_list['task_id']:
    #             task_id = vals_list['task_id']
    #             task_obj_val = self.env['project.task'].browse(task_id)
    #             if task_obj_val:
    #                 if task_obj_val.lock_timesheet:
    #                     raise UserError(
    #                         _('You can not create time sheet for this task, time sheet locked for this task'))
    #     else:
    #         for line in vals_list:
    #             if line and line['task_id']:
    #                 task_id = line['task_id']
    #                 task_obj_val = self.env['project.task'].browse(task_id)
    #                 if task_obj_val:
    #                     if task_obj_val.lock_timesheet:
    #                         raise UserError(
    #                             _('You can not create time sheet for this task, time sheet locked for this task'))
    #     return res

    # @api.onchange('task_id', 'unit_amount')
    # def get_time_sheet_for_task(self):
    #     if self.task_id:
    #         task_id = self.task_id
    #         line_ids = self.env['account.analytic.line'].sudo().search([('task_id', '=', task_id.id)])
    #         hours = 0.0
    #         for line in line_ids:
    #             hours += line.unit_amount
    #         print('========== Task id =====', line_ids)
    #         print('======== hours', hours)
    #         if hours > task_id.planning_time:
    #             raise UserError(
    #                 _('You can not add time sheet for this task'))
