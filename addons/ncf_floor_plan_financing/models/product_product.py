# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    is_floor_plan_vehicle = fields.Boolean(
        string='Floor Plan Vehicle',
        help='Check if this product is a vehicle eligible for floor plan financing'
    )
    vin = fields.Char(
        string='VIN',
        size=17,
        help='Vehicle Identification Number (17 characters)',
        copy=False
    )
    floor_plan_dealer_id = fields.Many2one(
        'res.partner',
        string='Assigned Dealer',
        domain="[('is_floor_plan_dealer', '=', True)]",
        help='Dealer assigned to this vehicle'
    )
    floor_plan_state = fields.Selection([
        ('available', 'Available for Funding'),
        ('partially_funded', 'Partially Funded'),
        ('fully_funded', 'Fully Funded'),
        ('repaid', 'Repaid'),
    ], string='Floor Plan State', compute='_compute_floor_plan_state', store=True)
    
    floor_plan_agreement_line_ids = fields.One2many(
        'floor.plan.agreement.line',
        'vehicle_id',
        string='Floor Plan Lines'
    )
    
    total_funding_amount = fields.Monetary(
        string='Total Funded',
        compute='_compute_floor_plan_amounts',
        currency_field='currency_id',
        help='Total amount funded for this vehicle'
    )
    remaining_to_fund = fields.Monetary(
        string='Remaining to Fund',
        compute='_compute_floor_plan_amounts',
        currency_field='currency_id',
        help='Remaining amount available for funding'
    )
    floor_plan_lines_count = fields.Integer(
        string='Floor Plan Lines',
        compute='_compute_floor_plan_amounts'
    )
    
    @api.depends('floor_plan_agreement_line_ids.state', 
                 'floor_plan_agreement_line_ids.principal_remaining')
    def _compute_floor_plan_state(self):
        """Compute floor plan state based on agreement lines"""
        for product in self:
            if not product.is_floor_plan_vehicle or not product.floor_plan_agreement_line_ids:
                product.floor_plan_state = 'available'
            else:
                active_lines = product.floor_plan_agreement_line_ids.filtered(
                    lambda l: l.state in ['funded', 'partial']
                )
                if not active_lines:
                    product.floor_plan_state = 'repaid'
                elif any(line.principal_remaining > 0 for line in active_lines):
                    # Check if vehicle value is fully funded
                    total_funded = sum(active_lines.mapped('funded_amount'))
                    if product.list_price and total_funded >= product.list_price:
                        product.floor_plan_state = 'fully_funded'
                    else:
                        product.floor_plan_state = 'partially_funded'
                else:
                    product.floor_plan_state = 'repaid'
    
    @api.depends('floor_plan_agreement_line_ids.funded_amount',
                 'floor_plan_agreement_line_ids.topup_amount',
                 'floor_plan_agreement_line_ids.state')
    def _compute_floor_plan_amounts(self):
        """Compute total funding amounts"""
        for product in self:
            active_lines = product.floor_plan_agreement_line_ids.filtered(
                lambda l: l.state not in ['draft', 'cancelled']
            )
            product.total_funding_amount = sum(active_lines.mapped('funded_amount')) + \
                                           sum(active_lines.mapped('topup_amount'))
            product.remaining_to_fund = max(0, (product.list_price or 0) - product.total_funding_amount)
            product.floor_plan_lines_count = len(active_lines)
    
    @api.constrains('vin', 'is_floor_plan_vehicle')
    def _check_vin_unique(self):
        """Ensure VIN is unique for floor plan vehicles"""
        for product in self:
            if product.is_floor_plan_vehicle and product.vin:
                duplicate = self.search([
                    ('id', '!=', product.id),
                    ('vin', '=', product.vin),
                    ('is_floor_plan_vehicle', '=', True)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        f"VIN '{product.vin}' already exists for another floor plan vehicle: {duplicate.name}"
                    )
    
    @api.constrains('vin')
    def _check_vin_length(self):
        """Validate VIN length (should be 17 characters)"""
        for product in self:
            if product.is_floor_plan_vehicle and product.vin and len(product.vin) != 17:
                raise ValidationError(
                    f"VIN must be exactly 17 characters. Current VIN '{product.vin}' has {len(product.vin)} characters."
                )
    
    def action_view_floor_plan_lines(self):
        """Smart button action to view floor plan lines"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Floor Plan Funding Lines',
            'res_model': 'floor.plan.agreement.line',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id}
        }
