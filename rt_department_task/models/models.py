# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _domain_project_id(self):
        # Get the employee for the current user
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        department_id = employee.department_id.id

        # Get tasks assigned to the employee's department
        department_tasks = self.env['project.task'].sudo().search([('department_id', '=', department_id)])

        # Get the project IDs from the tasks assigned to this department
        project_ids = [task.project_id.id for task in department_tasks]

        # Define the base domain for the projects, filtering for projects with timesheets enabled
        domain = [('allow_timesheets', '=', True), ('id', 'in', project_ids)]

        # If the user is not a Timesheet Manager, apply additional visibility checks
        if not self.env.user.has_group('hr_timesheet.group_timesheet_manager'):
            domain = expression.AND([domain,
                                     ['|', ('privacy_visibility', '!=', 'followers'),
                                      ('message_partner_ids', 'in', [self.env.user.partner_id.id])]
                                     ])
        return domain

    project_id = fields.Many2one(
        'project.project', 'Project', domain=_domain_project_id, index=True,
        compute='_compute_project_id', store=True, readonly=False)

    task_id = fields.Many2one(
        'project.task', 'Task', index='btree_not_null',
        compute='_compute_task_id', store=True, readonly=False,
        domain="[('allow_timesheets', '=', True), "
               "('project_id', '=?', project_id), "
               "('department_id', '=', user_department)]"
    )

    user_department = fields.Many2one('hr.department', string="User Department", compute="_compute_user_department")

    @api.onchange('project_id')
    def _compute_user_department(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if employee:
            self.user_department = employee.department_id
        else:
            self.user_department = False
