# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Hr Employee Inherit'

    target_hours = fields.Float('Target Hours',
        groups="hr.group_hr_user", default=198.0)
    total_hours_monthly = fields.Float('Total Hours Monthly',
        groups="hr.group_hr_user", default=198.0)

    hourly_cost = fields.Monetary('Hourly Cost', currency_field='currency_id',
        groups="hr.group_hr_user", default=1.0, compute='_compute_hourly_cost')

    @api.depends('contract_id','contract_id.wage')
    def _compute_hourly_cost(self):
        for rec in self:
            # employee_work_entry = self.env['hr.work.entry'].sudo().search([('employee_id','=',rec.id),])
            if rec.contract_id:
                # rec.hourly_cost = rec.contract_id.wage / sum(employee_work_entry.mapped('duration'))
                rec.hourly_cost = rec.contract_id.wage / rec.total_hours_monthly
            else:
                rec.hourly_cost = rec.hourly_cost

    # @api.model_create_multi
    # def create(self, vals):
    #     res = super(HrEmployee, self).create(vals)
    #     for rec in res:
    #         if rec.hourly_cost or rec.name:
    #             if rec['hourly_cost'] == 0.00:
    #                 raise ValidationError(_("The Hourly cost is required field when create."))
    #         if rec.total_hours_monthly or rec.name:
    #             if rec['total_hours_monthly'] == 0.00:
    #                 raise ValidationError(_("The Total Hours Monthly is required field when create."))
    #     return res
    #
    # def write(self, vals):
    #     res = super().write(vals)
    #     if 'hourly_cost' in vals or 'name' in vals :
    #         for rec in self:
    #             if rec.hourly_cost == 0.00:
    #                 raise ValidationError(_("The Hourly cost is required field."))
    #     if 'total_hours_monthly' in vals or 'name' in vals :
    #         for rec in self:
    #             if rec.total_hours_monthly == 0.00:
    #                 raise ValidationError(_("The Total Hours Monthly cost is required field."))
    #     return res

    # @api.onchange('hourly_cost')
    # def _constraints_on_hourly_cost(self):
    #     if self.hourly_cost == 0.00:
    #         raise ValidationError(_("The Hourly cost is required field."))

    # @api.constrains('hourly_cost')
    # def _constraints_on_hourly_cost(self):
    #     if self.hourly_cost == 0.00:
    #         raise ValidationError(_("The Hourly cost is required field."))
