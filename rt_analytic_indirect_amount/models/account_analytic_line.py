from collections import defaultdict
from statistics import mode
import re

from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.osv import expression
from odoo.tools import format_list
from odoo.tools.translate import _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    indirect_amount = fields.Monetary(string="Indirect Amount", default=0.0, copy=False, store=True,
                                   compute="_compute_indirect_amount", required=True, precompute=True)
    final_amount = fields.Monetary(string="Final Amount", default=0.0, copy=False, store=True,
                                compute="_compute_final_amount", precompute=True)

    def write(self, values):
        res = super(AccountAnalyticLine, self).write(values)
        if 'amount' in values:
            self._compute_final_amount()
        if 'indirect_amount' in values:
            self._compute_indirect_amount()
        return res

    def create(self, values):
        res = super(AccountAnalyticLine, self).create(values)
        if 'amount' in values:
            self._compute_final_amount()
        if 'indirect_amount' in values:
            self._compute_final_amount()
        return res

    @api.depends('amount', 'task_id')
    def _compute_indirect_amount(self):
        for rec in self:
            if rec.task_id:
                percentage = self.env['project.budget.line'].sudo().search([('task_id', '=', rec.task_id.id)])[
                    0].multiplier
                if percentage:
                    rec.indirect_amount = rec.amount * (percentage / 100)
                else:
                    rec.indirect_amount = 0.0
            else:
                rec.indirect_amount = 0.0

    @api.depends('indirect_amount', 'amount')
    def _compute_final_amount(self):
        for rec in self:
            rec.final_amount = rec.amount + rec.indirect_amount




