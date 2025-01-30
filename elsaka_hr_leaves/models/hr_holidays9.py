from odoo.tools.translate import _
from odoo import fields, api, models
from odoo.exceptions import UserError
from odoo.addons.resource.models.utils import HOURS_PER_DAY
import time


class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    @api.onchange('from_time','to_time')
    def _get_total_hours(self):
        if self.from_time and self.to_time and self.from_time > self.to_time:
            raise UserError(_("From Time can not be grater than To Time"))

        str_fromtime = str(self.from_time)
        str_totime = str(self.to_time)

        fromhr = str_fromtime.split('.')[0]
        frommin = str_fromtime.split('.')[1]
        tohr = str_totime.split('.')[0]
        tomin = str_totime.split('.')[1]

        if len(frommin) == 1:
            frommin = frommin + '0'
        if len(tomin) == 1:
            tomin = tomin + '0'

        if int(fromhr) >= 24:
            self.from_time = False
            raise UserError(_("From Time Hours can not be equal or greater than 24."))
        if int(tohr) >= 24:
            self.to_time = False
            raise UserError(_("To Time Hours can not be equal or greater than 24."))
        if frommin >= '60':
            self.from_time = False
            raise UserError(_("From Time Minits can not be equal or greater than 60."))
        if tomin >= '60':
            self.to_time = False
            raise UserError(_("To Time Minits can not be equal or greater than 60."))

        if self.from_time and self.to_time:
            total_hours = self.convert_float_to_time(self.from_time, self.to_time)
            total_hours = self.revise_time(total_hours)
            self.total_hours = total_hours

    from_time = fields.Float('From')
    to_time = fields.Float('To')
    total_hours = fields.Float(string='Total Hours')
    appear_time_field = fields.Boolean(string="Appear Time Field")
    half_day = fields.Boolean('Half-Day Leave', readonly=True,
                              states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    half_day_type = fields.Selection([('first_half', 'First Half'), ('second_half', 'Second Half')],
                                     string="Type", readonly=True,
                                     states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

    def action_set_permission_values(self):
        for rec in self:
            rec.onchange_request_unit_hours()
            rec.onchange_from_hour()
            rec.onchange_to_hour()
            rec._get_total_hours()

    @api.onchange('request_unit_hours')
    def onchange_request_unit_hours(self):
        if self.request_unit_hours:
            self.appear_time_field = True

    @api.onchange('request_unit_half')
    def onchange_request_unit_half(self):
        if self.request_unit_half:
            self.half_day = True
        else:
            self.half_day = False

    @api.onchange('request_date_from_period')
    def onchange_request_date_from_period(self):
        if self.request_date_from_period == 'am':

            self.half_day_type = 'first_half'
        else:
            # stop
            self.half_day_type = 'second_half'
        self.number_of_days = 0.5

    @api.onchange('request_hour_from')
    def onchange_from_hour(self):
        if self.request_hour_from == '6':
            self.from_time = 6.00
        if self.request_hour_from == '6.5':
            self.from_time = 6.30
        if self.request_hour_from == '7':
            self.from_time = 7.00
        if self.request_hour_from == '7.5':
            self.from_time = 7.30
        if self.request_hour_from == '8':
            self.from_time = 8.00
        if self.request_hour_from == '8.5':
            self.from_time = 8.30
        if self.request_hour_from == '9':
            self.from_time = 9.00
        if self.request_hour_from == '9.5':
            self.from_time = 9.30
        if self.request_hour_from == '10':
            self.from_time = 10.00
        if self.request_hour_from == '10.5':
            self.from_time = 10.30
        if self.request_hour_from == '11':
            self.from_time = 11.00
        if self.request_hour_from == '11.5':
            self.from_time = 11.30
        if self.request_hour_from == '12':
            self.from_time = 12.0
        if self.request_hour_from == '12.5':
            self.from_time = 12.30
        if self.request_hour_from == '13':
            self.from_time = 13.0
        if self.request_hour_from == '13.5':
            self.from_time = 13.30
        if self.request_hour_from == '14':
            self.from_time = 14.0
        if self.request_hour_from == '14.5':
            self.from_time = 14.30
        if self.request_hour_from == '15':
            self.from_time = 15.0
        if self.request_hour_from == '15.5':
            self.from_time = 15.30
        if self.request_hour_from == '16':
            self.from_time = 16.0
        if self.request_hour_from == '16.5':
            self.from_time = 16.30
        if self.request_hour_from == '17':
            self.from_time = 17.0
        if self.request_hour_from == '17.5':
            self.from_time = 17.30
        if self.request_hour_from == '18':
            self.from_time = 18.0
        if self.request_hour_from == '18.5':
            self.from_time = 18.30
        if self.request_hour_from == '19':
            self.from_time = 19.0
        if self.request_hour_from == '19.5':
            self.from_time = 19.30
        if self.request_hour_from == '20':
            self.from_time = 20.0
        if self.request_hour_from == '20.5':
            self.from_time = 20.30
        if self.request_hour_from == '21':
            self.from_time = 21.0

    @api.onchange('request_hour_to')
    def onchange_to_hour(self):
        if self.request_hour_to == '6':
            self.to_time = 6.00
        if self.request_hour_to == '6.5':
            self.to_time = 6.30
        if self.request_hour_to == '7':
            self.to_time = 7.00
        if self.request_hour_to == '7.5':
            self.to_time = 7.30
        if self.request_hour_to == '8':
            self.to_time = 8.00
        if self.request_hour_to == '8.5':
            self.to_time = 8.30
        if self.request_hour_to == '9':
            self.to_time = 9.00
        if self.request_hour_to == '9.5':
            self.to_time = 9.30
        if self.request_hour_to == '10':
            self.to_time = 10.00
        if self.request_hour_to == '10.5':
            self.to_time = 10.30
        if self.request_hour_to == '11':
            self.to_time = 11.00
        if self.request_hour_to == '11.5':
            self.to_time = 11.30
        if self.request_hour_to == '12':
            self.to_time = 12.0
        if self.request_hour_to == '12.5':
            self.to_time = 12.30
        if self.request_hour_to == '13':
            self.to_time = 13.0
        if self.request_hour_to == '13.5':
            self.to_time = 13.30
        if self.request_hour_to == '14':
            self.to_time = 14.0
        if self.request_hour_to == '14.5':
            self.to_time = 14.30
        if self.request_hour_to == '15':
            self.to_time = 15.0
        if self.request_hour_to == '15.5':
            self.to_time = 15.30
        if self.request_hour_to == '16':
            self.to_time = 16.0
        if self.request_hour_to == '16.5':
            self.to_time = 16.30
        if self.request_hour_to == '17':
            self.to_time = 17.0
        if self.request_hour_to == '17.5':
            self.to_time = 17.30
        if self.request_hour_to == '18':
            self.to_time = 18.0
        if self.request_hour_to == '18.5':
            self.to_time = 18.30
        if self.request_hour_to == '19':
            self.to_time = 19.0
        if self.request_hour_to == '19.5':
            self.to_time = 19.30
        if self.request_hour_to == '20':
            self.to_time = 20.0
        if self.request_hour_to == '20.5':
            self.to_time = 20.30
        if self.request_hour_to == '21':
            self.to_time = 21.0

    @api.onchange('holiday_status_id')
    def onchange_holiday_status_id(self):
        if not self.name:
            self.name = self.holiday_status_id.name
        if self.holiday_status_id:
            self.appear_time_field = self.holiday_status_id.appear_time_field
        if self.appear_time_field:
            self.request_unit_half = False

    @api.constrains('holiday_status_id', 'date_from')
    def check_before_after_days(self):
        import datetime
        date_format = '%Y-%m-%d'
        today_str = time.strftime(date_format)
        for rec in self:
            if rec.date_from:
                today = datetime.datetime.strptime(time.strftime(date_format), date_format)

                if rec.holiday_status_id.can_be_req_before > 0:
                    temp_before = (today + datetime.timedelta(days=rec.holiday_status_id.can_be_req_before)).strftime(
                        date_format)
                    if rec.date_from.split(' ')[0] <= temp_before:
                        raise UserError(_('You can not take leave before %s days') % (temp_before))

                if rec.holiday_status_id.can_be_req_after > 0:
                    date_from_strptime = (datetime.datetime.strptime(rec.date_from.split(' ')[0], date_format))
                    allowed_date = (date_from_strptime + datetime.timedelta(
                        days=rec.holiday_status_id.can_be_req_after)).strftime(date_format)
                    if today_str < allowed_date:
                        raise UserError(_('You can only request after %s.') % (allowed_date))

    def convert_float_to_time(self, s1, s2):
        from datetime import datetime
        s1_str0 = len(str(s1).split('.')[0]) == 1 and '0' + str(s1).split('.')[0] or str(s1).split('.')[0]
        s1_str1 = len(str(s1).split('.')[1]) == 1 and str(s1).split('.')[1] + '0' or str(s1).split('.')[1]
        s2_str0 = len(str(s2).split('.')[0]) == 1 and '0' + str(s2).split('.')[0] or str(s2).split('.')[0]
        s2_str1 = len(str(s2).split('.')[1]) == 1 and str(s2).split('.')[1] + '0' or str(s2).split('.')[1]

        s1_str = s1_str0 + '.' + s1_str1
        s2_str = s2_str0 + '.' + s2_str1

        s1 = s1_str.split('.')[0] + ':' + s1_str.split('.')[1] + ':00'
        s2 = s2_str.split('.')[0] + ':' + s2_str.split('.')[1] + ':00'

        FMT = '%H:%M:%S'
        tdelta = str(datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT))
        tdelta = tdelta.split(':')[0] + '.' + tdelta.split(':')[1]
        return float(tdelta)

    def revise_time(self, float_val):
        hours = str(float_val).split('.')[0]
        mins = str(float_val).split('.')[1]
        if len(mins) == 1:
            mins = mins + '0'
        if int(mins) == 60:
            hours = int(hours) + 1
            mins = 0
        elif int(mins) > 60:
            hours = int(hours) + 1
            mins = int(mins) - 60
            if mins < 10:
                mins = '0' + str(mins)
        else:
            return float_val
        float_val = float(str(hours) + '.' + str(mins))
        return float_val

    def _prepare_employees_holiday_values(self, employees):
        res = super()._prepare_employees_holiday_values(employees)
        for rec in res:
            rec['from_time'] = self.from_time
            rec['to_time'] = self.to_time
            rec['appear_time_field'] = self.appear_time_field
            rec['request_unit_hours'] = self.request_unit_hours
            rec['request_unit_half'] = self.request_unit_half
            rec['request_hour_from'] = self.request_hour_from
            rec['request_date_to'] = self.request_date_to
        return res
