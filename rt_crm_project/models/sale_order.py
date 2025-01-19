# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Order Inherit Crm'

    sale_scope_service_line_ids = fields.Char('Test')
    project_location = fields.Many2one(comodel_name='res.country', string="Project Location", copy=False, store=True)
    project_city = fields.Many2one(comodel_name="res.country.state", string="Project City", )
    country_code2 = fields.Char(string="Country Code", related="project_location.code", copy=False, store=True)
    year = fields.Char(string="Year", copy=False, compute="_compute_num_of_year", store=True)
    proposal_manager = fields.Many2one(comodel_name='res.users', string="Proposal Manager")
    prefix = fields.Char(string='Prefix', required=True, default='EGY', copy=False, store=True)
    contract_status = fields.Char(string='Contract Status', copy=False, store=True)

    # @api.onchange('project_location')
    # def _onchange_location(self):
    #     self.prefix = 'PDD' + '/' + str(self.project_location.code) + '/' + str(self.year)
    #
    @api.depends('date_order')
    def _compute_num_of_year(self):
        for record in self:
            # Get the current year
            current_year = datetime.now().year
            # Assign the current year to the field as a float
            str1 = str(current_year)
            str2 = str1[-2:]
            record.year = str2

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            print('========== val =========', val)
            if val and 'opportunity_id' in val and val['opportunity_id']:
                get_opp = self.env['crm.lead'].sudo().search([('id', '=', val['opportunity_id'])])
                county_code = get_opp.country_code
                year = get_opp.year
                val['project_location'] = get_opp.project_location.id
                val['project_city'] = get_opp.project_city.id
                val['proposal_manager'] = get_opp.proposal_manager.id
                val['country_code2'] = county_code
                val['year'] = year
                val['prefix'] = year + '/' + county_code


            elif val and 'project_po_name' in val and val['project_po_name']:
                po_name = list(val['project_po_name'].split("/"))
                print(f"PDD ===> {po_name[0]}")
                county_code = po_name[1]
                year = po_name[2]
                val['country_code2'] = county_code
                val['year'] = year
                val['prefix'] = str(year) + '/' + county_code

            elif val and 'country_code2' in val and val['country_code2']:
                val['prefix'] = val['year'] + '/' + val['country_code2']
            else:
                if val and 'project_location' in val and val['project_location'] == False:
                    raise ValidationError(_("You Must input ProjectLocation Field !."))
                else:
                    location_id = self.env['res.country'].sudo().search([('id', '=', val['project_location'])])
                    county_code = location_id.code
                    current_year = datetime.now().year
                    str1 = str(current_year)
                    year = str1[-2:]
                    val['prefix'] = year + '/' + county_code
            if val.get('name', _("New")) == _("New"):
                prefix = val.get('prefix', 'EG')
                sequence_code = f'sale.order.{prefix}'
                print('=========== sequence_code', sequence_code)
                sequence = self.env['ir.sequence'].search([('code', '=', sequence_code)], limit=1)
                print('====== sequence ========', sequence)
                if not sequence:
                    sequence = self.env['ir.sequence'].create({
                        'name': f'Sales Order {prefix} Sequence',
                        'code': sequence_code,
                        'prefix': f'{prefix}/',
                        'padding': 3,
                        'number_next': 1,
                        'number_increment': 1,
                        # 'company_id': False,
                    })
                val['name'] = sequence.next_by_code(sequence_code) or 'New'
            res = super(SaleOrder, self).create(val)
            print('======= res', res)
            return res
    #
    # @api.onchange('company_id')
    # def _onchange_company_id_warning(self):
    #     self.show_update_pricelist = True
    #     if self.country_code2:
    #         return

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sale Order Line inherit'

    department_ids = fields.Many2many('hr.department', 'Departments')
