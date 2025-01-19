# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, _lt
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'
    _description = 'project model inherit'

    budget_ids = fields.One2many('project.budget', 'project_id', 'Budgets', readonly=True)
    phases_budgets_all = fields.Boolean(string='Budget Ok', default=False, compute='compute_budget_all_done')

    @api.depends('budget_ids', 'phase_ids')
    def compute_budget_all_done(self):
        for rec in self:
            if rec.budget_ids and rec.phase_ids:
                if len(rec.budget_ids.ids) == len(rec.phase_ids.ids) or len(rec.budget_ids.ids) > len(rec.phase_ids.ids):
                    rec.phases_budgets_all = True
                else:
                    rec.phases_budgets_all = False
            else:
                rec.phases_budgets_all = False
    def create_project_budget(self):
        budget_obj = self.env['project.budget'].sudo()
        for rec in self:
            val = rec.project_budget_vals()
            for phase in self.phase_ids:
                budget_id = budget_obj.search([('phase_id', '=', phase.id)], limit=1)
                if not budget_id:
                    val['phase_id'] = phase and phase.id or False
                    val['name'] = self.name + '/' + phase.name
                    phase.phase_budget_done = True
                    budget_id = budget_obj.sudo().create(val)

    budget_count = fields.Integer(compute='_compute_budget_count')

    def _compute_budget_count(self):
        for project in self:
            budgets = self.env['project.budget'].search([('project_id', '=', project.id)])
            project.budget_count = len(budgets)

    def action_view_budget(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Budget'),
            'domain': [('id', 'in', self.budget_ids.ids)],
            'res_model': 'project.budget',
            'views': [[False, 'list'], [False, 'form']],
            'view_mode': 'list,form',
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    No Budgets found. Let's create one!
                </p><p>
                    Track major progress points that must be reached to achieve success.
                </p>
            """),
        }

    def _get_stat_buttons(self):
        buttons = super(ProjectProject, self)._get_stat_buttons()
        if self.env.user.has_groups('project.group_project_user'):
            self_sudo = self.sudo()
            buttons.append({
                'icon': 'dollar',
                'text': _lt('Budgets'),
                'number': self_sudo.budget_count,
                'action_type': 'object',
                'action': 'action_view_budget',
                'show': self_sudo.display_sales_stat_buttons and self_sudo.budget_count > 0,
                'sequence': 4,
            })
            buttons.append({
                'text': _lt('Create Budget'),
                'action_type': 'object',
                'action': 'create_project_budget',
                'show': self_sudo.display_sales_stat_buttons and self_sudo.phases_budgets_all == False,
                'sequence': 8,
            })

        return buttons


class ProjectMilestone(models.Model):
    _name = 'project.milestone'
    _inherit = 'project.milestone'

    currency_id = fields.Many2one(
        related='sale_line_id.order_id.currency_id',
        depends=['sale_line_id.order_id.currency_id'],
        store=True, precompute=True)

    order_id = fields.Many2one(related='sale_line_id.order_id', string='Sale Order Item')
    amount = fields.Monetary(related='sale_line_id.price_subtotal', string='Amount')
