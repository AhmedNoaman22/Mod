# -*- coding: utf-8 -*-


from odoo import api, fields, models, _, _lt


class ProjectProject(models.Model):
    _inherit = 'project.project'
    _description = 'Project Inherit'

    phase_ids = fields.One2many('project.phase', 'project_id', 'Phases', readonly=True)
    phase_count = fields.Integer(compute='_compute_phase_count')

    def _compute_phase_count(self):
        for project in self:
            phases = self.env['project.phase'].search([('id', 'in', project.phase_ids.ids)])
            print(f'phases_ids====> {len(phases)}')
            project.phase_count = len(phases)

    def action_view_phase(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Phase'),
            'domain': [('id', 'in', self.phase_ids.ids)],
            'res_model': 'project.phase',
            'views': [[False, 'kanban'], [False, 'list'], [False, 'form']],

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

    def _get_stat_buttons(self):
        buttons = super(ProjectProject, self)._get_stat_buttons()
        if self.env.user.has_groups('project.group_project_user'):
            self_sudo = self.sudo()
            buttons.append({
                'icon': 'check-square-o',
                'text': _lt('Phases'),
                'number': self_sudo.phase_count,
                'action_type': 'object',
                'action': 'action_view_phase',
                'show': self_sudo.display_sales_stat_buttons and self_sudo.phase_count > 0,
                'sequence': 0,
            })

        return buttons


