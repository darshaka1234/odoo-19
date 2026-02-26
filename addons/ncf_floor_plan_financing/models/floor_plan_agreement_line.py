# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero, float_compare
from datetime import timedelta


class FloorPlanAgreementLine(models.Model):
    _name = 'floor.plan.agreement.line'
    _description = 'Floor Plan Agreement Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'
    _rec_name = 'display_name'
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    agreement_id = fields.Many2one(
        'floor.plan.agreement',
        string='Agreement',
        required=True,
        ondelete='cascade',
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True
    )
    investor_id = fields.Many2one(
        'res.partner',
        string='Investor',
        related='agreement_id.investor_id',
        store=True,
        readonly=True
    )
    
    vehicle_id = fields.Many2one(
        'product.product',
        string='Vehicle',
        required=True,
        domain="[('is_floor_plan_vehicle', '=', True)]",
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True
    )
    vin = fields.Char(
        string='VIN',
        related='vehicle_id.vin',
        store=True,
        readonly=True
    )
    
    dealer_id = fields.Many2one(
        'res.partner',
        string='Dealer',
        required=True,
        domain="[('is_floor_plan_dealer', '=', True)]",
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True
    )
    
    funded_amount = fields.Monetary(
        string='Funded Amount',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        currency_field='currency_id',
        tracking=True
    )
    topup_amount = fields.Monetary(
        string='Top-up Amount',
        default=0.0,
        readonly=True,
        currency_field='currency_id',
        help='Additional funding amount requested as top-up'
    )
    repaid_amount = fields.Monetary(
        string='Repaid Amount',
        default=0.0,
        readonly=True,
        currency_field='currency_id',
        help='Total principal amount repaid'
    )
    principal_remaining = fields.Monetary(
        string='Principal Remaining',
        compute='_compute_principal_remaining',
        store=True,
        currency_field='currency_id',
        help='Outstanding principal balance'
    )
    
    interest_rate = fields.Float(
        string='Interest Rate (% p.a.)',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Annual interest rate percentage',
        tracking=True
    )
    
    interest_earned = fields.Monetary(
        string='Interest Earned',
        default=0.0,
        readonly=True,
        currency_field='currency_id',
        help='Total interest accrued (investor share + commission)'
    )
    interest_paid = fields.Monetary(
        string='Interest Paid by Dealer',
        default=0.0,
        readonly=True,
        currency_field='currency_id',
        help='Total interest paid by dealer'
    )
    interest_outstanding = fields.Monetary(
        string='Interest Outstanding',
        compute='_compute_interest_outstanding',
        store=True,
        currency_field='currency_id',
        help='Interest earned but not yet paid by dealer'
    )
    
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        related='agreement_id.commission_rate',
        store=True,
        readonly=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('funded', 'Funded'),
        ('partial', 'Partially Repaid'),
        ('paid_off', 'Paid Off'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    
    start_date = fields.Date(
        string='Funding Start Date',
        readonly=True,
        tracking=True,
        help='Date when funds were disbursed'
    )
    end_date = fields.Date(
        string='Expected End Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Expected completion date'
    )
    last_interest_calc_date = fields.Date(
        string='Last Interest Calculation Date',
        readonly=True,
        help='Last date when interest was calculated'
    )
    
    transaction_ids = fields.One2many(
        'floor.plan.transaction',
        'agreement_line_id',
        string='Transactions',
        readonly=True
    )
    transactions_count = fields.Integer(
        string='Transactions Count',
        compute='_compute_transactions_count'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    notes = fields.Text(string='Notes')
    
    @api.depends('vehicle_id.name', 'vin', 'agreement_id.name')
    def _compute_display_name(self):
        """Compute display name"""
        for line in self:
            if line.vehicle_id and line.vin:
                line.display_name = f"{line.agreement_id.name} - {line.vehicle_id.name} ({line.vin})"
            elif line.vehicle_id:
                line.display_name = f"{line.agreement_id.name} - {line.vehicle_id.name}"
            else:
                line.display_name = line.agreement_id.name or 'New'
    
    @api.depends('funded_amount', 'topup_amount', 'repaid_amount')
    def _compute_principal_remaining(self):
        """Compute remaining principal balance"""
        for line in self:
            line.principal_remaining = (line.funded_amount + line.topup_amount) - line.repaid_amount
    
    @api.depends('interest_earned', 'interest_paid')
    def _compute_interest_outstanding(self):
        """Compute outstanding interest"""
        for line in self:
            line.interest_outstanding = line.interest_earned - line.interest_paid
    
    @api.depends('transaction_ids')
    def _compute_transactions_count(self):
        """Compute number of transactions"""
        for line in self:
            line.transactions_count = len(line.transaction_ids)
    
    @api.constrains('funded_amount')
    def _check_funded_amount(self):
        """Validate funded amount"""
        for line in self:
            if line.funded_amount <= 0:
                raise ValidationError(_('Funded amount must be greater than zero.'))
    
    @api.constrains('interest_rate')
    def _check_interest_rate(self):
        """Validate interest rate"""
        for line in self:
            if line.interest_rate <= 0:
                raise ValidationError(_('Interest rate must be greater than zero.'))
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate dates"""
        for line in self:
            if line.start_date and line.end_date and line.start_date >= line.end_date:
                raise ValidationError(_('Start date must be before end date.'))
    
    @api.constrains('repaid_amount', 'funded_amount', 'topup_amount')
    def _check_repaid_amount(self):
        """Validate repaid amount doesn't exceed total funded"""
        for line in self:
            total_funded = line.funded_amount + line.topup_amount
            if float_compare(line.repaid_amount, total_funded, precision_digits=2) > 0:
                raise ValidationError(
                    _('Repaid amount (%.2f) cannot exceed total funded amount (%.2f).') % 
                    (line.repaid_amount, total_funded)
                )
    
    @api.model
    def default_get(self, fields_list):
        """Set default interest rate from agreement"""
        res = super().default_get(fields_list)
        if 'agreement_id' in res and 'interest_rate' not in res:
            agreement = self.env['floor.plan.agreement'].browse(res['agreement_id'])
            if agreement:
                res['interest_rate'] = agreement.default_interest_rate
        return res
    
    # ========================================
    # STATE TRANSITION ACTIONS
    # ========================================
    
    def action_submit(self):
        """Submit line for approval"""
        for line in self:
            if line.state != 'draft':
                raise UserError(_('Only draft lines can be submitted.'))
            if not line.vehicle_id or not line.dealer_id:
                raise UserError(_('Vehicle and Dealer must be set before submission.'))
            if line.agreement_id.state == 'draft':
                line.agreement_id.action_submit()
            line.write({'state': 'pending'})
            line.message_post(body=_('Funding line submitted for approval.'))
    
    def action_approve(self):
        """Approve line (Finance Manager action)"""
        for line in self:
            if line.state != 'pending':
                raise UserError(_('Only pending lines can be approved.'))
            if line.agreement_id.state not in ['submitted', 'approved', 'active']:
                line.agreement_id.action_approve()
            line.write({'state': 'approved'})
            line.message_post(body=_('Funding line approved.'))
    
    def action_cancel(self):
        """Cancel line"""
        for line in self:
            if line.state in ['funded', 'partial']:
                raise UserError(_('Cannot cancel funded or partially repaid lines.'))
            line.write({'state': 'cancelled'})
            line.message_post(body=_('Funding line cancelled.'))
    
    # ========================================
    # JOURNAL ENTRY #1: INVESTOR INVESTS
    # ========================================
    
    def action_fund(self):
        """
        Journal Entry #1: Investor Invests
        DR - Client Funds Bank Asset
        CR - Investor Payable Liability
        """
        for line in self:
            if line.state != 'approved':
                raise UserError(_('Only approved lines can be funded.'))
            
            # Get accounts
            client_funds_bank = self.env.ref('ncf_floor_plan_financing.account_client_funds_bank_asset')
            investor_payable = self.env.ref('ncf_floor_plan_financing.account_investor_payable')
            journal = self.env.ref('ncf_floor_plan_financing.journal_floor_plan_financing')
            
            amount = line.funded_amount
            
            # Create journal entry
            move_vals = {
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'ref': f'Investor Investment - {line.display_name}',
                'line_ids': [
                    (0, 0, {
                        'account_id': client_funds_bank.id,
                        'debit': amount,
                        'credit': 0.0,
                        'name': f'Investment from {line.investor_id.name}',
                        'partner_id': line.investor_id.id,
                    }),
                    (0, 0, {
                        'account_id': investor_payable.id,
                        'debit': 0.0,
                        'credit': amount,
                        'name': f'Investment by {line.investor_id.name}',
                        'partner_id': line.investor_id.id,
                    }),
                ]
            }
            
            # Validate balance
            self._validate_accounting_balance(move_vals['line_ids'])
            
            # Create and post move
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            
            # Create transaction record
            transaction = self.env['floor.plan.transaction'].create({
                'transaction_type': 'investor_invest',
                'agreement_line_id': line.id,
                'amount': amount,
                'move_id': move.id,
                'state': 'posted',
                'notes': f'Initial funding for {line.vehicle_id.name}'
            })
            
            # Update line state
            line.write({
                'state': 'funded',
                'start_date': fields.Date.context_today(self),
                'last_interest_calc_date': fields.Date.context_today(self)
            })
            
            # Update agreement state
            line.agreement_id._check_and_update_state()
            
            line.message_post(body=_('Funding completed. Amount: %.2f') % amount)
    
    # ========================================
    # JOURNAL ENTRY #2: TRANSFER TO DEALER
    # ========================================
    
    def action_transfer_to_dealer(self):
        """
        Journal Entry #2: Platform Transfers Money to Dealer
        DR - Dealer Loan Receivable Asset
        CR - Client Funds Bank Asset
        """
        for line in self:
            if line.state not in ['funded', 'partial']:
                raise UserError(_('Only funded lines can be transferred to dealer.'))
            
            # Check if already transferred
            existing_transfer = line.transaction_ids.filtered(
                lambda t: t.transaction_type == 'transfer_to_dealer' and t.state == 'posted'
            )
            if existing_transfer:
                raise UserError(_('Funds have already been transferred to dealer.'))
            
            # Get accounts
            dealer_loan_receivable = self.env.ref('ncf_floor_plan_financing.account_dealer_loan_receivable')
            client_funds_bank = self.env.ref('ncf_floor_plan_financing.account_client_funds_bank_asset')
            journal = self.env.ref('ncf_floor_plan_financing.journal_floor_plan_financing')
            
            amount = line.funded_amount + line.topup_amount
            
            # Create journal entry
            move_vals = {
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'ref': f'Transfer to Dealer - {line.display_name}',
                'line_ids': [
                    (0, 0, {
                        'account_id': dealer_loan_receivable.id,
                        'debit': amount,
                        'credit': 0.0,
                        'name': f'Loan to {line.dealer_id.name}',
                        'partner_id': line.dealer_id.id,
                    }),
                    (0, 0, {
                        'account_id': client_funds_bank.id,
                        'debit': 0.0,
                        'credit': amount,
                        'name': f'Transfer to {line.dealer_id.name}',
                        'partner_id': line.dealer_id.id,
                    }),
                ]
            }
            
            # Validate balance
            self._validate_accounting_balance(move_vals['line_ids'])
            
            # Create and post move
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            
            # Create transaction record
            transaction = self.env['floor.plan.transaction'].create({
                'transaction_type': 'transfer_to_dealer',
                'agreement_line_id': line.id,
                'amount': amount,
                'move_id': move.id,
                'state': 'posted',
                'notes': f'Transfer funds to dealer for {line.vehicle_id.name}'
            })
            
            line.message_post(body=_('Funds transferred to dealer. Amount: %.2f') % amount)
    
    # ========================================
    # JOURNAL ENTRY #3: CALCULATE INTEREST
    # ========================================
    
    def _calculate_interest(self):
        """
        Journal Entry #3: Calculate Interest
        DR - Dealer Interest Receivable Asset
        CR - Investor Interest Payable Liability (investor share)
        CR - Commission Income (platform commission)
        """
        for line in self:
            if line.state not in ['funded', 'partial']:
                continue
            
            # Calculate days since last calculation
            last_calc = line.last_interest_calc_date or line.start_date
            if not last_calc:
                continue
            
            today = fields.Date.context_today(self)
            if last_calc >= today:
                continue  # Already calculated for today
            
            days = (today - last_calc).days
            if days <= 0:
                continue
            
            # Calculate interest: Principal × Rate × (Days / 365)
            principal = line.principal_remaining
            if float_is_zero(principal, precision_digits=2):
                continue
            
            daily_rate = line.interest_rate / 36500  # Convert annual % to daily decimal
            interest_amount = principal * daily_rate * days
            
            if float_is_zero(interest_amount, precision_digits=2):
                continue
            
            # Split interest: investor share vs commission
            commission_amount = interest_amount * (line.commission_rate / 100)
            investor_interest = interest_amount - commission_amount
            
            # Get accounts
            dealer_interest_receivable = self.env.ref('ncf_floor_plan_financing.account_dealer_interest_receivable')
            investor_interest_payable = self.env.ref('ncf_floor_plan_financing.account_investor_interest_payable')
            commission_income = self.env.ref('ncf_floor_plan_financing.account_commission_income')
            journal = self.env.ref('ncf_floor_plan_financing.journal_floor_plan_financing')
            
            # Create journal entry
            move_vals = {
                'journal_id': journal.id,
                'date': today,
                'ref': f'Interest Accrual - {line.display_name} ({days} days)',
                'line_ids': [
                    (0, 0, {
                        'account_id': dealer_interest_receivable.id,
                        'debit': interest_amount,
                        'credit': 0.0,
                        'name': f'Interest from {line.dealer_id.name} ({days} days)',
                        'partner_id': line.dealer_id.id,
                    }),
                    (0, 0, {
                        'account_id': investor_interest_payable.id,
                        'debit': 0.0,
                        'credit': investor_interest,
                        'name': f'Interest for {line.investor_id.name}',
                        'partner_id': line.investor_id.id,
                    }),
                    (0, 0, {
                        'account_id': commission_income.id,
                        'debit': 0.0,
                        'credit': commission_amount,
                        'name': f'Commission on interest ({line.commission_rate}%)',
                        'partner_id': line.dealer_id.id,
                    }),
                ]
            }
            
            # Validate balance
            self._validate_accounting_balance(move_vals['line_ids'])
            
            # Create and post move
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            
            # Create transaction record
            transaction = self.env['floor.plan.transaction'].create({
                'transaction_type': 'interest_calculated',
                'agreement_line_id': line.id,
                'amount': interest_amount,
                'move_id': move.id,
                'state': 'posted',
                'notes': f'Interest for {days} days. Investor: {investor_interest:.2f}, Commission: {commission_amount:.2f}'
            })
            
            # Update line
            line.write({
                'interest_earned': line.interest_earned + interest_amount,
                'last_interest_calc_date': today
            })
    
    @api.model
    def _cron_calculate_all_interest(self):
        """Cron job to calculate interest for all funded lines"""
        lines = self.search([
            ('state', 'in', ['funded', 'partial']),
            '|',
            ('last_interest_calc_date', '<', fields.Date.context_today(self)),
            ('last_interest_calc_date', '=', False)
        ])
        
        for line in lines:
            try:
                line._calculate_interest()
            except Exception as e:
                # Log error but continue processing other lines
                line.message_post(body=_('Interest calculation failed: %s') % str(e))
        
        return True
    
    # ========================================
    # JOURNAL ENTRY #4: DEALER PAYS INTEREST
    # ========================================
    
    def action_receive_dealer_interest(self, payment_amount):
        """
        Journal Entry #4: Dealer Pays Monthly Interest
        DR - Client Funds Bank Asset
        CR - Dealer Interest Receivable Asset
        """
        self.ensure_one()
        
        if self.state not in ['funded', 'partial']:
            raise UserError(_('Can only receive interest payments for funded lines.'))
        
        if payment_amount <= 0:
            raise UserError(_('Payment amount must be greater than zero.'))
        
        outstanding_interest = self.interest_outstanding
        if float_compare(payment_amount, outstanding_interest, precision_digits=2) > 0:
            raise UserError(
                _('Payment amount (%.2f) exceeds outstanding interest (%.2f).') % 
                (payment_amount, outstanding_interest)
            )
        
        # Get accounts
        client_funds_bank = self.env.ref('ncf_floor_plan_financing.account_client_funds_bank_asset')
        dealer_interest_receivable = self.env.ref('ncf_floor_plan_financing.account_dealer_interest_receivable')
        journal = self.env.ref('ncf_floor_plan_financing.journal_floor_plan_financing')
        
        # Create journal entry
        move_vals = {
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': f'Dealer Interest Payment - {self.display_name}',
            'line_ids': [
                (0, 0, {
                    'account_id': client_funds_bank.id,
                    'debit': payment_amount,
                    'credit': 0.0,
                    'name': f'Interest payment from {self.dealer_id.name}',
                    'partner_id': self.dealer_id.id,
                }),
                (0, 0, {
                    'account_id': dealer_interest_receivable.id,
                    'debit': 0.0,
                    'credit': payment_amount,
                    'name': f'Interest payment from {self.dealer_id.name}',
                    'partner_id': self.dealer_id.id,
                }),
            ]
        }
        
        # Validate balance
        self._validate_accounting_balance(move_vals['line_ids'])
        
        # Create and post move
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        
        # Create transaction record
        transaction = self.env['floor.plan.transaction'].create({
            'transaction_type': 'dealer_interest_payment',
            'agreement_line_id': self.id,
            'amount': payment_amount,
            'move_id': move.id,
            'state': 'posted',
            'notes': f'Interest payment from dealer'
        })
        
        # Update line
        self.write({
            'interest_paid': self.interest_paid + payment_amount
        })
        
        self.message_post(body=_('Interest payment received. Amount: %.2f') % payment_amount)
        
        return transaction
    
    # ========================================
    # JOURNAL ENTRY #5: PAY INVESTOR
    # ========================================
    
    def action_pay_investor_interest(self, payment_amount):
        """
        Journal Entry #5: Platform Pays Interest to Investor
        DR - Investor Interest Payable Liability
        CR - Client Funds Bank Asset
        """
        self.ensure_one()
        
        if payment_amount <= 0:
            raise UserError(_('Payment amount must be greater than zero.'))
        
        # Calculate investor's share of interest paid by dealer
        investor_share_rate = 1 - (self.commission_rate / 100)
        max_payable = self.interest_paid * investor_share_rate
        
        # Check against investor interest payable (from accounting)
        if float_compare(payment_amount, max_payable, precision_digits=2) > 0:
            raise UserError(
                _('Payment amount (%.2f) exceeds maximum payable to investor (%.2f).') % 
                (payment_amount, max_payable)
            )
        
        # Get accounts
        investor_interest_payable = self.env.ref('ncf_floor_plan_financing.account_investor_interest_payable')
        client_funds_bank = self.env.ref('ncf_floor_plan_financing.account_client_funds_bank_asset')
        journal = self.env.ref('ncf_floor_plan_financing.journal_floor_plan_financing')
        
        # Create journal entry
        move_vals = {
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': f'Investor Interest Payout - {self.display_name}',
            'line_ids': [
                (0, 0, {
                    'account_id': investor_interest_payable.id,
                    'debit': payment_amount,
                    'credit': 0.0,
                    'name': f'Interest payout to {self.investor_id.name}',
                    'partner_id': self.investor_id.id,
                }),
                (0, 0, {
                    'account_id': client_funds_bank.id,
                    'debit': 0.0,
                    'credit': payment_amount,
                    'name': f'Interest payout to {self.investor_id.name}',
                    'partner_id': self.investor_id.id,
                }),
            ]
        }
        
        # Validate balance
        self._validate_accounting_balance(move_vals['line_ids'])
        
        # Create and post move
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        
        # Create transaction record
        transaction = self.env['floor.plan.transaction'].create({
            'transaction_type': 'investor_interest_payout',
            'agreement_line_id': self.id,
            'amount': payment_amount,
            'move_id': move.id,
            'state': 'posted',
            'notes': f'Interest payout to investor'
        })
        
        self.message_post(body=_('Interest paid to investor. Amount: %.2f') % payment_amount)
        
        return transaction
    
    # ========================================
    # JOURNAL ENTRY #6: PRINCIPAL REPAYMENT
    # ========================================
    
    def action_receive_principal_repayment(self, repayment_amount):
        """
        Journal Entry #6: Partial/Full Repayment of Principal
        Part 1:
        DR - Client Funds Bank Asset
        CR - Dealer Loan Receivable Asset
        Part 2:
        DR - Investor Payable Liability
        CR - Client Funds Bank Asset
        """
        self.ensure_one()
        
        if self.state not in ['funded', 'partial']:
            raise UserError(_('Can only receive principal repayments for funded lines.'))
        
        if repayment_amount <= 0:
            raise UserError(_('Repayment amount must be greater than zero.'))
        
        if float_compare(repayment_amount, self.principal_remaining, precision_digits=2) > 0:
            raise UserError(
                _('Repayment amount (%.2f) exceeds remaining principal (%.2f).') % 
                (repayment_amount, self.principal_remaining)
            )
        
        # Get accounts
        client_funds_bank = self.env.ref('ncf_floor_plan_financing.account_client_funds_bank_asset')
        dealer_loan_receivable = self.env.ref('ncf_floor_plan_financing.account_dealer_loan_receivable')
        investor_payable = self.env.ref('ncf_floor_plan_financing.account_investor_payable')
        journal = self.env.ref('ncf_floor_plan_financing.journal_floor_plan_financing')
        
        # Create journal entry with 4 lines (2 parts)
        move_vals = {
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': f'Principal Repayment - {self.display_name}',
            'line_ids': [
                # Part 1: Receive from dealer
                (0, 0, {
                    'account_id': client_funds_bank.id,
                    'debit': repayment_amount,
                    'credit': 0.0,
                    'name': f'Principal repayment from {self.dealer_id.name}',
                    'partner_id': self.dealer_id.id,
                }),
                (0, 0, {
                    'account_id': dealer_loan_receivable.id,
                    'debit': 0.0,
                    'credit': repayment_amount,
                    'name': f'Principal repayment from {self.dealer_id.name}',
                    'partner_id': self.dealer_id.id,
                }),
                # Part 2: Pay to investor
                (0, 0, {
                    'account_id': investor_payable.id,
                    'debit': repayment_amount,
                    'credit': 0.0,
                    'name': f'Principal repayment to {self.investor_id.name}',
                    'partner_id': self.investor_id.id,
                }),
                (0, 0, {
                    'account_id': client_funds_bank.id,
                    'debit': 0.0,
                    'credit': repayment_amount,
                    'name': f'Principal repayment to {self.investor_id.name}',
                    'partner_id': self.investor_id.id,
                }),
            ]
        }
        
        # Validate balance
        self._validate_accounting_balance(move_vals['line_ids'])
        
        # Create and post move
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        
        # Create transaction record
        transaction = self.env['floor.plan.transaction'].create({
            'transaction_type': 'principal_repayment',
            'agreement_line_id': self.id,
            'amount': repayment_amount,
            'move_id': move.id,
            'state': 'posted',
            'notes': f'Principal repayment'
        })
        
        # Update line
        new_repaid = self.repaid_amount + repayment_amount
        self.write({'repaid_amount': new_repaid})
        
        # Update state
        if float_is_zero(self.principal_remaining, precision_digits=2):
            self.write({'state': 'paid_off'})
            self.message_post(body=_('Principal fully repaid!'))
        else:
            self.write({'state': 'partial'})
            self.message_post(body=_('Partial principal repayment. Amount: %.2f, Remaining: %.2f') % 
                            (repayment_amount, self.principal_remaining))
        
        # Update agreement state
        self.agreement_id._check_and_update_state()
        
        return transaction
    
    # ========================================
    # JOURNAL ENTRY #7: COMMISSION TRANSFER
    # ========================================
    
    @api.model
    def action_transfer_commission(self, amount):
        """
        Journal Entry #7: Transfer Commission to Platform
        DR - Platform Bank Asset
        CR - Client Funds Bank Asset
        
        Note: This is a company-wide action, not per line
        """
        if amount <= 0:
            raise UserError(_('Transfer amount must be greater than zero.'))
        
        # Get accounts
        platform_bank = self.env.ref('ncf_floor_plan_financing.account_platform_bank_asset')
        client_funds_bank = self.env.ref('ncf_floor_plan_financing.account_client_funds_bank_asset')
        journal = self.env.ref('ncf_floor_plan_financing.journal_floor_plan_financing')
        
        # Create journal entry
        move_vals = {
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': f'Commission Transfer to Platform',
            'line_ids': [
                (0, 0, {
                    'account_id': platform_bank.id,
                    'debit': amount,
                    'credit': 0.0,
                    'name': 'Commission transfer to platform bank',
                }),
                (0, 0, {
                    'account_id': client_funds_bank.id,
                    'debit': 0.0,
                    'credit': amount,
                    'name': 'Commission transfer from client funds',
                }),
            ]
        }
        
        # Validate balance
        self._validate_accounting_balance(move_vals['line_ids'])
        
        # Create and post move
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        
        return move
    
    # ========================================
    # TOP-UP REQUEST
    # ========================================
    
    def action_request_topup(self, topup_amount, new_interest_rate=None):
        """
        Create a new agreement line for top-up funding
        Linked to same agreement and investor
        """
        self.ensure_one()
        
        if self.state not in ['funded', 'partial']:
            raise UserError(_('Can only request top-up for active funding lines.'))
        
        if topup_amount <= 0:
            raise UserError(_('Top-up amount must be greater than zero.'))
        
        # Create new line
        new_line = self.create({
            'agreement_id': self.agreement_id.id,
            'vehicle_id': self.vehicle_id.id,
            'dealer_id': self.dealer_id.id,
            'funded_amount': topup_amount,
            'interest_rate': new_interest_rate or self.interest_rate,
            'state': 'draft',
            'notes': f'Top-up request for {self.display_name}'
        })
        
        # Link as top-up to original line
        self.write({'topup_amount': self.topup_amount + topup_amount})
        
        self.message_post(body=_('Top-up request created. New line: %s, Amount: %.2f') % 
                         (new_line.display_name, topup_amount))
        
        return new_line
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    @staticmethod
    def _validate_accounting_balance(line_vals):
        """Validate that journal entry balances (debits = credits)"""
        total_debit = sum(l[2]['debit'] for l in line_vals if l[0] == 0)
        total_credit = sum(l[2]['credit'] for l in line_vals if l[0] == 0)
        
        if not float_is_zero(total_debit - total_credit, precision_digits=2):
            raise ValidationError(
                _('Journal entry does not balance:\nTotal Debit: %.2f\nTotal Credit: %.2f\nDifference: %.2f') % 
                (total_debit, total_credit, total_debit - total_credit)
            )
        return True
    
    def action_view_transactions(self):
        """Action to view all transactions for this line"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transactions',
            'res_model': 'floor.plan.transaction',
            'view_mode': 'tree,form',
            'domain': [('agreement_line_id', '=', self.id)],
            'context': {'default_agreement_line_id': self.id}
        }
