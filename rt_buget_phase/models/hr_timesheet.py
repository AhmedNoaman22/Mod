# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'AccountAnalyticLine Inherit budget'

    # task_id = fields.Many2one(
    #     'project.task', 'Task', index='btree_not_null',
    #     compute='_compute_task_id', store=True, readonly=False, required=True,
    #     domain="[('allow_timesheets', '=', True), ('project_id', '=?', project_id), ('allow_task_timesheet', '=', False), ('parent_id.allow_task_timesheet', '=', False)]")

    hours_spent_edit = fields.Boolean(default=lambda self: True if self.env.user.has_group(
        'rt_buget_phase.group_project_task_allocated_time') else False, copy=False, compute='_compute_hours_spent_edit')

    # @api.depends('effective_hours', 'subtask_effective_hours', 'allocated_hours')
    # def _compute_remaining_hours(self):
    #     for task in self:
    #         remaining_hours = task.allocated_hours - task.effective_hours - task.subtask_effective_hours
    #         print(f"remaining_hours {remaining_hours}")
    #         if remaining_hours < 0 and not task.parent_id:
    #             raise UserError(_('yyyyy'))
    #         task.remaining_hours = remaining_hours

    @api.onchange('unit_amount', 'task_id', 'task_id.parent_id','task_id.remaining_hours')
    def _onchange_unit_amount(self, try_to_match=False):
        for rec in self:
            if rec.task_id:
                # print(f"Total remaining_hours ===> {rec.task_id.remaining_hours}")
                # if not rec.task_id.parent_id:
                #     if rec.task_id.remaining_hours < 0:
                #         raise ValidationError(_("The Hours spent mustn't exceed the Task Remaining hours."))

                if rec.task_id.parent_id:
                    print(f" total amount =====> {rec.unit_amount}")
                    print(f" rec.task_id.parent_id.remaining_hours ===> {rec.task_id.parent_id.remaining_hours}")
                    if rec.unit_amount > rec.task_id.parent_id.remaining_hours:
                        raise ValidationError(_("The Hours spent mustn't exceed the Main Task Remaining hours."))

    @api.depends('project_id')
    def _compute_hours_spent_edit(self):
        for rec in self:
            if rec.task_id.allow_task_timesheet == False and rec.project_id:
                rec.hours_spent_edit = True
                print(f"hours_spent_edit True====> {rec.hours_spent_edit}")
            else:
                rec.hours_spent_edit = False
                print(f'hours_spent_edit False =====> {rec.hours_spent_edit}')


    @api.constrains('task_id')
    def _task_timesheet_adding(self):
        for rec in self:
            user_employee_department_ids = self.env.user.employee_ids.department_id.ids
            task_assigned_users = rec.task_id.user_ids.ids
            task_parent_assigned_users = rec.task_id.parent_id.user_ids.ids
            current_user = self.env.user.id
            if rec.task_id:
                if not rec.task_id.parent_id:
                    if rec.task_id.department_id.id not in user_employee_department_ids and current_user not in task_assigned_users:
                        raise ValidationError(_("This employee can't add a time sheet for this Task As:\n"
                                                "He is not from the assigned user for this task\n"
                                                "And not from the same department tha has been selected to the Task  ."))
                    if rec.task_id.department_id:
                        if rec.employee_id.department_id != rec.task_id.department_id and current_user not in task_assigned_users:
                            raise ValidationError(_("You can't add a time sheet for this employee for this Task As:\n"
                                                    "He is not from the assigned user for this task\n"
                                                    "And not from the same department tha has been selected to the Task  ."))
                    if rec.task_id.allow_task_timesheet == True:
                        raise ValidationError(_("You can't add a time sheet for this Task As:\n"
                                                "It is not allowed for this task\n"))
                if rec.task_id.parent_id:
                    if rec.task_id.parent_id.department_id.id not in user_employee_department_ids and current_user not in task_parent_assigned_users:
                        raise ValidationError(_("This employee can't add a time sheet for this Task As:\n"
                                                "He is not from the assigned user for the Main Task\n"
                                                "And not from the same department tha has been selected to the Main Task  ."))
                    if rec.task_id.parent_id.department_id:
                        if rec.employee_id.department_id != rec.task_id.parent_id.department_id and current_user not in task_parent_assigned_users:
                            raise ValidationError(_("You can't add a time sheet for this employee for this Task As:\n"
                                                    "He is not from the assigned user for the Main task\n"
                                                    "And not from the same department tha has been selected to the Main Task  ."))
                    if rec.task_id.parent_id.allow_task_timesheet == True or rec.task_id.parent_id.parent_id.allow_task_timesheet == True:
                        raise ValidationError(_("You can't add a time sheet for this Task As:\n"
                                                "It is not allowed for this task as per Main Task\n"))

