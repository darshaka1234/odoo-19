# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardTopupRequest(models.TransientModel):
    _name = 'wizard.topup.request'
    _description = 'Top-up Request Wizard'
    
    agreement_line_id = fields.Many2one(
        'floor.plan.agreement.line',
        string='Original Funding Line',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    
    # Display fields from original line
    vehicle_id = fields.Many2one(
        'product.product',
        related='agreement_line_id.vehicle_id',
        readonly=True
    )
    vin = fields.Char(
        related='agreement_line_id.vin',
        readonly=True
    )
    dealer_id = fields.Many2one(
        'res.partner',
        related='agreement_line_id.dealer_id',
        readonly=True
    )
    investor_id = fields.Many2one(
        'res.partner',
        related='agreement_line_id.investor_id',
        readonly=True
    )
    current_funded_amount = fields.Monetary(
        string='Current Funded Amount',
        related='agreement_line_id.funded_amount',
        currency_field='currency_id',
        readonly=True
    )
    current_interest_rate = fields.Float(
        string='Current Interest Rate',
        related='agreement_line_id.interest_rate',
        readonly=True
    )
    
    # Top-up request fields
    topup_amount = fields.Monetary(
        string='Top-up Amount',
        required=True,
        currency_field='currency_id',
        help='Additional funding amount requested'
    )
    new_interest_rate = fields.Float(
        string='New Interest Rate (%)',
        help='Leave empty to use the same rate as original line'
    )
    use_same_rate = fields.Boolean(
        string='Use Same Interest Rate',
        default=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    
    reason = fields.Text(
        string='Reason for Top-up',
        required=True
    )
    
    @api.onchange('use_same_rate')
    def _onchange_use_same_rate(self):
        """Set rate based on checkbox"""
        if self.use_same_rate:
            self.new_interest_rate = self.current_interest_rate
        else:
            self.new_interest_rate = 0.0
    
    def action_create_topup(self):
        """Create new funding line for top-up"""
        self.ensure_one()
        
        if self.topup_amount <= 0:
            raise UserError(_('Top-up amount must be greater than zero.'))
        
        # Determine interest rate
        if self.use_same_rate or not self.new_interest_rate:
            interest_rate = self.current_interest_rate
        else:
            interest_rate = self.new_interest_rate
        
        # Create new funding line
        new_line = self.agreement_line_id.action_request_topup(
            topup_amount=self.topup_amount,
            new_interest_rate=interest_rate
        )
        
        # Add reason to notes
        new_line.write({
            'notes': f'Top-up request: {self.reason}'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Top-up Funding Line'),
            'res_model': 'floor.plan.agreement.line',
            'res_id': new_line.id,
            'view_mode': 'form',
            'target': 'current',
        }
