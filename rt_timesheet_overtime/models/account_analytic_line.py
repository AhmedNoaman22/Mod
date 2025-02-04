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

    overtime = fields.Boolean(string="OverTime", default=False)
    indirect_amount = fields.Float(string="Indirect Amount", default=0.0, copy=False, store=True, required=True)
    final_amount = fields.Float(string="Final Amount", default=0.0, copy=False, store=True, compute="_compute_final_amount", precompute=True)
    # overtime_amount = fields.Float(string="OverTime Amount", default=0.0, compute="_compute_overtime_amount")

    def write(self, values):
        res = super(AccountAnalyticLine, self).write(values)
        if 'overtime' in values:
            self._compute_final_amount()
        if 'amount' in values:
            self._compute_final_amount()
        if 'indirect_amount' in values:
            self._compute_final_amount()
        return res

    def create(self, values):
        res = super(AccountAnalyticLine, self).create(values)
        if 'overtime' in values:
            self._compute_final_amount()
        if 'amount' in values:
            self._compute_final_amount()
        if 'indirect_amount' in values:
            self._compute_final_amount()
        return res

    @api.depends('indirect_amount','amount')
    def _compute_final_amount(self):
        for rec in self:
            rec.final_amount = rec.amount + rec.indirect_amount

    # @api.depends('overtime','unit_amount','employee_id')
    # def _compute_overtime_amount(self):
    #     for rec in self:
    #         if rec.employee_id:
    #             if rec.overtime:
    #                 overtime_amount = rec.unit_amount * rec.employee_id.hourly_cost
    #             else:
    #                 overtime_amount = 0.0
    #         else:
    #             overtime_amount = 0.0
    #         rec.overtime_amount = overtime_amount


    def _timesheet_postprocess_values(self, values):
        """ Get the addionnal values to write on record
            :param dict values: values for the model's fields, as a dictionary::
                {'field_name': field_value, ...}
            :return: a dictionary mapping each record id to its corresponding
                dictionary values to write (may be empty).
        """
        res = super()._timesheet_postprocess_values(values)

        res = {id_: {} for id_ in self.ids}
        sudo_self = self.sudo()  # this creates only one env for all operation that required sudo()
        # (re)compute the amount (depending on overtime [Added by mahmoud Raafat ], unit_amount, employee_id for the cost, and account_id for currency)
        if any(field_name in values for field_name in ['overtime','unit_amount', 'employee_id', 'account_id']):
            for timesheet in sudo_self:
                if not timesheet.account_id.active:
                    project_plan, _other_plans = self.env['account.analytic.plan']._get_all_plans()
                    raise ValidationError(_(
                        "Timesheets must be created with at least an active analytic account defined in the plan '%(plan_name)s'.",
                        plan_name=project_plan.name
                    ))
                accounts = timesheet._get_analytic_accounts()
                companies = timesheet.company_id | accounts.company_id | timesheet.task_id.company_id | timesheet.project_id.company_id
                if len(companies) > 1:
                    raise ValidationError(_('The project, the task and the analytic accounts of the timesheet must belong to the same company.'))

                cost = timesheet._hourly_cost()
                # (re)compute the amount (depending on overtime [Added by mahmoud Raafat ] requested by Eng Mahmoud Saleh for Mod
                if timesheet.overtime == True:
                    amount = -timesheet.unit_amount * cost * 1.5
                else:
                    amount = -timesheet.unit_amount * cost

                print(f" Amount After ===> {amount}")
                amount_converted = timesheet.employee_id.currency_id._convert(
                    amount, timesheet.account_id.currency_id or timesheet.currency_id, self.env.company, timesheet.date)
                if timesheet.task_id:
                    percentage = self.env['project.budget.line'].sudo().search([('task_id','=',timesheet.task_id.id)])[0].multiplier
                    if percentage:
                        timesheet.indirect_amount = amount_converted * (percentage/100)
                    else:
                        timesheet.indirect_amount = 0.0
                else:
                    timesheet.indirect_amount = 0.0
                timesheet.final_amount = amount_converted + timesheet.indirect_amount

                res[timesheet.id].update({
                    'amount': amount_converted,
                })
        return res


