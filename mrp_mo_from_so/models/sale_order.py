from odoo import api, fields, models, _


class SaleOrderInheritance(models.Model):
    _inherit = 'sale.order'

    total_areas = fields.Float(string="Total Area", compute='compute_total_areas')
    delivery_date = fields.Date(string="Delivery Date")
    related_mo_ids = fields.Many2many('mrp.production')
    related_products_id = fields.Many2many('product.product')

    @api.depends('order_line')
    def compute_total_areas(self):
        for rec in self:
            list_areas = []
            for lines in rec.order_line:
                if lines.product_width > 0 and lines.product_length > 0:
                    sum_totals = lines.product_area * lines.product_uom_qty
                    list_areas.append(sum_totals)

            rec.total_areas = sum(list_areas)

    def action_view_mrp_production_customes(self):
        self.ensure_one()
        mrp_production_ids = self.related_mo_ids.ids
        mrp_production = self.related_mo_ids
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
        }
        ids_list = []
        for ids in mrp_production:
            if ids.is_child == False:
                ids_list.append(ids)

        if len(ids_list) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': mrp_production_ids[0],
            })
        else:
            action.update({
                'name': _("%s Child MO's") % self.name,
                'domain': [('id', 'in', mrp_production_ids), ('is_child', '=', False)],
                'view_mode': 'tree,form',
            })
        return action
