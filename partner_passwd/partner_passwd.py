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
from openerp import SUPERUSER_ID
from lxml import etree
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import random
from Crypto.Cipher import AES
from Crypto import Random


import logging

_logger = logging.getLogger(__name__)

class res_partner_passwd(models.Model):
    _name = "res.partner.passwd"
    _description = "Password"

    def encrypt(self, cleartext, key):          #key = uuid
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        msg = iv + cipher.encrypt(cleartext)
        return msg.encode("hex")

    def decrypt(self, ciphertext, key):
        cipher=AES.new(key, AES.MODE_CFB, ciphertext.decode("hex")[:AES.block_size])
        return cipher.decrypt(ciphertext.decode("hex"))[AES.block_size:]

    def pw_Gen(self, pw_length = 15):
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./0:;<=>?@[\]^_`{|}~"
        password = ""
        random.seed()
        for i in range(pw_length):
            next_index = random.randrange(len(alphabet))
            password = password + alphabet[next_index]
        return password
            
    @api.one
#   generate a new password:    
    def generate_passwd(self):
        self.passwd=self.pw_Gen()
        return True

    service    = fields.Many2one('res.partner.service', readonly=True, states={'draft': [('readonly', False)]})
    name       = fields.Char(string='Name', index=True, readonly=True, states={'draft': [('readonly', False)]})  
    passwd     = fields.Char(string='Password', index=True, readonly=True, states={'draft': [('readonly', False)]})
    state      = fields.Selection([('draft','Draft'),('sent','Sent'),('cancel','Cancelled'),], string='Status', index=True, readonly=True, default='draft',
                    track_visibility='onchange', copy=False,
                    help=" * The 'Draft' status is used when the password is editable.\n"
                         " * The 'Sent' status is used when the password has been sent to the user.\n"
                         " * The'Cancelled'status is used when the password has been cancelled.\n")
    partner_id = fields.Many2one('res.partner')

    @api.one
#    def send_passwd(self, cr, uid, ids, context=None):
    def send_passwd(self):
        """ Sends the password to the users mail.
        """        
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        template = self.env.ref('account.email_template_edi_invoice', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',        #res.partner
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
        )
        self.passwd=self.encrypt(self.passwd, self.pool['ir.config_parameter'].get_param(self.env.cr, SUPERUSER_ID, 'database.uuid').replace('-', ''))
        self.state='sent'
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
        


    @api.one
    def edit_passwd(self):
        self.state='draft'
        self.passwd=self.decrypt(self.passwd, self.pool['ir.config_parameter'].get_param(self.env.cr, SUPERUSER_ID, 'database.uuid').replace('-', ''))
        return True

    @api.one
    def cancel_passwd(self):
        self.state='cancel'
        return True

    #@api.one
    #def read(self,cr,uid, *args, **kwargs):
    #    return super(res_partner_passwd, self).read(cr,uid, *args, **kwargs)

class res_partner(models.Model):
    _inherit = "res.partner"

    passwd_ids = fields.Many2many('res.partner.passwd','res_partner_passwd_rel','partner_id','passwd_id', string='Password',)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
