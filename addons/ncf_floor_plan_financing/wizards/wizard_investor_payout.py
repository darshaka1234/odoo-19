# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardInvestorPayout(models.TransientModel):
    _name = 'wizard.investor.payout'
    _description = 'Investor Interest Payout Wizard'
    
    line_ids = fields.One2many(
        'wizard.investor.payout.line',
        'wizard_id',
        string='Payout Lines'
    )
    total_payout = fields.Monetary(
        string='Total Payout',
        compute='_compute_total_payout',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    
    @api.depends('line_ids.payout_amount')
    def _compute_total_payout(self):
        """Calculate total payout amount"""
        for wizard in self:
            wizard.total_payout = sum(wizard.line_ids.mapped('payout_amount'))
    
    @api.model
    def default_get(self, fields_list):
        """Populate lines with pending investor payouts"""
        res = super().default_get(fields_list)
        
        # Get all funded lines with paid interest
        lines = self.env['floor.plan.agreement.line'].search([
            ('state', 'in', ['funded', 'partial']),
            ('interest_paid', '>', 0)
        ])
        
        # Group by investor and calculate payable amounts
        investor_data = {}
        for line in lines:
            investor = line.investor_id
            if investor.id not in investor_data:
                investor_data[investor.id] = {
                    'investor_id': investor.id,
                    'total_interest_paid': 0,
                    'commission_rate': line.commission_rate,
                    'lines': []
                }
            investor_share_rate = 1 - (line.commission_rate / 100)
            line_payable = line.interest_paid * investor_share_rate
            investor_data[investor.id]['total_interest_paid'] += line_payable
            investor_data[investor.id]['lines'].append(line.id)
        
        # Create wizard lines
        line_vals = []
        for inv_id, data in investor_data.items():
            if data['total_interest_paid'] > 0:
                line_vals.append((0, 0, {
                    'investor_id': inv_id,
                    'available_amount': data['total_interest_paid'],
                    'payout_amount': data['total_interest_paid'],
                    'agreement_line_ids': [(6, 0, data['lines'])]
                }))
        
        res['line_ids'] = line_vals
        return res
    
    def action_process_payouts(self):
        """Process selected investor payouts"""
        self.ensure_one()
        
        selected_lines = self.line_ids.filtered(lambda l: l.payout_amount > 0)
        if not selected_lines:
            raise UserError(_('No payouts selected.'))
        
        for line in selected_lines:
            # Process payout for each agreement line proportionally
            total_to_pay = line.payout_amount
            for agreement_line in line.agreement_line_ids:
                investor_share_rate = 1 - (agreement_line.commission_rate / 100)
                line_max_payable = agreement_line.interest_paid * investor_share_rate
                
                if line_max_payable > 0:
                    # Calculate proportional amount
                    proportion = line_max_payable / line.available_amount
                    line_payout = total_to_pay * proportion
                    
                    # Process payout
                    agreement_line.action_pay_investor_interest(line_payout)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payouts Processed'),
                'message': _('Successfully processed %.2f in investor payouts.') % self.total_payout,
                'type': 'success',
                'sticky': False,
            }
        }


class WizardInvestorPayoutLine(models.TransientModel):
    _name = 'wizard.investor.payout.line'
    _description = 'Investor Payout Line'
    
    wizard_id = fields.Many2one('wizard.investor.payout', required=True, ondelete='cascade')
    investor_id = fields.Many2one('res.partner', string='Investor', required=True)
    available_amount = fields.Monetary(
        string='Available Amount',
        currency_field='currency_id',
        readonly=True,
        help='Maximum amount available for payout'
    )
    payout_amount = fields.Monetary(
        string='Payout Amount',
        currency_field='currency_id',
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    agreement_line_ids = fields.Many2many(
        'floor.plan.agreement.line',
        string='Related Funding Lines'
    )
    
    @api.onchange('payout_amount')
    def _onchange_payout_amount(self):
        """Validate payout amount"""
        if self.payout_amount > self.available_amount:
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('Payout amount exceeds available amount.')
                }
            }
