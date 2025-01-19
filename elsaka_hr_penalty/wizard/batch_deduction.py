# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class batch_deduction(models.TransientModel):
    """Batch Deduction Calculation Wizard"""

    _name = "batch.deduction"
    _description = "Batch Deduction Wizard"

    # @api.multi
    def do_update(self):
        emp_delay_pool = self.env['employee.delay']
        emp_delay_ids = self._context.get('active_ids',[])
        for emp_delay in emp_delay_ids:
            if emp_delay.state == 'draft':
                emp_delay_pool.calc_delay()
                emp_delay.state = '1approve'
            if emp_delay.state == '1approve':
                emp_delay.state = '2approve'
            if emp_delay.state == '2approve':
                emp_delay.state = 'approved'
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
