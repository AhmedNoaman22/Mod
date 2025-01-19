# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class rt_buget_phase(models.Model):
#     _name = 'rt_buget_phase.rt_buget_phase'
#     _description = 'rt_buget_phase.rt_buget_phase'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

