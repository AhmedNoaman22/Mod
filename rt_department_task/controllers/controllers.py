# -*- coding: utf-8 -*-
# from odoo import http


# class RtDepartmentTask(http.Controller):
#     @http.route('/rt_department_task/rt_department_task', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_department_task/rt_department_task/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_department_task.listing', {
#             'root': '/rt_department_task/rt_department_task',
#             'objects': http.request.env['rt_department_task.rt_department_task'].search([]),
#         })

#     @http.route('/rt_department_task/rt_department_task/objects/<model("rt_department_task.rt_department_task"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_department_task.object', {
#             'object': obj
#         })

