# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'
    _description = 'Project Milestone Inherit'

    phase_id = fields.Many2one('project.phase', 'Phase', readonly=True, store=True)
    # project_id = fields.Many2one('project.project', 'Project', readonly=True, store=True)
    company_id = fields.Many2one(related='project_id.company_id', string='Company', readonly=True, store=True)
    # accrual_date = fields.Datetime(string='Accrual Date')
