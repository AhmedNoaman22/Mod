# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError


class BankRecWidgetLine(models.Model):
    _inherit = "bank.rec.widget.line"
    _description = 'Bank Rec Widget Line Inherit'

    phase_id = fields.Many2one(
        'project.phase', 'Phase', compute='compute_phase_milestone')
    milestone_id = fields.Many2one(
        'project.milestone', 'Milestone', compute='compute_phase_milestone')


    @api.depends('source_aml_id')
    def compute_phase_milestone(self):
        for line in self:
            if line.flag in ('aml', 'liquidity'):
                line.phase_id = line.source_aml_id.phase_id.id
                line.milestone_id = line.source_aml_id.milestone_id.id
            else:
                line.phase_id = line.phase_id
                line.milestone_id = line.milestone_id


    def _get_aml_values(self, **kwargs):
        self.ensure_one()
        return {
            'name': self.name,
            'account_id': self.account_id.id,
            'phase_id': self.phase_id.id,
            'milestone_id': self.milestone_id.id,
            'currency_id': self.currency_id.id,
            'amount_currency': self.amount_currency,
            'balance': self.debit - self.credit,
            'reconcile_model_id': self.reconcile_model_id.id,
            'analytic_distribution': self.analytic_distribution,
            'tax_repartition_line_id': self.tax_repartition_line_id.id,
            'tax_ids': [Command.set(self.tax_ids.ids)],
            'tax_tag_ids': [Command.set(self.tax_tag_ids.ids)],
            'group_tax_id': self.group_tax_id.id,
            **kwargs,
        }
