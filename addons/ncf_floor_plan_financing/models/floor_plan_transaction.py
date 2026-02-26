# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FloorPlanTransaction(models.Model):
    _name = 'floor.plan.transaction'
    _description = 'Floor Plan Transaction Log'
    _order = 'transaction_date desc, id desc'
    _rec_name = 'name'
    
    name = fields.Char(
        string='Transaction Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    transaction_date = fields.Date(
        string='Transaction Date',
        required=True,
        default=fields.Date.context_today,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    transaction_type = fields.Selection([
        ('investor_invest', 'Investor Investment'),
        ('transfer_to_dealer', 'Transfer to Dealer'),
        ('interest_calculated', 'Interest Calculated'),
        ('dealer_interest_payment', 'Dealer Interest Payment'),
        ('investor_interest_payout', 'Investor Interest Payout'),
        ('principal_repayment', 'Principal Repayment'),
        ('commission_transfer', 'Commission Transfer'),
    ], string='Transaction Type', required=True, readonly=True)
    
    agreement_line_id = fields.Many2one(
        'floor.plan.agreement.line',
        string='Agreement Line',
        required=True,
        ondelete='cascade',
        readonly=True
    )
    agreement_id = fields.Many2one(
        'floor.plan.agreement',
        string='Agreement',
        related='agreement_line_id.agreement_id',
        store=True,
        readonly=True
    )
    investor_id = fields.Many2one(
        'res.partner',
        string='Investor',
        related='agreement_id.investor_id',
        store=True,
        readonly=True
    )
    dealer_id = fields.Many2one(
        'res.partner',
        string='Dealer',
        related='agreement_line_id.dealer_id',
        store=True,
        readonly=True
    )
    
    amount = fields.Monetary(
        string='Amount',
        required=True,
        readonly=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        ondelete='restrict',
        help='Related accounting journal entry'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)
    
    notes = fields.Text(
        string='Notes',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('floor.plan.transaction') or 'New'
        return super().create(vals_list)
    
    def action_view_journal_entry(self):
        """Action to view related journal entry"""
        self.ensure_one()
        if not self.move_id:
            return {}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
