# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'
    _description = 'Project Task Inherit budget'

    # def _default_user_ids(self):
    #     return self.env.context.keys() & {'default_personal_stage_type_ids', 'default_personal_stage_type_id'} and self.env.user

    budget_id = fields.Many2one('project.budget', 'Budget',)
    department_id = fields.Many2one('hr.department', 'Department',)
    allow_task_timesheet = fields.Boolean(string='Lock Task TimeSheet', default=lambda self: True if self.parent_id.allow_task_timesheet == True else False, copy=False, store=True)
    allocated_time_edit = fields.Boolean(default=lambda self: True if self.env.user.has_group('rt_buget_phase.group_project_task_allocated_time') else False, copy=False, compute='_compute_allocated_time_edit')
    allow_task_timesheet_edit = fields.Boolean(default=lambda self: True if self.env.user.has_group('rt_buget_phase.group_hr_lock_timesheet_hours_spent') else False, copy=False, compute='_compute_allocated_time_edit')

    parent_id = fields.Many2one('project.task', string='Parent Task', index=True, domain="['!', ('id', 'child_of', id)]", tracking=True)
    child_ids = fields.One2many('project.task', 'parent_id', string="Sub-tasks", domain="[('recurring_task', '=', False)]")

    # project_id = fields.Many2one('project.project', related='parent_id.project_id', copy=False, store=True, readonly=False)
    # phase_id = fields.Many2one('project.phase', related='parent_id.phase_id', copy=False, store=True, readonly=False)
    # milestone_id = fields.Many2one('project.milestone', related='parent_id.milestone_id', copy=False, store=True, readonly=False)

    # @api.depends('parent_id')
    # def _compute_project_phase_milesone(self):
    #     for rec in self:
    #         if rec.parent_id:
    #             print(f"parent Task ===== {rec.parent_id.name}")
    #             rec.project_id = rec.parent_id.project_id.id
    #             rec.phase_id = rec.parent_id.phase_id.id
    #             rec.milestone_id = rec.parent_id.milestone_id.id

    # @api.model
    # def _default_user_ids(self):
    #     res = super(ProjectTask, self)._default_user_ids()
    #     non_users = [6, 0, []]
    #     return non_users
    #
    # user_ids = fields.Many2many('res.users', relation='project_task_user_rel', column1='task_id', column2='user_id',
    #     string='Assignees', context={'active_test': False}, tracking=True, default=_default_user_ids, domain="[('share', '=', False), ('active', '=', True)]")


    @api.depends('effective_hours', 'subtask_effective_hours', 'allocated_hours')
    def _compute_remaining_hours(self):
        for task in self:
            remaining_hours = task.allocated_hours - task.effective_hours - task.subtask_effective_hours
            print(f"remaining_hours {remaining_hours}")
            if remaining_hours < 0 and not task.parent_id:
                raise UserError(_("The Hours spent mustn't exceed the Task Remaining hours."))
            task.remaining_hours = remaining_hours

    # @api.depends('parent_id')
    # def _compute_department_assigned(self):
    #     for rec in self:
    #         if rec.parent_id:
    #             rec.department_id = rec.parent_id.department_id
    #             rec.user_ids = rec.parent_id.user_ids
    #         else:
    #             rec.department_id = False
    #             rec.user_ids = False

    @api.depends('name','parent_id')
    def _compute_allocated_time_edit(self):
        for rec in self:
            if not rec.parent_id:
                if self.env.user.has_group('rt_buget_phase.group_project_task_allocated_time') and rec.name:
                    rec.allocated_time_edit = True
                    print(f"rec.allocated_time_edit True====> {rec.allocated_time_edit}")
                else:
                    rec.allocated_time_edit = False
                    print(f'allocated_time_edit False =====> {rec.allocated_time_edit}')
                if self.env.user.has_group('rt_buget_phase.group_hr_lock_timesheet_hours_spent') and rec.name:
                    rec.allow_task_timesheet_edit = True
                    print(f"rec.allow_task_timesheet_edit True====> {rec.allow_task_timesheet_edit}")
                else:
                    rec.allow_task_timesheet_edit = False
                    print(f'allow_task_timesheet_edit False =====> {rec.allow_task_timesheet_edit}')
            elif rec.parent_id:
                    rec.allocated_time_edit = rec.parent_id.allocated_time_edit
                    rec.allow_task_timesheet_edit = rec.parent_id.allow_task_timesheet_edit

    # @api.depends('parent_id','parent_id.allow_task_timesheet')
    # def _compute_allow_task_timesheet(self):
    #     for rec in self:
    #         if rec.parent_id:
    #             rec.allow_task_timesheet = rec.parent_id.allow_task_timesheet

    # @api.onchange('parent_id.allow_task_timesheet')
    # def _compute_allow_task_timesheet(self):
    #     for rec in self:
    #         rec.allow_task_timesheet = rec.parent_id.allow_task_timesheet

