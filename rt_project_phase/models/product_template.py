# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = 'Product Template Inherit'

    service_tracking = fields.Selection(
        selection_add=[('budget_in_project', 'Project & budget'),],ondelete={'budget_in_project': 'set default'},
    )
