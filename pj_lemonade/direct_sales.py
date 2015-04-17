# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import time

class schedule_seat_down_meeting(osv.osv):
    _name = "schedule.seat.down.meeting"
    _description = "Seat Down Meeting Schedule"
    _inherit = ['ir.needaction_mixin']
    _order = 'date_time DESC'
    _rec_name = 'date_time'
    
    def _is_user_request(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for schedule_vals in self.read(cr, uid, ids, ['user_id', 'requesting_user_id'], context=context):
            res[schedule_vals['id']] = {
                                        'is_requesting_user': schedule_vals['requesting_user_id'][0] == uid,
                                        'is_requested_user': schedule_vals['user_id'][0] == uid,
                                        }
        return res
    
    _columns = {
                'date_time': fields.datetime('Date/time', required=True),
                'user_id': fields.many2one('res.users', 'Seat Down With', required=True, ondelete='cascade'),
                'requesting_user_id': fields.many2one('res.users', 'Requesting Seat Down', required=True, readonly=True, ondelete='cascade'),
                'request_obs': fields.text('Requesting Observations'),
                'confirm_obs': fields.text('Confirmation Observations'),
                'state': fields.selection([('draft','Draft'),('draft_request', 'Waiting Approval'), ('draft_reschedule', 'Waiting Approval'), ('approved', 'Approved'), ('canceled', 'Canceled')], 'State', required=True),   
                'duration': fields.float('Duration'),
                'is_requesting_user': fields.function(_is_user_request, type='boolean', multi='user_request'),
                'is_requested_user': fields.function(_is_user_request, type='boolean', multi='user_request'),
                }
    
    _defaults = {
                 'requesting_user_id': lambda s,cr,uid,c: uid,
                 'state': 'draft',
                 'is_requesting_user': True,
                 }
    
    def btn_request_seatdown(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft_request'}, context=context)
    
    def btn_confirm_seatdown(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'approved'}, context=context)
    
    def btn_reschedule_seatdown(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft_reschedule'}, context=context)
    
    def btn_cancel_seatdown(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'canceled'}, context=context)
    
    def _needaction_domain_get(self, cr, uid, context=None):
        return ['|','&',('state', '=', 'draft_request'),('user_id', '=', uid),'&',('state', '=', 'draft_reschedule'),('requesting_user_id', '=', uid)]

class direct_sale_street(osv.osv):
    _name = "direct.sale.street"
    _description = "Direct Sale Street"
    _order = 'street, number'
    
    _columns = {
                'street': fields.char('Street'),
                'number': fields.char('Number'),
                'floor': fields.char('Floor'),
                'obs': fields.char('Observations'),
                'direct_sale_id': fields.many2one('direct.sale', 'Sale', required=True, ondelete='cascade'),
                }
    
class direct_sale(osv.osv):
    _name = "direct.sale"
    _description = "Direct Sale"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'date'
    _order = 'date DESC'
    
    def efficiency_calc(self, output, input):
        if not output or not input:
            return 0.0
        else:
            return float(output)/input*100
    
    def _efficiency(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for direct_sale_id in ids:
            direct_sale_vals = self.read(cr, uid, direct_sale_id, ['sales_number', 'people_approached'], context=context)
            res[direct_sale_id] = self.efficiency_calc(direct_sale_vals['sales_number'], direct_sale_vals['people_approached'])
        return res
    
    def _views(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for direct_sale_id in ids:
            direct_sale_vals = self.read(cr, uid, direct_sale_id, ['sales_number', 'people_approached', 'efficiency'], context=context)
            res[direct_sale_id] = {
                                   'people_approached_view': _('People') + ': ' + str( direct_sale_vals['people_approached'] or 0 ),
                                   'sales_number_view': _('Sales') + ': ' + str( direct_sale_vals['sales_number'] or 0 ),
                                   'efficiency_view': _('Efficiency') + ': ' + '%.2f' % ( direct_sale_vals['efficiency'] or 0.0 ) + '%',
                                   }
        return res
    
    def __get_users_child_of(self, cr, uid, context=None):
        if uid == SUPERUSER_ID:
            return self.pool.get('hr.employee').search(cr, uid, [], context=context)
        else:
            cr.execute("""WITH RECURSIVE all_childs AS (
                            SELECT emp.id, rsc.user_id FROM hr_employee emp LEFT JOIN resource_resource rsc ON emp.resource_id = rsc.id WHERE rsc.user_id = %s
                          UNION ALL
                            SELECT emp.id, rsc.user_id
                            FROM hr_employee emp LEFT JOIN resource_resource rsc ON emp.resource_id = rsc.id ,all_childs childs
                            WHERE emp.parent_id = childs.id
                          )
                        SELECT id
                        FROM all_childs
                        """, (uid,))
            employee_ids = cr.fetchall()
            if not employee_ids or not employee_ids[0]:
                employee_ids = []
            else:
                employee_ids = [ employee[0] for employee in employee_ids ]
            return employee_ids
    
    def _get_all_childs(self, cr, uid, ids, field_name, args, context=None):
        user_ids = self.__get_users_child_of(cr, uid, context=context)
        return dict.fromkeys(ids, user_ids)
            
    _columns = {
                'date': fields.date('Date', required=True),
                'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
                'doors': fields.integer('Nº of Doors'),
                'people_approached': fields.integer('Nº of People'),
                'sale_bh': fields.integer('Nº of BH'),
                'sale_apr': fields.integer('Nº of Apr'),
                'sale_f1': fields.integer('Nº of F1'),
                'sales_number': fields.integer('Nº of F2'),
                'efficiency': fields.function(_efficiency, type="float", string="Efficiency(%)", store={'direct.sale': (lambda self,cr,uid,ids,ctx=None: ids, ['sales_number','people_approached'], 10)}),
                'observations': fields.text('Observations'),
                'sales_number_view': fields.function(_views, type='char', strin='Nº of Sales', multi='views'),
                'people_approached_view': fields.function(_views, type='char', strin='Nº of People Approached', multi='views'),
                'efficiency_view': fields.function(_views, type="char", string="Efficiency(%)", multi='views'),
                'objectives': fields.char('Objectives'),
                'street_ids': fields.one2many('direct.sale.street', 'direct_sale_id', 'Addresses'),
                'all_child_ids': fields.function(_get_all_childs, type='many2many', relation='res.users', string='Child Domain'),
                }
    
    _sql_constraints = [
        ('date_employee_uniq', 'unique (date,employee_id)', 'You can only create a direct sale for each day once per employee!')
    ]
    
    def _current_employee(self, cr, uid, context=None):
        employee = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if employee:
            return employee[0]
        else:
            return False
    
    _defaults = {
                 'date': time.strftime('%Y-%m-%d'),
                 'employee_id': _current_employee,
                 'all_child_ids': __get_users_child_of,
                 }
        
    def search_read(self, cr, uid, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        if uid != SUPERUSER_ID:
            if not domain:
                domain = []
            domain.append( ('employee_id','in',self.__get_users_child_of(cr, uid, context)) )
        return super(direct_sale, self).search_read(cr, uid, domain, fields, offset, limit, order, context)
    
    def onchange_sales_number(self, cr, uid, ids, sales_number, people_approached, context=None):
        return {'value': { 'efficiency': self.efficiency_calc(sales_number, people_approached) }}
    
    def onchange_people_approached(self, cr, uid, ids, people_approached, sales_number, context=None):
        return {'value': { 'efficiency': self.efficiency_calc(sales_number, people_approached) }}
