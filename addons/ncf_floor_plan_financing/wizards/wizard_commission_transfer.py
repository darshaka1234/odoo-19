# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardCommissionTransfer(models.TransientModel):
    _name = 'wizard.commission.transfer'
    _description = 'Commission Transfer Wizard'
    
    accumulated_commission = fields.Monetary(
        string='Accumulated Commission',
        compute='_compute_accumulated_commission',
        currency_field='currency_id',
        readonly=True,
        help='Total commission earned and not yet transferred'
    )
    
    transfer_amount = fields.Monetary(
        string='Transfer Amount',
        required=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    
    transfer_date = fields.Date(
        string='Transfer Date',
        default=fields.Date.context_today,
        required=True
    )
    
    notes = fields.Text(string='Notes')
    
    # Display breakdown
    total_interest_earned = fields.Monetary(
        string='Total Interest Earned',
        compute='_compute_commission_breakdown',
        currency_field='currency_id'
    )
    total_commission_earned = fields.Monetary(
        string='Total Commission Earned',
        compute='_compute_commission_breakdown',
        currency_field='currency_id'
    )
    
    @api.depends('transfer_date')
    def _compute_accumulated_commission(self):
        """Calculate accumulated commission income"""
        for wizard in self:
            # Query commission income account balance
            commission_account = self.env.ref('ncf_floor_plan_financing.account_commission_income')
            
            # Get balance from account move lines
            domain = [
                ('account_id', '=', commission_account.id),
                ('parent_state', '=', 'posted'),
                ('date', '<=', wizard.transfer_date)
            ]
            move_lines = self.env['account.move.line'].search(domain)
            
            # Commission income is credit balance
            total_credit = sum(move_lines.mapped('credit'))
            total_debit = sum(move_lines.mapped('debit'))
            wizard.accumulated_commission = total_credit - total_debit
    
    @api.depends('transfer_date')
    def _compute_commission_breakdown(self):
        """Calculate commission breakdown"""
        for wizard in self:
            # Get all posted interest calculation transactions
            transactions = self.env['floor.plan.transaction'].search([
                ('transaction_type', '=', 'interest_calculated'),
                ('state', '=', 'posted'),
                ('transaction_date', '<=', wizard.transfer_date)
            ])
            
            wizard.total_interest_earned = sum(transactions.mapped('amount'))
            
            # Calculate commission from interest
            total_commission = 0
            for trans in transactions:
                line = trans.agreement_line_id
                commission_rate = line.commission_rate / 100
                commission_amount = trans.amount * commission_rate
                total_commission += commission_amount
            
            wizard.total_commission_earned = total_commission
    
    @api.onchange('accumulated_commission')
    def _onchange_accumulated_commission(self):
        """Set transfer amount to full accumulated commission"""
        if self.accumulated_commission > 0:
            self.transfer_amount = self.accumulated_commission
    
    def action_transfer_commission(self):
        """Transfer commission to platform bank"""
        self.ensure_one()
        
        if self.transfer_amount <= 0:
            raise UserError(_('Transfer amount must be greater than zero.'))
        
        if self.transfer_amount > self.accumulated_commission:
            raise UserError(
                _('Transfer amount (%.2f) exceeds accumulated commission (%.2f).') % 
                (self.transfer_amount, self.accumulated_commission)
            )
        
        # Process commission transfer
        move = self.env['floor.plan.agreement.line'].action_transfer_commission(self.transfer_amount)
        
        if self.notes:
            move.write({'narration': self.notes})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Commission Transferred'),
                'message': _('Successfully transferred %.2f to platform bank.') % self.transfer_amount,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': move.id,
                    'view_mode': 'form',
                }
            }
        }
