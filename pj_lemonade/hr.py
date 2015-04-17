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
from openerp import tools
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class hr_team(osv.osv):
    _name = "hr.team"
    _description = "Team"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)
    
    _columns = {
                'name': fields.char('Name', required=True),
                'employee_id': fields.many2one('hr.employee', 'Team Leader', ondelete='set null'),
                'image': fields.binary("Team Image"),
                'image_medium': fields.function(_get_image, fnct_inv=_set_image, string="Medium-sized image", type="binary", multi="get_image", store = {'hr.team': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10)}),
                'image_small': fields.function(_get_image, fnct_inv=_set_image, string="Small-sized photo", type="binary", multi="get_image", store = {'hr.team': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10)}),
                'employee_ids': fields.one2many('hr.employee', 'team_id', 'Team Members'),
                }

class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    _columns = {
                'team_id': fields.many2one('hr.team', 'Team', ondelete='set null'),
                'job': fields.selection([('distributor', 'Distributor'), ('leader','Leader'), ('assistance_manager', 'Assistance Manager'), ('manager', 'Manager')], 'Job', required=True)
                }
    
    _defaults = {
                 'job': 'distributor',
                 }
    
    def __get_job_group(self, cr, uid, job, context=None):
        if job == 'distributor':
            xml_id = 'group_direct_sales_distributor'
        elif job == 'leader':
            xml_id = 'group_direct_sales_leader'
        elif job == 'assistance_manager':
            xml_id = 'group_direct_sales_assistance_manager'
        elif job == 'manager':
            xml_id = 'group_direct_sales_manager'
        else:
            return False
        return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'pj_lemonade', xml_id)[1]
    
    def __set_user_with_job(self, cr, uid, user_id, job, context=None):
        if not user_id or not job:
            return False
        group_id = self.__get_job_group(cr, uid, job, context=context)
        
        if not group_id:
            return False
        
        return self.pool.get('res.users').write(cr, uid, [user_id], {'groups_id': [(4, group_id)]}, context=context)
        
    def create(self, cr, uid, vals, context=None):
        employee_id = super(hr_employee, self).create(cr, uid, vals, context)
        
        if 'user_id' in vals and vals['user_id']:
            self.__set_user_with_job(cr, uid, vals['user_id'], 'distributor', context)
        
        return employee_id
    
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
                        SELECT id
                        FROM all_childs
                        """, (uid,))
            employee_ids = cr.fetchall()
            if not employee_ids or not employee_ids[0]:
                employee_ids = []
            else:
                employee_ids = [ employee[0] for employee in employee_ids ]
            return employee_ids
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if uid != SUPERUSER_ID and context and context.get('employee_child_domain', False):
            if not args:
                args = []
            args.append( ('id','in',self.__get_users_child_of(cr, uid, context)) )
        return super(hr_employee, self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
    
    def search_read(self, cr, uid, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        if uid != SUPERUSER_ID and context and context.get('employee_child_domain', False):
            if not domain:
                domain = []
            domain.append( ('id','in',self.__get_users_child_of(cr, uid, context)) )
        return super(hr_employee, self).search_read(cr, uid, domain, fields, offset, limit, order, context)
    
    def btn_promote(self, cr, uid, ids, context=None):
        for employee in self.browse(cr, uid, ids, context=context):
            if employee.user_id:
                job = employee.job
                if job == 'distributor':
                    new_job = 'leader'
                elif job == 'leader':
                    new_job = 'assistance_manager'
                elif job == 'assistance_manager':
                    new_job = 'manager'
                else:
                    continue
                self.__set_user_with_job(cr, uid, employee.user_id.id, new_job, context=context)
                self.write(cr, uid, [employee.id], {'job': new_job}, context=context)
        return True
    
    def btn_demote(self, cr, uid, ids, context=None):
        for employee in self.browse(cr, uid, ids, context=context):
            if employee.user_id:
                job = employee.job
                if job == 'leader':
                    new_job = 'distributor'
                elif job == 'assistance_manager':
                    new_job = 'leader'
                elif job == 'manager':
                    new_job = 'assistance_manager'
                else:
                    continue
                
                group_job_id = self.__get_job_group(cr, uid, job, context=context)
                for group in employee.user_id.groups_id:
                    if group.id == group_job_id:
                        group.write({'users': [(3, employee.user_id.id)]})
                        break
                
                self.__set_user_with_job(cr, uid, employee.user_id.id, new_job, context=context)
                self.write(cr, uid, [employee.id], {'job': new_job}, context=context)
        return True
        
    
    
    