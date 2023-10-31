from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_area = fields.Float(string="Area",)# compute="get_product_dimension_data")
    product_width = fields.Float(string="Width",)# compute="get_product_dimension_data")
    product_length = fields.Float(string="Height",)# compute="get_product_dimension_data")



    # def get_product_dimension_data(self):
    #     for rec in self:
    #         rec.product_width = rec.sale_line_ids.product_width
    #         rec.product_length = rec.sale_line_ids.product_length
    #         rec.product_area = rec.sale_line_ids.product_area
