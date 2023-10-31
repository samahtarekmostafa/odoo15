from odoo import models, fields, api, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_width = fields.Float(string="Width", compute='get_dimension_data')
    product_length = fields.Float(string="Height", compute='get_dimension_data')
    product_area = fields.Float(string="Area", compute='get_dimension_data')

    def get_dimension_data(self):
        for rec in self:
            rec.product_width = rec.move_id.product_width
            rec.product_length = rec.move_id.product_length
            rec.product_area = rec.move_id.product_area
