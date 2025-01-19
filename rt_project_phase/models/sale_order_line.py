# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = 'Sale Order Line Inherit'

    phase_id = fields.Many2one('project.phase', 'Phase', copy=False)
    milestone_id = fields.Many2one(
        'project.milestone', 'Milestone', readonly=True, copy=False)
    accrual_date = fields.Datetime(string='Accrual Date', default=lambda self: fields.Datetime.now())


    def write(self, vals):
        res = super().write(vals)
        if 'accrual_date' in vals:
            for rec in self:
                self.env['project.milestone'].sudo().search([('id','=',rec.milestone_id.id)]).write({
                    'deadline': rec.accrual_date,
                })
        return res

    def _generate_milestone(self):
        if self.product_id.service_policy == 'delivered_milestones':
            if not self.milestone_id:
                milestone = self.env['project.milestone'].create({
                    'name': self.name,
                    'project_id': self.project_id.id or self.order_id.project_id.id,
                    'sale_line_id': self.id,
                    'deadline': self.accrual_date,
                    'quantity_percentage': 1,
                })
                if self.product_id.service_tracking == 'task_in_project':
                    self.task_id.milestone_id = milestone.id
                self.milestone_id = milestone.id
                # if not self.order_id.project_id and not self.phase_id:
                #     self._create_phase()
                    # else:
                #     if self.product_id.service_tracking == 'task_in_project':
                #         self.task_id.phase_id = self.phase_id.id
                #         self.task_id.name = milestone.id
                #     partners_ids = []
                #     partners_ids.append(self.order_id.partner_id.id)
                #     self.phase_id.partner_ids = self.phase_id.partner_ids.ids + partners_ids
                # self.milestone_id.phase_id = self.phase_id.id
                # if self.product_id.service_tracking == 'budget_in_project':
                #     self._create_budget()
            else:
                self.env['project.milestone'].search([('id','=',self.milestone_id.id)]).write({
                    'name': self.name,
                    'project_id': self.project_id.id or self.order_id.project_id.id,
                    'sale_line_id': self.id,
                    'deadline': self.accrual_date,
                    'quantity_percentage': 1,
                })

    def _generate_phase(self):
        if not self.order_id.project_id and not self.phase_id:
            self._create_phase()
        else:
            if self.product_id.service_tracking == 'task_in_project':
                self.task_id.phase_id = self.phase_id.id
                self.task_id.name = self.milestone_id.id
            partners_ids = []
            partners_ids.append(self.order_id.partner_id.id)
            self.phase_id.partner_ids = self.phase_id.partner_ids.ids + partners_ids
        self.milestone_id.phase_id = self.phase_id.id

    def prepare_phase_vals(self):
        title = self.name
        vals = {
            'name': self.project_id.name + '-' + title,
            'project_id': self.project_id.id or self.order_id.project_id.id,
            'partner_ids': [(6, 0, [self.order_id.partner_id.id])],
        }
        return vals

    def _create_phase(self):
        title = self.name
        product_exist = self.env['sale.order.line'].search([('order_id','=',self.order_id.id),('product_id','=',self.product_id.id),('phase_id','!=',False)])
        if product_exist:
            for item in product_exist:
                self.write({
                    'phase_id': item.phase_id.id,
                })
                if self.product_id.service_tracking == 'task_in_project':
                    self.task_id.phase_id = item.phase_id.id
                self.milestone_id.phase_id = item.phase_id.id
                phase = item.phase_id
        else:
            phase = self.env['project.phase'].create(self.prepare_phase_vals())
            self.write({
                'phase_id': phase.id,
            })
            if self.product_id.service_tracking == 'task_in_project':
                self.task_id.phase_id = phase.id
        return phase

    # def _create_budget(self):
    #     title = self.name
    #     budget = self.env['res.partner'].create({
    #         'name': self.project_id.name + title,
    #     })
    #     return budget

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['phase_id'] = self.phase_id.id
        res['milestone_id'] = self.milestone_id.id
        return res


    def _timesheet_service_generation(self):
        """ For service lines, create the task or the project. If already exists, it simply links
            the existing one to the line.
            Note: If the SO was confirmed, cancelled, set to draft then confirmed, avoid creating a
            new project/task. This explains the searches on 'sale_line_id' on project/task. This also
            implied if so line of generated task has been modified, we may regenerate it.
        """
        so_line_task_global_project = self.filtered(
            lambda sol: sol.is_service and sol.product_id.service_tracking == 'task_global_project')
        so_line_new_project = self.filtered(
            lambda sol: sol.is_service and sol.product_id.service_tracking in ['project_only', 'task_in_project',
                                                                               'budget_in_project'])

        # search so lines from SO of current so lines having their project generated, in order to check if the current one can
        # create its own project, or reuse the one of its order.
        map_so_project = {}
        if so_line_new_project:
            order_ids = self.mapped('order_id').ids
            so_lines_with_project = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False),
                                                 ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                                                 ('product_id.project_template_id', '=', False)])
            map_so_project = {sol.order_id.id: sol.project_id for sol in so_lines_with_project}
            so_lines_with_project_templates = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), (
            'product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                                                           ('product_id.project_template_id', '!=', False)])
            map_so_project_templates = {(sol.order_id.id, sol.product_id.project_template_id.id): sol.project_id for sol in
                                        so_lines_with_project_templates}

        # search the global project of current SO lines, in which create their task
        map_sol_project = {}
        if so_line_task_global_project:
            map_sol_project = {sol.id: sol.product_id.with_company(sol.company_id).project_id for sol in
                               so_line_task_global_project}

        def _can_create_project(sol):
            if not sol.project_id:
                if sol.product_id.project_template_id:
                    return (sol.order_id.id, sol.product_id.project_template_id.id) not in map_so_project_templates
                elif sol.order_id.id not in map_so_project:
                    return True
            return False

        def _determine_project(so_line):
            """Determine the project for this sale order line.
            Rules are different based on the service_tracking:

            - 'project_only': the project_id can only come from the sale order line itself
            - 'task_in_project': the project_id comes from the sale order line only if no project_id was configured
              on the parent sale order"""

            if so_line.product_id.service_tracking in ['task_in_project', 'project_only']:
                return so_line.order_id.project_id or so_line.project_id

            return False

        # task_global_project: create task in global project
        for so_line in so_line_task_global_project:
            if not so_line.task_id:
                if map_sol_project.get(so_line.id) and so_line.product_uom_qty > 0:
                    so_line._timesheet_create_task(project=map_sol_project[so_line.id])

        # project_only, task_in_project: create a new project, based or not on a template (1 per SO). May be create a task too.
        # if 'task_in_project' and project_id configured on SO, use that one instead
        for so_line in so_line_new_project:
            project = _determine_project(so_line)
            if not project and _can_create_project(so_line):
                project = so_line._timesheet_create_project()
                if so_line.product_id.project_template_id:
                    map_so_project_templates[(so_line.order_id.id, so_line.product_id.project_template_id.id)] = project
                else:
                    map_so_project[so_line.order_id.id] = project
            elif not project:
                # Attach subsequent SO lines to the created project
                so_line.project_id = (
                        map_so_project_templates.get((so_line.order_id.id, so_line.product_id.project_template_id.id))
                        or map_so_project.get(so_line.order_id.id)
                )
            if so_line.product_id.service_tracking == 'task_in_project':
                if not project:
                    if so_line.product_id.project_template_id:
                        project = map_so_project_templates[(so_line.order_id.id, so_line.product_id.project_template_id.id)]
                    else:
                        project = map_so_project[so_line.order_id.id]
                if not so_line.task_id:
                    so_line._timesheet_create_task(project=project)
            so_line._generate_milestone()
            so_line._generate_phase()
