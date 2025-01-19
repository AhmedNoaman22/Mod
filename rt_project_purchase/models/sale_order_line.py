# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = 'Sale Order Line Inherit Project'

    project_po_name = fields.Char(related='order_id.project_po_name', string='Project Name', store=True)

    def _timesheet_create_project_prepare_values(self):
        self.ensure_one()
        vals = super()._timesheet_create_project_prepare_values()
        if self.order_id.project_po_name:
            print(f"Order Projcet id 2 ====> {self.order_id.project_po_name}")
            vals['name'] = self.order_id.project_po_name
        return vals

    def _timesheet_create_project(self):
        self.ensure_one()
        project = super()._timesheet_create_project()
        # values = self._timesheet_create_project_prepare_values()
        if self.project_po_name:
            project.write({'name': self.project_po_name})
        return project


