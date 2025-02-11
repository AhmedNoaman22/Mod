# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProjectPhase(models.Model):
    _inherit = 'project.phase'
    _description = 'project phase model inherit'

    phase_budget_done = fields.Boolean(string='Budget Ok', default=False, store=True)
    budget_line_ids = fields.One2many('project.budget.line', 'phase_id', 'Budgets Lines', copy=False)
    partner_ids = fields.Many2many('res.partner', 'Customers', copy=False)

