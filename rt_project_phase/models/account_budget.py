# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class AccountBudgetPost(models.Model):
    _inherit = "account.budget.post"
    _description = 'Budgetary Position Inherit'

    phase_id = fields.Many2one(
        'project.phase', 'Phase',)



