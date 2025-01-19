# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class Task(models.Model):
    _inherit = "project.task"
    _description = 'Task Inherit'

    phase_id = fields.Many2one(
        'project.phase', 'Phase',)


    @api.onchange('phase_id')
    def _onchange_phase_id(self):
        for rec in self:
            rec.milestone_id = False

    @api.depends('project_id', 'phase_id')
    def _compute_display_name(self):
        for task in self:
            task.display_name = f'{task.name} / {task.project_id.display_name} / {task.phase_id.display_name}'

