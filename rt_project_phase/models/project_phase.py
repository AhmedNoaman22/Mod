# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class ProjectPhase(models.Model):
    _name = 'project.phase'
    _description = 'RTt Project Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char(string='Name', required=True)
    ph_reference = fields.Char(string='Reference', default='New', readonly=True, store=True, copy=False)
    partner_ids = fields.Many2many('res.partner', 'Customers', copy=False)
    milestone_ids = fields.One2many(
        'project.milestone', 'phase_id', 'Milestone')
    order_ids = fields.Many2many(
        'sale.order', 'Order', compute='_compute_order_count')
    task_ids = fields.One2many(
        'project.task', 'phase_id', 'Tasks')

    order_count = fields.Integer(compute='_compute_order_count')

    project_id = fields.Many2one('project.project', string='Project', store=True)
    company_id = fields.Many2one(related='project_id.company_id', string='Company', readonly=True, store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ph_reference') or vals['ph_reference'] == _('New'):
                vals['ph_reference'] = self.env['ir.sequence'].next_by_code('project_phase_code') or _('New')
        return super().create(vals_list)


    # @api.model_create_multi
    # def create(self, vals):
    #     if vals.get('ph_reference', 'New') == 'New':
    #         vals['ph_reference'] = self.env['ir.sequence'].next_by_code('project_phase_code')
    #     return super(ProjectPhase, self).create(vals)

    def _compute_order_count(self):
        for phase in self:
            sol = self.env['sale.order.line'].search([('phase_id', '=', phase.id)])
            order = self.env['sale.order'].search([('id', 'in', sol.order_id.ids)])
            print(f"order ===> {order}")
            phase.order_count = len(order)
            phase.order_ids = order.ids

    def action_view_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Order'),
            'domain': [('id', 'in', self.order_ids.ids)],
            'res_model': 'sale.order',
            'views': [[False, 'list'], [False, 'form']],
            'view_mode': 'list,form',
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    No orders found. Let's create one!
                </p><p>
                    Track major progress points that must be reached to achieve success.
                </p>
            """),
        }

    def action_view_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Projects'),
            'domain': [('id', '=', self.project_id.id)],
            'res_model': 'project.project',
            'views': [[False, 'list'], [False, 'form']],
            'view_mode': 'list,form',
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    No projects found. Let's create one!
                </p><p>
                    Track major progress points that must be reached to achieve success.
                </p>
            """),
        }
