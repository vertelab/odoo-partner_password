# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
def migrate(cr, version):
    cr.execute("select partner_id,passwd_id from res_partner_passwd_rel")
    links = cr.fetchall()
    for link in links:
        cr.execute("UPDATE res_partner_passwd SET partner_id=%s WHERE id=%s" % link)
    cr.execute('DROP TABLE res_partner_passwd_rel')
