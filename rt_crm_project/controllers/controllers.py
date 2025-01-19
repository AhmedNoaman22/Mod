# -*- coding: utf-8 -*-
# from odoo import http


# class RtCrmProject(http.Controller):
#     @http.route('/rt_crm_project/rt_crm_project', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_crm_project/rt_crm_project/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_crm_project.listing', {
#             'root': '/rt_crm_project/rt_crm_project',
#             'objects': http.request.env['rt_crm_project.rt_crm_project'].search([]),
#         })

#     @http.route('/rt_crm_project/rt_crm_project/objects/<model("rt_crm_project.rt_crm_project"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_crm_project.object', {
#             'object': obj
#         })

