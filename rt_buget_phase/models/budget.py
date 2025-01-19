# -*- coding: utf-8 -*-
from pygments.lexer import default

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError



class ProjectBudgetModel(models.Model):
    _inherit = 'project.budget'
    _description = 'project budget model inherit'

    phase_id = fields.Many2one('project.phase', 'Phase', copy=False)
    task_ids = fields.One2many('project.task', 'budget_id', copy=False)
    task_count = fields.Integer(compute='_compute_task_count')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_currency_id',
        store=True,
        precompute=True,
        ondelete='restrict'
    )
    @api.depends('company_id')
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id

    total_amount_plan_hours = fields.Monetary(string="Total Planned Cost", store=True, compute='_compute_totals', tracking=4)
    total_amount_actual_hours = fields.Monetary(string="Total Actual Cost", store=True, compute='_compute_totals', tracking=4)


    @api.depends('budget_line_ids', 'budget_line_ids.amount_planing_hours', 'budget_line_ids.amount_planing_hours', 'budget_line_ids.amount_actually_hours')
    def _compute_totals(self):
        for rec in self:
            if rec.budget_line_ids:
                rec.total_amount_plan_hours = sum(rec.budget_line_ids.mapped('amount_planing_hours'))
                # total_cost = 0.0
                # for line in rec.budget_line_ids:
                #     total_cost = total_cost + line.amount_actually_hours
                #
                # rec.total_amount_actual_hours = total_cost
            rec.total_amount_actual_hours = sum(self.budget_line_ids.mapped('amount_actually_hours'))


    def _compute_task_count(self):
        for budget in self:
            tasks = self.env['project.task'].search([('id', 'in', budget.task_ids.ids)])
            print(f'phases_ids====> {len(tasks)}')
            budget.task_count = len(tasks)

    def action_view_task(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Task'),
            'domain': [('id', 'in', self.task_ids.ids)],
            'res_model': 'project.task',
            'views': [[False, 'kanban'], [False, 'list'], [False, 'form']],

            # 'views': [(self.env.ref('rt_project_phase.view_project_phase_list').id, 'list')],
            'view_mode': 'list,form',
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    No phases found. Let's create one!
                </p><p>
                    Track major progress points that must be reached to achieve success.
                </p>
            """),
        }



    def create_Tasks(self):
        for rec in self:
            if len(rec.budget_line_ids.task_id) == len(rec.budget_line_ids):
                raise ValidationError(_("The Tasks for all departments had been created!."))
            else:
                task_vals = []
                for line in rec.budget_line_ids:
                    if not line.task_id:
                        task = self.env['project.task'].create(line._prepare_tasks_vals())
                        line.task_id = task.id
                        task_vals.append(task.id)
                tasks = self.env['project.task'].search([('id','in',task_vals)])
                rec.task_ids = rec.task_ids.ids + tasks.ids
                print(f"rec.budget_line_ids ===> {len(rec.budget_line_ids)}")

        # message = 'The Tasks of this budget had been created'
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': _('Creating Tasks'),
        #         'message': message,
        #         'type': 'success',
        #         'sticky': False,
        #     }
        # }

    # 'title': _('The inter-warehouse transfers have been generated'),
    # 'message': '%s',
    # 'links': [{
    #     'label': move.picking_id.name,
    #     'url': f'#action={action.id}&id={move.picking_id.id}&model=stock.picking&view_type=form'
    # }],
    # 'sticky': False,


    # def _get_task_created_notification(self):
    #     message = 'The Tasks of this budget had been created'
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': message,
    #             'type': 'success',
    #             'sticky': True,
    #         }
    #     }


class BudgetLine(models.Model):
    _inherit = 'project.budget.line'
    _description = 'project budget line inherit'

    task_id = fields.Many2one('project.task', 'Task', copy=False, store=True)
    project_id = fields.Many2one(related='budget_id.project_id', copy=False, store=True)
    phase_id = fields.Many2one(related='budget_id.phase_id', copy=False, store=True)
    company_id = fields.Many2one(related='budget_id.company_id', copy=False, store=True)


    actually_time_sheet_hour = fields.Float(string='Timesheets Hours', compute='compute_actually_hours')
    actually_cost_hour = fields.Float(string='Actually Cost', compute='compute_actually_hours', copy=False)
    multiplier = fields.Float(string='(%) Multiplier', default=65, readonly=True)
    actually_cost_hours = fields.Float(string='Actually Cost Hours + Indirect Overhead', compute='compute_actually_hours', copy=False)
    amount_planing_hours = fields.Float(string='Budget Amount', compute='compute_amount_planing_hours', inverse='inverse_compute_amount', copy=False)
    amount_actually_hours = fields.Float(string='Total Cost', compute='compute_amount_actually_hours', copy=False)

    def unlink(self):
        for rec in self:
            if rec.task_id.timesheet_ids:
                print(f"task timesheet ids ====> {rec.task_id.timesheet_ids}")
                raise UserError(
                    _(f'Unable to delete this line as this task  {rec.task_id.name} as it has a timesheet.'))
            return super(BudgetLine, self).unlink()


    def _prepare_tasks_vals(self):
        return {
            'name': self.name or self.department_id.name,
            'project_id': self.project_id.id,
            'budget_id': self.budget_id.id,
            'phase_id': self.phase_id.id,
            'department_id': self.department_id.id,
            'allocated_hours': self.task_planned_hours,
        }

    @api.depends('task_id', 'task_id.timesheet_ids', 'task_id.total_hours_spent', 'project_id','budget_id','budget_id.total_amount_actual_hours')
    def compute_actually_hours(self):
        for line in self:
            timesheets = self.env['account.analytic.line'].search(['|',('task_id','=',line.task_id.id),('task_id.parent_id','=',line.task_id.id)])
            hours_spent = 0.0
            hours_cost = 0.0
            if line.task_id.total_hours_spent:
                hours_spent = line.task_id.total_hours_spent
            print(f" hours_spent ======> {hours_spent}")
            print(f" timesheeets ======> {timesheets}")
            if timesheets:
                hours_cost = sum(timesheets.mapped('amount'))
            print(f"hours cost ===== {hours_cost}")
            line.actually_time_sheet_hour = hours_spent
            if not hours_spent == 0.0:
                line.actually_cost_hour = hours_cost * -1
                # line.multiplier = ((hours_cost / hours_spent) * -1) * 0.65
                line.actually_cost_hours = hours_cost * -1 * (1 + (line.multiplier / 100))
            else:
                line.actually_cost_hour = 0.0
                line.actually_cost_hours = 0.0


    @api.onchange('task_planned_hours', 'hour_cost', 'amount_planing_hours')
    def onchange_task_planned_hours(self):
        for line in self:
            line.amount_planing_hours = line.task_planned_hours * line.hour_cost

    @api.onchange('hour_cost', 'amount_planing_hours')
    def onchange_amount_planing_hours(self):
        for line in self:
            line.task_planned_hours = line.amount_planing_hours / line.hour_cost if line.hour_cost != 0.0 else 0.0

    @api.depends('task_planned_hours', 'hour_cost')
    def compute_amount_planing_hours(self):
        for line in self:
            line.amount_planing_hours = line.task_planned_hours * line.hour_cost

    @api.depends('amount_planing_hours', 'hour_cost')
    def inverse_compute_amount(self):
        for line in self:
            print(f'line hour cost ==== {line.hour_cost}')
            line.task_planned_hours = line.amount_planing_hours / line.hour_cost if line.hour_cost != 0.0 else 0.0

    @api.depends('actually_cost_hour', 'actually_time_sheet_hour', 'multiplier')
    def compute_amount_actually_hours(self):
        for line in self:
            print(f" 1.56 ====== value = {(1 + (line.multiplier / 100))}")
            line.amount_actually_hours = line.actually_cost_hour * (1 + (line.multiplier / 100))

    pm_percentage = fields.Float(string='%PM', default=0, copy=False)
    etc_hours = fields.Float(string='ETC Hours', default=0, copy=False, compute='_compute_etc_hours_cost')
    etc_cost_planned = fields.Float(string='ETC Cost Planned', default=0, copy=False, compute='_compute_etc_hours_cost')

    @api.onchange('actually_time_sheet_hour','pm_percentage','amount_actually_hours')
    def _onchange_compute_etc_hours_cost(self):
        for rec in self:
            if not rec.pm_percentage == 0.0:
                rec.etc_hours = ((1 - (rec.pm_percentage / 100)) * rec.actually_time_sheet_hour) / (rec.pm_percentage / 100)
                rec.etc_cost_planned = ((1 - (rec.pm_percentage / 100)) * rec.amount_actually_hours) / (rec.pm_percentage / 100)

    @api.depends('actually_time_sheet_hour','pm_percentage','amount_actually_hours')
    def _compute_etc_hours_cost(self):
        for rec in self:
            if not rec.pm_percentage == 0.0:
                rec.etc_hours = ((1 - (rec.pm_percentage / 100)) * rec.actually_time_sheet_hour) / (rec.pm_percentage / 100)
                rec.etc_cost_planned = ((1 - (rec.pm_percentage / 100)) * rec.amount_actually_hours) / (rec.pm_percentage / 100)
            else:
                rec.etc_hours = 0.0
                rec.etc_cost_planned = 0.0

