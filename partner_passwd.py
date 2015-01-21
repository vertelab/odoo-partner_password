# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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

import itertools
from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp



class res_partner_passwd(models.Model):
    _name = "res.partner.passwd"
    _description = "Password"

    name       = fields.Char(string='Name', index=True, readonly=True, states={'draft': [('readonly', False)]})
    passwd     = fields.Char(string='Password', index=True, readonly=True, states={'draft': [('readonly', False)]})
    state      = fields.Selection([('draft','Draft'),('sent','Sent'),('cancel','Cancelled'),], string='Status', index=True, readonly=True, default='draft',
                    track_visibility='onchange', copy=False,
                    help=" * The 'Draft' status is used when ....\n"
                         " * ...\n"
                         " * ...\n")
    partner_id = fields.Many2one('res.partner')

class res_partner(models.Model):
    _inherit = "res.partner"

    passwd_ids = fields.Many2many('res.partner.passwd','res_partner_passwd_rel','partner_id','passwd_id', string='Password',)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
