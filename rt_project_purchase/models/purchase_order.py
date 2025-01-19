# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = 'Purchase Order Inherit'


    project_id = fields.Many2one('project.project', string='Project', store=True, domain="[('company_id', '=', company_id)]")

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        self.ensure_one()
        vals = super()._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        if self.project_id:
            vals['project_po_id'] = self.project_id.id
            vals['project_po_name'] = self.project_id.name
            po_name = list(self.project_id.name.split("/"))
            print(f"PDD ===> {po_name[0]}")
            county_code = po_name[1]
            year = po_name[2]
            vals['country_code2'] = county_code
            vals['year'] = year
            vals['prefix'] = 'PDD' + '/' + county_code + '/' + str(year)
            po_name2 = list(self.project_id.name.split("-"))
            vals['name'] = po_name2[0]
        return vals
