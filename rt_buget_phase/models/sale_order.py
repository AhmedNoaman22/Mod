# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = 'Sale Order Inherit'

    def action_confirm(self):
        """ On SO confirmation, compute project of budget if budget relating with sale_order_id. """
        sales_budget = self.env['project.budget'].sudo().search([('sale_order_id','=',self.id)])
        print(f"sol Buget ===> {sales_budget[0]}")
        if sales_budget:
            sales_budget[0]._compute_project()
            for line in sales_budget[0].budget_line_ids:
                line._compute_phase_id()
        return super().action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = 'Sale Order Line Inherit'

    project_budget_line = fields.Many2one('project.budget.line', string='Budget Line', copy=False, store=True)

