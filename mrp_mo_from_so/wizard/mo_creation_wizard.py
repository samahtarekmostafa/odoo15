from odoo import models, fields, api, _
from itertools import groupby
from odoo.exceptions import ValidationError


class MyWizard(models.TransientModel):
    _name = 'mo.wizard'

    name = fields.Char(related='product_id.name')
    get_larger = fields.Boolean()
    product_id = fields.Many2one('product.template')
    so_line_id = fields.Many2one('sale.order.line')
    product_ids = fields.Many2many('product.product')
    product_uom_qty = fields.Float()
    product_qty = fields.Integer(compute='product_quant')
    component_ids = fields.Many2many('mrp.bom', string="Components")
    sale_order_id = fields.Many2one('sale.order')
    type = fields.Selection([('single', 'Single'), ('doublex', 'Doublex'), ('triplex', 'Triplex')])
    index_number = fields.Char(string="Index No", related='so_line_id.index_number')
    product_width = fields.Float(string="Width")
    product_length = fields.Float(string="Height")
    product_area = fields.Float(string="Area")
    area_type = fields.Selection([('area', 'Area'), ('linear', 'Linear')], string="Area Select")

    def product_quant(self):
        for rec in self:
            if rec.product_uom_qty:
                rec.product_qty = int(rec.product_uom_qty)
            else:
                rec.product_qty = 0

    def create_sub_bom(self, products_list, origin, parent_mo, width, length, area):
        for rec in self:
            rec.so_line_id.parent_mo_id = parent_mo.id
            rec.so_line_id.full_index = parent_mo.full_index
            company_id = self.env.company
            src_domain = [('company_id', '=', company_id.id), ('usage', '=', 'internal')]
            dest_domain = [('company_id', '=', company_id.id), ('name', '=', 'Production')]
            src_locations = self.env['stock.location'].search(src_domain)[0]
            dest_locations = self.env['stock.location'].search(dest_domain)[0]
            product_index = 0
            for product, qty in products_list.items():
                product_index += 1
                product_obj_tmpl = self.env['product.template'].browse(product.id)
                # Create Moves for Sub Product Glass A and Glass B
                sub_products_boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_obj_tmpl.id)])[-1]
                sub_products = sub_products_boms.product_tmpl_id.product_variant_id
                sub_moves_list = []
                for items in sub_products_boms.bom_line_ids:
                    values = {
                        'product_id': items.product_id.id,
                        'name': items.product_id.name,
                        'product_uom': items.product_id.uom_id.id,
                        'location_id': src_locations.id,
                        'location_dest_id': dest_locations.id,
                    }
                    sub_moves = self.env['stock.move'].create(values)
                    sub_moves_list.append(sub_moves.id)
                pro_index = "S#" + str(product_index)
                mo = self.env['mrp.production'].create({
                    'product_id': sub_products.id,
                    'origin': origin,
                    'is_child': True,
                    'product_width': width,
                    'product_length': length,
                    'product_area': area,
                    'parent_mo_id': parent_mo.id,
                    'product_qty': sub_products_boms.product_qty,
                    'order_index': pro_index,
                    'bom_id': sub_products_boms.id,
                    'product_uom_id': sub_products.uom_id.id,
                    'move_raw_ids': sub_moves_list,
                })
                quant_list = []
                for quant in range(rec.product_qty):
                    mo_quant = self.env['mo.detail'].create({
                        'name': mo.name + "-" + str(quant + 1),
                    })
                    quant_list.append(mo_quant.id)
                mo.update({
                    'mo_detail_ids': quant_list,
                })
                rec.so_line_id.related_mo_ids += mo
                rec.sale_order_id.related_mo_ids += mo


    def create_mo_from_boms(self):
        for rec in self:
            self.get_larger_area()
            self.so_line_id.compute_amount()
            company_id = self.env.company
            products_list = {}
            single_product_list = {}
            moves_list = []
            src_domain = [('company_id', '=', company_id.id), ('usage', '=', 'internal')]
            dest_domain = [('company_id', '=', company_id.id), ('name', '=', 'Production')]
            src_locations = self.env['stock.location'].search(src_domain)[0]
            dest_locations = self.env['stock.location'].search(dest_domain)[0]
            for boms in rec.component_ids:
                products_list.update({boms.product_tmpl_id: boms.product_qty})
            for products in rec.product_ids:
                product_rec = self.env['product.product'].search([('name', '=', products.name)])
                rec.so_line_id.related_products_ids += product_rec
                single_product_list.update({product_rec: 1})
            for product, qty in products_list.items():
                product_object_tmpl = self.env['product.template'].browse(product.id)
                product_obj = product_object_tmpl.product_variant_id
                # Create Moves for Sub Product Glass A and Glass B
                vals = {
                    'product_id': product_obj.id,
                    'name': product_obj.name,
                    'product_uom_qty': qty,
                    'product_uom': product_obj.uom_id.id,
                    'location_id': src_locations.id,
                    'location_dest_id': dest_locations.id,
                }
                moves = self.env['stock.move'].create(vals)
                moves_list.append(moves.id)
            for product, qty in single_product_list.items():
                product_object = self.env['product.product'].browse(product.id)
                # Create Moves for Sub Product Glass A and Glass B
                vals = {
                    'product_id': product_object.id,
                    'name': product_object.name,
                    'product_uom_qty': qty,
                    'product_uom': product_object.uom_id.id,
                    'location_id': src_locations.id,
                    'location_dest_id': dest_locations.id,
                }
                moves = self.env['stock.move'].create(vals)
                moves_list.append(moves.id)
            mo = self.env['mrp.production'].create({
                'product_id': rec.product_id.product_variant_id.id,
                'order_index': rec.index_number,
                'type': rec.type,
                'product_width': rec.so_line_id.product_width,
                'product_length': rec.so_line_id.product_length,
                'product_area': rec.so_line_id.product_area,
                'so_line_id': rec.so_line_id.id,
                'product_qty': rec.product_uom_qty,
                'product_uom_id': rec.product_id.uom_id.id,
                'move_raw_ids': moves_list,
            })
            quant_list = []
            for quant in range(rec.product_qty):
                mo_quant = self.env['mo.detail'].create({
                    'name': mo.name + "-" + str(quant + 1),
                })
                quant_list.append(mo_quant.id)
            mo.update({
                'mo_detail_ids': quant_list,
            })
            width = rec.so_line_id.product_width
            length = rec.so_line_id.product_length
            area = rec.so_line_id.product_area
            rec.so_line_id.related_mo_ids += mo
            rec.sale_order_id.related_mo_ids += mo
            origin = mo.name
            parent_mo = mo
            self.create_sub_bom(products_list, origin, parent_mo, width, length, area)

    def get_larger_area(self):
        for rec in self:
            if rec.get_larger == True:
                products_width = []
                products_length = []
                area_type = []
                company_id = self.env.company
                for boms in rec.component_ids:
                    products_width.append(boms.product_width)
                    products_length.append(boms.product_length)
                    area_type.append(boms.area_type)

                if rec.get_larger == True:
                    max_width = max(products_width)
                    max_length = max(products_length)
                    rec.so_line_id.product_width = max_width
                    rec.so_line_id.product_length = max_length
                    rec.so_line_id.area_type = area_type[0]
                else:
                    if products_width.count(products_width[0]) == len(products_width) and products_length.count(
                            products_length[0]) == len(products_length):
                        rec.so_line_id.product_width = products_width[0]
                        rec.so_line_id.product_length = products_length[0]
                        rec.so_line_id.area_type = area_type[0]
                    else:
                        raise ValidationError(_("Not Identical Measures"))



