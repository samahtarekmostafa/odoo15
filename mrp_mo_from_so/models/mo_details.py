from odoo import models, fields, api, _


class MoQuantity(models.Model):
    _name = "mo.detail"
    _description = "desc.detail"

    name = fields.Char()
    parent_mo_id = fields.Many2one('mrp.production')
