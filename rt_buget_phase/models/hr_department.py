# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _description = 'Hr Department Compute Hour Cost'

    hour_cost = fields.Float(string='Hour Cost', compute='_compute_hour_cost', readonly=False)

    @api.depends('member_ids','member_ids.hourly_cost')
    def _compute_hour_cost(self):
        for rec in self:
            dep_employees = self.env['hr.employee'].sudo().search([('id','in',rec.member_ids.ids),('contract_id.state','=','open')])
            if dep_employees:
                rec.hour_cost = sum(dep_employees.mapped('hourly_cost')) / len(dep_employees)
            else:
                rec.hour_cost = rec.hour_cost



