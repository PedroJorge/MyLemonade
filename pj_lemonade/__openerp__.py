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

{
    'name' : 'Lemonade - Gestão de Vendas e Recursos Humanos',
    'version' : '0.1',
    'author' : 'Pedro Jorge',
    'category' : 'Human Resources',
    'description' : """
                    
                    """,
    'sequence': 1,
    'website': '',
    'depends' : ['hr_gamification','document'],
    'data': [
             'data/groups.xml',
             'security/ir.model.access.csv',
             'wizard/grant_badge.xml',
             'hr.xml',
             'direct_sales.xml',
             ],
    'installable': True,
    'auto_install': False,
}

