# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FloorPlanAgreement(models.Model):
    _name = 'floor.plan.agreement'
    _description = 'Floor Plan Financing Agreement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc, id desc'
    _rec_name = 'name'
    
    name = fields.Char(
        string='Agreement Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True
    )
    
    investor_id = fields.Many2one(
        'res.partner',
        string='Investor',
        required=True,
        domain="[('is_floor_plan_investor', '=', True)]",
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    
    agreement_line_ids = fields.One2many(
        'floor.plan.agreement.line',
        'agreement_id',
        string='Funding Lines',
        copy=False
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        default=20.0,
        required=True,
        help='Platform commission percentage on interest earned',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    
    default_interest_rate = fields.Float(
        string='Default Interest Rate (%)',
        default=12.0,
        required=True,
        help='Default annual interest rate for lines',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    
    date_created = fields.Date(
        string='Created Date',
        default=fields.Date.context_today,
        required=True,
        readonly=True,
        tracking=True
    )
    
    date_submitted = fields.Date(
        string='Submitted Date',
        readonly=True,
        tracking=True
    )
    
    date_approved = fields.Date(
        string='Approved Date',
        readonly=True,
        tracking=True
    )
    
    # Computed fields
    total_funded = fields.Monetary(
        string='Total Funded',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    total_outstanding = fields.Monetary(
        string='Total Outstanding',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    total_repaid = fields.Monetary(
        string='Total Repaid',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    total_interest_earned = fields.Monetary(
        string='Total Interest Earned',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    lines_count = fields.Integer(
        string='Lines Count',
        compute='_compute_totals',
        store=True
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
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('floor.plan.agreement') or 'New'
        return super().create(vals_list)
    
    @api.depends('agreement_line_ids.funded_amount',
                 'agreement_line_ids.topup_amount',
                 'agreement_line_ids.principal_remaining',
                 'agreement_line_ids.repaid_amount',
                 'agreement_line_ids.interest_earned',
                 'agreement_line_ids.state')
    def _compute_totals(self):
        """Compute agreement totals from lines"""
        for agreement in self:
            active_lines = agreement.agreement_line_ids.filtered(
                lambda l: l.state not in ['draft', 'cancelled']
            )
            agreement.total_funded = sum(active_lines.mapped('funded_amount')) + \
                                     sum(active_lines.mapped('topup_amount'))
            agreement.total_outstanding = sum(active_lines.mapped('principal_remaining'))
            agreement.total_repaid = sum(active_lines.mapped('repaid_amount'))
            agreement.total_interest_earned = sum(active_lines.mapped('interest_earned'))
            agreement.lines_count = len(active_lines)
    
    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        """Validate commission rate"""
        for agreement in self:
            if not 0 <= agreement.commission_rate <= 100:
                raise ValidationError(_('Commission rate must be between 0% and 100%.'))
    
    @api.constrains('default_interest_rate')
    def _check_interest_rate(self):
        """Validate interest rate"""
        for agreement in self:
            if agreement.default_interest_rate <= 0:
                raise ValidationError(_('Interest rate must be greater than 0%.'))
    
    def action_submit(self):
        """Submit agreement for approval"""
        for agreement in self:
            if not agreement.agreement_line_ids:
                raise UserError(_('Cannot submit agreement without funding lines.'))
            agreement.write({
                'state': 'submitted',
                'date_submitted': fields.Date.context_today(self)
            })
            agreement.message_post(body=_('Agreement submitted for approval.'))
    
    def action_approve(self):
        """Approve agreement (Finance Manager action)"""
        for agreement in self:
            agreement.write({
                'state': 'approved',
                'date_approved': fields.Date.context_today(self)
            })
            agreement.message_post(body=_('Agreement approved.'))
    
    def action_set_to_draft(self):
        """Reset agreement to draft"""
        for agreement in self:
            if agreement.state not in ['submitted']:
                raise UserError(_('Only submitted agreements can be reset to draft.'))
            agreement.write({'state': 'draft'})
            agreement.message_post(body=_('Agreement reset to draft.'))
    
    def action_cancel(self):
        """Cancel agreement"""
        for agreement in self:
            if agreement.state == 'active':
                raise UserError(_('Cannot cancel active agreement with funded lines.'))
            agreement.write({'state': 'cancelled'})
            agreement.message_post(body=_('Agreement cancelled.'))
    
    def _check_and_update_state(self):
        """Check if agreement should be set to active or closed based on lines"""
        for agreement in self:
            if agreement.state in ['draft', 'submitted', 'cancelled']:
                continue
            
            active_lines = agreement.agreement_line_ids.filtered(
                lambda l: l.state in ['funded', 'partial']
            )
            closed_lines = agreement.agreement_line_ids.filtered(
                lambda l: l.state in ['paid_off']
            )
            
            if active_lines and agreement.state != 'active':
                agreement.state = 'active'
            elif not active_lines and closed_lines and agreement.state != 'closed':
                agreement.state = 'closed'
    
    def action_view_lines(self):
        """Action to view agreement lines"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Funding Lines',
            'res_model': 'floor.plan.agreement.line',
            'view_mode': 'tree,form',
            'domain': [('agreement_id', '=', self.id)],
            'context': {'default_agreement_id': self.id}
        }
    
    def action_view_transactions(self):
        """Action to view all transactions related to this agreement"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transactions',
            'res_model': 'floor.plan.transaction',
            'view_mode': 'tree,form',
            'domain': [('agreement_id', '=', self.id)],
        }
