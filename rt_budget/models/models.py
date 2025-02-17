# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def project_budget_vals(self):
        val = {
            'name': self.name,
            'project_id': self.id,
            'company_id': self.company_id.id or self.env.company.id,
        }
        return val

    def create_project_budget(self):
        budget_obj = self.env['project.budget']
        for rec in self:
            val = rec.project_budget_vals()
            res = budget_obj.sudo().create(val)
            return res

#Added on rt_task_department
# class HrDepartment(models.Model):
#     _inherit = 'hr.department'
#
#     hour_cost = fields.Float(string='Hour Cost')


class ProjectBudgetModel(models.Model):
    _name = 'project.budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'project budget model'

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one(comodel_name='res.company', default='lambda self: self.env.user.company_id.id',
                                 string="Company", required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_confirm', 'To Confirm'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The Budget is not to confirm or confirmed yet. Saving and to confirm firstly to apply.\n"
             " * To Confirm: The budget is to_confirm for responsible to confirm it.\n"
             " * Confirmed: The budget is confirmed for this project.\n"
             " * Done: The Budget has been processed.\n"
             " * Cancelled: The Budget has been cancelled.")

    def action_to_confirm(self):
        for rec in self:
            rec.state = 'to_confirm'

    def action_confirm(self):
        for rec in self:
            if rec.project_id == False:
                raise UserError(
                    _("You can’t confirm any Budget without Project. Please add Project to confirm this Budget."))
            else:
                rec.state = 'confirmed'

    def action_done(self):
        for rec in self:
            if rec.project_id == False:
                raise UserError(
                    _("You can’t confirm any Budget without Project. Please add Project to confirm this Budget."))
            else:
                rec.state = 'done'

    def action_cancel(self):
        for budget in self:
            if budget.project_id:
                raise UserError(
                    _("You can’t cancel any Budget with Project"))
            else:
                budget.state = 'cancel'

    def action_reset(self):
        for request in self:
            request.state = 'draft'
        return True

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    project_id = fields.Many2one(comodel_name='project.project', string="Project")
    note = fields.Html(string='Note')
    budget_line_ids = fields.One2many('project.budget.line', 'budget_id', string="Budget Line")


class BudgetLine(models.Model):
    _name = 'project.budget.line'
    _description = 'project budget line'

    name = fields.Char(string="Name")
    budget_id = fields.Many2one('project.budget', string="Budget")
    state = fields.Selection(related='budget_id.state', store=True)
    department_id = fields.Many2one(comodel_name="hr.department", string="Department")
    hour_cost = fields.Float(string='Department Hour Cost', readonly=True,  default=0.0)
    task_planned_hours = fields.Float(string='Budget Hours')
    actually_time_sheet_hour = fields.Float(string='Timesheets Hours')
    actually_cost_hour = fields.Float(string='Actually Cost')
    multiplier = fields.Float(string='(%) Multiplier', default=lambda self: self.department_id.multiplier_percentage if self.department_id else 0.0, compute="_compute_multiplier", store=True, copy=False, precompute=True)
    actually_cost_hours = fields.Float(string='Actually Cost Hours + Indirect Overhead')
    pm_percentage = fields.Float(string='HOD', default=0)
    etc_hours = fields.Float(string='ETC Hours', default=0)
    etc_cost_planned = fields.Float(string='ETC Cost Planned', default=0)
    amount_planing_hours = fields.Float(string='Budget Amount')
    amount_actually_hours = fields.Float(string='Total Cost')

    note = fields.Char(string='Note')

    @api.depends('department_id')
    def _compute_multiplier(self):
        for rec in self:
            if rec.department_id:
                rec.multiplier = rec.department_id.multiplier_percentage
            else:
                rec.multiplier = 0.0

    @api.onchange('department_id')
    def _onchange_department(self):
        for rec in self:
            if rec.department_id:
                rec.hour_cost = rec.department_id.hour_cost

    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     for val in vals_list:
    #         if val and 'department_id' in val:
    #             if val['department_id']:
    #                 department = self.env['hr.department'].sudo().search([('id', '=', val['department_id'])])
    #                 val['hour_cost'] = department.hour_cost
    #             else:
    #                 val['hour_cost'] = 0.0
    #         res = super(BudgetLine, self).create(val)
    #         print('======= res', res)
    #         return res
    #
    # def write(self, val):
    #     if val and 'department_id' in val:
    #         if val['department_id']:
    #             department = self.env['hr.department'].sudo().search([('id', '=', val['department_id'])])
    #             val['hour_cost'] = department.hour_cost
    #         else:
    #             val['hour_cost'] = 0.0
    #     res = super(BudgetLine, self).write(val)
    #     print('======= res', res)
    #     return res
    # #
