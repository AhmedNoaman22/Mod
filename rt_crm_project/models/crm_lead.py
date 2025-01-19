from odoo import models, fields, api, Command
from datetime import datetime, time


class CrmProject(models.Model):
    _inherit = 'crm.lead'

    project_location = fields.Many2one(comodel_name='res.country', string="Project Location")
    project_city = fields.Many2one(comodel_name="res.country.state", string="Project City", )
    country_code = fields.Char(string="Country Code", related="project_location.code")
    year = fields.Char(string="Year", compute="_compute_num_of_year")
    proposal_manager = fields.Many2one(comodel_name='res.users', string="Proposal Manager")

    def _compute_num_of_year(self):
        for record in self:
            # Get the current year
            current_year = datetime.now().year
            # Assign the current year to the field as a float
            str1 = str(current_year)
            str2 = str1[-2:]
            record.year = str2

    @api.onchange('project_location')
    def calc_open_city_ids(self):
        for rec in self:
            if rec.project_city:
                rec.project_country_ids = rec.project_location

    def convert_amount_currency_to_company_currency(self, amount_currency, date, currency):
        company = self.company_id
        balance = currency._convert(amount_currency, company.currency_id, company, date)
        return balance

    # def action_create_pdd1(self):
    #     print('========== TEST ==============')

    # def action_sale_quotations_new(self):
    #     res = super(CrmProject, self).action_sale_quotations_new()
    #     # print('========== enter here =========', res)
    #     active_id = self.id
    #     # print('======= active ', active_id)
    #     crm_lead = self.env['crm.lead'].sudo().search([('id', '=', active_id)])
    #     # if crm_lead and crm_lead.scope_service_line_ids:
    #     #     lines = crm_lead.scope_service_line_ids
    #     #     print('========= lines', lines)
    #     #     line_ser_list = []
    #     #     for line in lines:
    #     #         val = {
    #     #             'scope_phase': line.scope_phase,
    #     #             'department': line.department,
    #     #             'phases_duration_week': line.phases_duration_week,
    #     #             'fee_percentage': line.fee_percentage,
    #     #             'amount': line.amount,
    #     #         }
    #     #         line_ser_list.append(val)
    #     #     if res and res['context']:
    #     #         res['context']['default_sale_scope_service_line_ids'] = line_ser_list
    #     # if crm_lead and crm_lead.crm_product_ids:
    #     #     lines = crm_lead.crm_product_ids
    #     #     print('========= lines', lines)
    #     #     line_prod_list = []
    #     #     for line in lines:
    #     #         val = {
    #     #             'product_id': line.product_id.id,
    #     #             'product_uom_qty': line.quantity,
    #     #             'price_unit': line.unit_price,
    #     #             'name': line.product_id.name,
    #     #             'company_id': self.env.company.id
    #     #         }
    #     #         line_prod_list.append(val)
    #     #     if res and res['context']:
    #     #         res['context']['default_order_line'] = line_prod_list
    #     res['default_country_code2'] = 'test'
    #     print('======== res 123', res)
    #     if res and res['context']:
    #         res['context']['default_country_code2'] = 'test'
    #         # res['context']['default_crm_description'] = crm_lead.crm_description
    #         # res['context']['default_location'] = crm_lead.location
    #         # res['context']['default_project_status'] = crm_lead.project_status
    #     print('======== res 123', res)
    #     return res
