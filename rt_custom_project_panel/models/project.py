# -*- coding: utf-8 -*-

import json
from collections import defaultdict
from datetime import date

from odoo import api, fields, models, _, _lt
from odoo.exceptions import ValidationError, AccessError
from odoo.osv import expression
from odoo.tools import Query, SQL, OrderedSet


class CustomProject(models.Model):
    _inherit = 'project.project'

    def _get_phase_items(self):
        domain = [('project_id', '=', self.id)]
        rec = self.env['project.phase'].search(domain, limit=100)
        return {
            'total': self.env['project.phase'].sudo().search_count(domain),
            'data': rec.read(['id', 'name', 'ph_reference']),
            'rec_ids': rec.ids,
        }

    def _get_custom_budget_items(self):
        domain = [('project_id', '=', self.id)]
        rec = self.env['project.budget'].search(domain, limit=100)
        return {
            'total': self.env['project.budget'].sudo().search_count(domain),
            'data': {},
            # 'data': rec.read(['id']),
            'data': rec.read(['id', 'name', 'phase_id', 'date_from', 'date_to']),
            'rec_ids': rec.ids,
        }

    def get_panel_data(self):
        panel_data = super().get_panel_data()
        data = {
            **panel_data,
            'phase_items': self._get_phase_items(),
            'custom_budget_items': self._get_custom_budget_items(),
        }
        return data