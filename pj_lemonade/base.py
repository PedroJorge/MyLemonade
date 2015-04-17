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

class res_users(osv.osv):
    _inherit = "res.users"
    
    def __get_users_child_of(self, cr, uid, context=None):
        if uid == SUPERUSER_ID:
            return self.search(cr, uid, [], context=context)
        else:
            cr.execute("""WITH RECURSIVE all_childs AS (
                            SELECT emp.id, rsc.user_id FROM hr_employee emp LEFT JOIN resource_resource rsc ON emp.resource_id = rsc.id WHERE rsc.user_id = %s
                          UNION ALL
                            SELECT emp.id, rsc.user_id
                            FROM hr_employee emp LEFT JOIN resource_resource rsc ON emp.resource_id = rsc.id ,all_childs childs
                            WHERE emp.parent_id = childs.id
                          )
                        SELECT user_id
                        FROM all_childs
                        """, (uid,))
            user_ids = cr.fetchall()
            if not user_ids or not user_ids[0]:
                user_ids = []
            else:
                user_ids = [ user[0] for user in user_ids ]
            return user_ids
    
    def _get_all_child(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for user_id in ids:
            res[user_id] = self.__get_users_child_of(cr, user_id, context=context)
        return res
    
    def search_childs(self, cr, uid, obj, name, args, context=None):
        return [('id','in',self.__get_users_child_of(cr, uid, context))]
    
    _columns = {
                'all_child_ids': fields.function(_get_all_child, type='many2many', relation='res.users', string='Child Domain', fnct_search=search_childs),
                }
    
    def create(self, cr, uid, vals, context=None):
        user_id = super(res_users, self).create(cr, uid, vals, context=context)
        self.pool.get('hr.employee').create(cr, uid, {
                                                      'user_id': user_id,
                                                      'name': vals.get('name'),
                                                      'active': vals.get('active', False),
                                                      }, context=context)
        return user_id
    
    def unlink(self, cr, uid, ids, context=None):
        employee_pool = self.pool.get('hr.employee')
        employee_ids = employee_pool.search(cr, uid, [('user_id', 'in', ids)], context=context)
        res = super(res_users, self).unlink(cr, uid, ids, context)
        employee_pool.write(cr, uid, employee_ids, {'active': False}, context=context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        if 'active' in vals:
            employee_pool = self.pool.get('hr.employee')
            employee_ids = employee_pool.search(cr, uid, [('user_id', 'in', ids)], context=context)
            employee_pool.write(cr, uid, employee_ids, {'active': vals['active']}, context=context)
        return super(res_users, self).write(cr, uid, ids, vals, context=context)
    
    
    