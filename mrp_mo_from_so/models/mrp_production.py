from odoo import models, fields, api, _
from datetime import datetime


class BoM(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order')
    parent_mo_id = fields.Many2one('mrp.production')
    mrp_production_child_count_custom = fields.Integer(compute="compute_mrp_production_child_count")
    mrp_production_source_count = fields.Integer("Number of source MO", compute='compute_mrp_production_source_count')
    order_index = fields.Char()
    full_index = fields.Char()
    parent_index = fields.Char(related="parent_mo_id.full_index")
    so_line_id = fields.Many2one('sale.order.line')
    is_child = fields.Boolean()
    type = fields.Selection([('single', 'Single'), ('doublex', 'Doublex'), ('triplex', 'Triplex')])
    delivery_date = fields.Date(string="Delivery Date", related='sale_order_id.delivery_date')
    product_width = fields.Float(string="Width")
    product_length = fields.Float(string="Height")
    product_area = fields.Float(string="Area")
    date = fields.Date(compute="date_compute")
    mo_detail_ids = fields.Many2many('mo.detail')
    product_quant = fields.Integer(compute="compute_quant")
    order_subtotal = fields.Float(compute="compute_subtotal")

    def compute_subtotal(self):
        for rec in self:
            rec.order_subtotal = rec.product_area * rec.product_qty * rec.product_id.list_price

    def date_compute(self):
        for rec in self:
            rec.date = rec.date_planned_start.date()

    def compute_quant(self):
        for rec in self:
            rec.product_quant = int(rec.product_qty)

    def compute_area(self):
        for rec in self:
            if rec.is_child == False:
                rec.product_width = rec.so_line_id.product_width
                rec.product_length = rec.so_line_id.product_length
                rec.product_area = rec.so_line_id.product_area
            else:
                rec.product_width = rec.bom_id.product_width
                rec.product_length = rec.bom_id.product_length
                rec.product_area = rec.bom_id.product_area

    def button_mark_done(self):
        self.create_update_move_finished()

        return super(BoM, self).button_mark_done()

    def create_update_move_finished(self):
        list_move_finished = [(4, move.id) for move in self.move_finished_ids.filtered(
            lambda m: not m.byproduct_id and m.product_id != self.product_id)]
        list_move_finished = []
        moves_finished_values = self._get_moves_finished_values()
        moves_byproduct_dict = {move.byproduct_id.id: move for move in
                                self.move_finished_ids.filtered(lambda m: m.byproduct_id)}
        move_finished = self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id)
        for move_finished_values in moves_finished_values:
            if move_finished_values.get('byproduct_id') in moves_byproduct_dict:
                # update existing entries
                list_move_finished += [
                    (1, moves_byproduct_dict[move_finished_values['byproduct_id']].id, move_finished_values)]
            elif move_finished_values.get('product_id') == self.product_id.id and move_finished:
                list_move_finished += [(1, move_finished.id, move_finished_values)]
            else:
                # add new entries
                list_move_finished += [(0, 0, move_finished_values)]
        self.move_finished_ids = list_move_finished

    @api.model
    def create(self, vals):
        type = vals.get('type')
        order_index = vals.get('order_index')
        if type == 'single':
            suffix = ""
        elif type == 'doublex':
            suffix = "DGU#"
        elif type == 'triplex':
            suffix = "LAM#"
        else:
            suffix = ""
        vals['full_index'] = suffix + order_index

        return super(BoM, self).create(vals)

    def action_confirm(self):
        if self.sale_order_id:
            for moves in self.move_raw_ids:
                product = moves.product_id
                routes = product.route_ids
                for route in routes:
                    if route.name == "Replenish on Order (MTO)":
                        mto = route
                        product.route_ids -= mto
        return super(BoM, self).action_confirm()

    def compute_mrp_production_child_count(self):
        count_obj = self.search_count([('origin', '=', self.name)])
        self.mrp_production_child_count_custom = count_obj

    def compute_mrp_production_source_count(self):
        count_obj = self.search_count([('name', '=', self.parent_mo_id.name)])
        self.mrp_production_source_count = count_obj

    def action_view_mrp_production_childs_customes(self):
        self.ensure_one()
        mrp_production_ids = self.search([('origin', '=', self.name)]).ids
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
        }
        if len(mrp_production_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': mrp_production_ids[0],
            })
        else:
            action.update({
                'name': _("%s Child MO's") % self.name,
                'domain': [('id', 'in', mrp_production_ids)],
                'view_mode': 'tree,form',
            })
        return action

    def action_view_mrp_production_sources(self):
        self.ensure_one()
        mrp_production_ids = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.mrp_production_ids.ids
        mrp_production_ids = self.search([('name', '=', self.parent_mo_id.name)]).ids
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
        }
        if len(mrp_production_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': mrp_production_ids[0],
            })
        else:
            action.update({
                'name': _("MO Generated by %s") % self.name,
                'domain': [('id', 'in', mrp_production_ids)],
                'view_mode': 'tree,form',
            })
        return action
