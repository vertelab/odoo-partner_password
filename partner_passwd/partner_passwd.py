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

import logging
_logger = logging.getLogger(__name__)
#Message appear if Crypto.Cipher is not installed
try:
    from Crypto.Cipher import AES
    from Crypto import Random
except ImportError:
    _logger.info("""You need Crypto.Cipher!
                install it by using the commando: apt-get install python-crypto """)



class res_partner_passwd(models.Model):
    _name = "res.partner.passwd"
    _description = "Password"

    def _encrypt(self, cleartext, key):          #key = uuid
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        msg = iv + cipher.encrypt(cleartext)
        return msg.encode("hex")

    def _decrypt(self, ciphertext, key):
        cipher=AES.new(key, AES.MODE_CFB, ciphertext.decode("hex")[:AES.block_size]) #You need Crypto.Cipher!
        return cipher.decrypt(ciphertext.decode("hex"))[AES.block_size:]

    def _get_key(self):
        return '0769382aa0a111e48be990489ab8facf'
        #return self.pool['ir.config_parameter'].get_param(self.env.cr, SUPERUSER_ID, 'database.uuid').replace('-', '')

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
    passwd     = fields.Char(string='Password', index=True, readonly=True, states={'draft': [('readonly', False)]}, default=pw_Gen)
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
            default_model='res.partner',        #res.partner
            default_res_id=self.id,
            default_use_template=bool(template),
            #default_template_id=template.id,
            default_composition_mode='comment',
            #mark_invoice_as_sent=True,
        )
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
    @api.returns('ir.ui.view')
    def open_mailform(self):
        """ Update form view id of action to open the invoice """
        return self.env.ref('base.view_partner_form')
    
        
    @api.one
    @api.returns('ir.actions.act_window')
    def xopen_mailform(self):
        """ Sends the password to the users mail.
        """        
     
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
#            'type': 'ir.actions.client',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'view_id': self.env.ref('base.view_partner_form'),

            #'views': [(compose_form.id, 'form')],
            #'view_id': self.env.ref('mail.email_compose_message_wizard_form'),
            'res_id': self.id,
            'target': 'new',
            
        }
     
        #return {
            #'name': _('Compose Email'),
            #'type': 'ir.actions.act_window',
##            'type': 'ir.actions.client',
            #'view_type': 'form',
            #'view_mode': 'form',
            #'res_model': 'mail.compose.message',
            ##'views': [(compose_form.id, 'form')],
            #'view_id': self.env.ref('mail.email_compose_message_wizard_form'),
            #'target': 'new',
            
        #}

    @api.one
    def edit_passwd(self):
        self.state='draft'
        return True

    @api.one
    def cancel_passwd(self):
        self.state='cancel'
        return True

    @api.v7
    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        result = super(res_partner_passwd, self).read(cr, user, ids, fields, context, load)
        for record in result:
            if 'passwd' in record:
                _logger.info('reading password 7 encrypted |%s|' % record['passwd'])
                try:
                    record['passwd'] = self._decrypt(record['passwd'], self._get_key())
                except TypeError:
                    pass
                _logger.info('reading password 7 cleartext |%s|' % record['passwd'])
        return result


    @api.v8
    def read(self, fields=None, load='_classic_read'):      #untested
        result = super(res_partner_passwd, self).read(fields, load)
        for record in result:
            if 'passwd' in record:
                _logger.info('reading password 8 encrypted |%s|' % record['passwd'])
                record['passwd'] = self._decrypt(record['passwd'], self._get_key())
                _logger.info('reading password 8 cleartext |%s|' % record['passwd'])
        return result

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if 'passwd' in vals:
            vals['passwd'] = self._encrypt(vals['passwd'], self._get_key())
            _logger.info('creating password |%s|' % vals['passwd'])
        return super(res_partner_passwd, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'passwd' in vals:
            vals['passwd'] = self._encrypt(vals['passwd'], self._get_key())
            _logger.info('writing password |%s|' % vals['passwd'])
        return super(res_partner_passwd, self).write(vals)

class res_partner(models.Model):
    _inherit = "res.partner"

    passwd_ids = fields.Many2many('res.partner.passwd','res_partner_passwd_rel','partner_id','passwd_id', string='Password',)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
