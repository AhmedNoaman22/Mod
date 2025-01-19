# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = 'Sale Order Inherit'

    phase_count = fields.Integer(compute='_compute_phase_count')

    @api.onchange('project_id')
    def _onchange_project_id_phase(self):
        for rec in self:
            if rec.project_id == False:
                rec.order_line.phase_id = False
                rec.order_line.milestone_id = False

    @api.depends('order_line.product_id.service_tracking')
    def _compute_visible_project(self):
        """ Users should be able to select a project_id on the SO if at least one SO line has a product with its service tracking
        configured as 'task_in_project' """
        for order in self:
            order.visible_project = any(
                service_tracking in ['project_only', 'task_in_project'] for service_tracking in order.order_line.mapped('product_id.service_tracking')
            )

    def _compute_phase_count(self):
        phases_ids = []
        for order in self:
            for line in order.order_line:
                if line.phase_id:
                    phase = self.env['project.phase'].search([('id', '=', line.phase_id.id)])
                    if phase.id not in phases_ids:
                        phases_ids.append(phase.id)
            print(f'phases_ids====> {len(phases_ids)}')
            order.phase_count = len(phases_ids)

    def action_view_phase(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Phase'),
            'domain': [('id', 'in', self.order_line.phase_id.ids)],
            'res_model': 'project.phase',
            'views': [[False, 'list'], [False, 'form']],

            # 'views': [(self.env.ref('rt_project_phase.view_project_phase_list').id, 'list')],
            'view_mode': 'list,form',
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    No phases found. Let's create one!
                </p><p>
                    Track major progress points that must be reached to achieve success.
                </p>
            """),
        }
