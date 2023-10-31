from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    product_width = fields.Float(string="Width")
    product_length = fields.Float(string="Height")
    product_area = fields.Float(string="Area", compute='compute_area')
    area_type = fields.Selection([('area', 'Area'), ('linear', 'Linear'), ('none', 'None')], string="Area Select")
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, )
    get_larger = fields.Boolean()

    @api.onchange('area_type', 'product_length')
    def compute_area(self):
        for rec in self:
            if rec.product_width and rec.product_length:
                if rec.area_type == 'area':
                    rec.product_area = (rec.product_width * rec.product_length) / 10000
                elif rec.area_type == 'linear':
                    rec.product_area = ((rec.product_width + rec.product_length) * 2) / 100
                else:
                    rec.product_area = 1
            else:
                rec.product_area = 1
