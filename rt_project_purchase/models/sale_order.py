# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = 'Sale Order Inherit Project'

    project_po_name = fields.Char(string='Project PO Name', copy=False, store=True, readonly=True)
    project_po_id = fields.Many2one('project.project', string='Project PO', copy=False, store=True, readonly=True)

            # @api.onchange('company_id')
            # def _onchange_company_id_warning(self):
            #     self.show_update_pricelist = True
            #     if self.order_line and self.state == 'draft':
            #         self.company_id = self.env.company.id or False
            # return {
            #     'warning': {
            #         'title': _("Warning for the change of your quotation's company"),
            #         'message': _("Changing the company of an existing quotation might need some "
            #                      "manual adjustments in the details of the lines. You might "
            #                      "consider updating the prices."),
            #     }
            # }


    # def _prepare_purchase_order_data(self, company, company_partner):
    #     self.ensure_one()
    #     vals = super()._prepare_purchase_order_data(company, company_partner)
    #     if self.project_id:
    #         vals['project_id'] = self.project_id.id
    #     return vals
