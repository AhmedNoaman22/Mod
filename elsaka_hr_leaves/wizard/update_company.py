# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class update_company(models.TransientModel):
    """Update Company"""

    _name = "update.company"
    _description = "Update Company in Analytic Journal Items List View"

    def do_update(self):
        analytic_line_pool = self.env['account.analytic.line']
        analytic_line_ids = self._context.get('active_ids',[])
        for line in analytic_line_ids:
            line.company_id = line.journal_id and line.journal_id.company_id.id or False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

