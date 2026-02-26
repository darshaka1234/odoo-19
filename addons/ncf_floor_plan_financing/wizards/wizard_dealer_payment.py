# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardDealerPayment(models.TransientModel):
    _name = 'wizard.dealer.payment'
    _description = 'Dealer Payment Wizard'
    
    agreement_line_id = fields.Many2one(
        'floor.plan.agreement.line',
        string='Funding Line',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    payment_type = fields.Selection([
        ('interest', 'Interest Payment'),
        ('principal', 'Principal Repayment'),
    ], string='Payment Type', required=True, default='interest')
    
    amount = fields.Monetary(
        string='Payment Amount',
        required=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Display fields
    outstanding_interest = fields.Monetary(
        string='Outstanding Interest',
        related='agreement_line_id.interest_outstanding',
        currency_field='currency_id',
        readonly=True
    )
    principal_remaining = fields.Monetary(
        string='Principal Remaining',
        related='agreement_line_id.principal_remaining',
        currency_field='currency_id',
        readonly=True
    )
    
    payment_date = fields.Date(
        string='Payment Date',
        default=fields.Date.context_today,
        required=True
    )
    notes = fields.Text(string='Notes')
    
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        """Suggest max amount based on payment type"""
        if self.payment_type == 'interest':
            self.amount = self.outstanding_interest
        elif self.payment_type == 'principal':
            self.amount = self.principal_remaining
    
    def action_process_payment(self):
        """Process dealer payment"""
        self.ensure_one()
        
        if self.amount <= 0:
            raise UserError(_('Payment amount must be greater than zero.'))
        
        if self.payment_type == 'interest':
            # Process interest payment
            self.agreement_line_id.action_receive_dealer_interest(self.amount)
            message = _('Interest payment of %.2f received from dealer.') % self.amount
        elif self.payment_type == 'principal':
            # Process principal repayment
            self.agreement_line_id.action_receive_principal_repayment(self.amount)
            message = _('Principal repayment of %.2f received from dealer.') % self.amount
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Processed'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
