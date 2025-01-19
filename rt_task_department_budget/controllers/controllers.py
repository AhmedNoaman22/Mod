# -*- coding: utf-8 -*-
# from odoo import http


# class RtTaskDepartmentBudget(http.Controller):
#     @http.route('/rt_task_department_budget/rt_task_department_budget', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_task_department_budget/rt_task_department_budget/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_task_department_budget.listing', {
#             'root': '/rt_task_department_budget/rt_task_department_budget',
#             'objects': http.request.env['rt_task_department_budget.rt_task_department_budget'].search([]),
#         })

#     @http.route('/rt_task_department_budget/rt_task_department_budget/objects/<model("rt_task_department_budget.rt_task_department_budget"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_task_department_budget.object', {
#             'object': obj
#         })

