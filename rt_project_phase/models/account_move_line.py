# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _description = 'Journal Item Inherit'

    phase_id = fields.Many2one(
        'project.phase', 'Phase')
    milestone_id = fields.Many2one('project.milestone', 'Milestone')


    # @api.onchange('phase_id')
    # def _onchange_phase_id(self):
    #     for rec in self:
    #         rec.milestone_id = rec.phase_id.milestone_id

