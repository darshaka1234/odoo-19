# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Floor Plan Investor Fields
    is_floor_plan_investor = fields.Boolean(
        string='Floor Plan Investor',
        help='Check if this partner is a floor plan investor'
    )
    investor_agreement_ids = fields.One2many(
        'floor.plan.agreement',
        'investor_id',
        string='Investor Agreements'
    )
    investor_total_invested = fields.Monetary(
        string='Total Invested',
        compute='_compute_investor_totals',
        currency_field='currency_id',
        help='Total amount invested across all agreements'
    )
    investor_total_outstanding = fields.Monetary(
        string='Total Outstanding',
        compute='_compute_investor_totals',
        currency_field='currency_id',
        help='Total outstanding principal amount'
    )
    investor_total_interest_earned = fields.Monetary(
        string='Total Interest Earned',
        compute='_compute_investor_totals',
        currency_field='currency_id',
        help='Total interest earned across all agreements'
    )
    investor_agreements_count = fields.Integer(
        string='Agreements Count',
        compute='_compute_investor_totals'
    )
    
    # Floor Plan Dealer Fields
    is_floor_plan_dealer = fields.Boolean(
        string='Floor Plan Dealer',
        help='Check if this partner is a floor plan dealer'
    )
    dealer_agreement_line_ids = fields.One2many(
        'floor.plan.agreement.line',
        'dealer_id',
        string='Dealer Funding Lines'
    )
    dealer_total_borrowed = fields.Monetary(
        string='Total Borrowed',
        compute='_compute_dealer_totals',
        currency_field='currency_id',
        help='Total amount borrowed'
    )
    dealer_total_owed = fields.Monetary(
        string='Total Owed',
        compute='_compute_dealer_totals',
        currency_field='currency_id',
        help='Total outstanding principal + interest'
    )
    dealer_total_repaid = fields.Monetary(
        string='Total Repaid',
        compute='_compute_dealer_totals',
        currency_field='currency_id',
        help='Total amount repaid'
    )
    dealer_funding_lines_count = fields.Integer(
        string='Funding Lines Count',
        compute='_compute_dealer_totals'
    )
    
    @api.depends('investor_agreement_ids.agreement_line_ids.funded_amount',
                 'investor_agreement_ids.agreement_line_ids.principal_remaining',
                 'investor_agreement_ids.agreement_line_ids.interest_earned')
    def _compute_investor_totals(self):
        """Compute investor totals from all related agreement lines"""
        for partner in self:
            if partner.is_floor_plan_investor:
                lines = self.env['floor.plan.agreement.line'].search([
                    ('agreement_id.investor_id', '=', partner.id)
                ])
                partner.investor_total_invested = sum(lines.mapped('funded_amount')) + sum(lines.mapped('topup_amount'))
                partner.investor_total_outstanding = sum(lines.mapped('principal_remaining'))
                partner.investor_total_interest_earned = sum(lines.mapped('interest_earned'))
                partner.investor_agreements_count = len(partner.investor_agreement_ids)
            else:
                partner.investor_total_invested = 0.0
                partner.investor_total_outstanding = 0.0
                partner.investor_total_interest_earned = 0.0
                partner.investor_agreements_count = 0
    
    @api.depends('dealer_agreement_line_ids.funded_amount',
                 'dealer_agreement_line_ids.principal_remaining',
                 'dealer_agreement_line_ids.repaid_amount',
                 'dealer_agreement_line_ids.interest_earned')
    def _compute_dealer_totals(self):
        """Compute dealer totals from all related agreement lines"""
        for partner in self:
            if partner.is_floor_plan_dealer:
                lines = partner.dealer_agreement_line_ids.filtered(lambda l: l.state not in ['draft', 'cancelled'])
                partner.dealer_total_borrowed = sum(lines.mapped('funded_amount')) + sum(lines.mapped('topup_amount'))
                partner.dealer_total_owed = sum(lines.mapped('principal_remaining')) + \
                                            sum(line.interest_earned - line.interest_paid for line in lines)
                partner.dealer_total_repaid = sum(lines.mapped('repaid_amount'))
                partner.dealer_funding_lines_count = len(lines)
            else:
                partner.dealer_total_borrowed = 0.0
                partner.dealer_total_owed = 0.0
                partner.dealer_total_repaid = 0.0
                partner.dealer_funding_lines_count = 0
    
    def action_view_investor_agreements(self):
        """Smart button action to view investor agreements"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Investor Agreements',
            'res_model': 'floor.plan.agreement',
            'view_mode': 'tree,form',
            'domain': [('investor_id', '=', self.id)],
            'context': {'default_investor_id': self.id}
        }
    
    def action_view_dealer_funding_lines(self):
        """Smart button action to view dealer funding lines"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dealer Funding Lines',
            'res_model': 'floor.plan.agreement.line',
            'view_mode': 'tree,form',
            'domain': [('dealer_id', '=', self.id)],
            'context': {'default_dealer_id': self.id}
        }
