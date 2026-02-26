# -*- coding: utf-8 -*-
{
    'name': 'NCF Floor Plan Financing',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Finance',
    'summary': 'Crowdfunded floor plan financing for vehicle dealers with multi-investor support',
    'description': """
        Floor Plan Financing Module
        ============================
        
        Manage crowdfunded vehicle financing with:
        * Multi-investor funding for vehicles (VIN-based tracking)
        * Agreement-based funding with approval workflow
        * Automated daily interest calculation with commission split
        * Dealer loan management with partial/full repayments
        * Top-up funding on existing agreements
        * Segregated bank accounts (Platform vs Client Funds)
        * Complete accounting integration with 7 transaction types
        * Investor and dealer portfolio tracking
        
        Key Features:
        -------------
        - Multiple investors can fund portions of vehicles
        - Dealers receive funded amounts to purchase cars
        - Monthly interest payments with platform commission
        - Principal repayment tracking (partial/full)
        - Comprehensive reporting and dashboards
    """,
    'author': 'NCF',
    'website': 'https://www.ncf.com',
    'depends': [
        'base',
        'account',
        'product',
    ],
    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence_data.xml',
        'data/account_account_data.xml',
        'data/ir_cron_data.xml',
        
        # Views
        'views/res_partner_views.xml',
        'views/floor_plan_agreement_views.xml',
        'views/floor_plan_agreement_line_views.xml',
        'views/floor_plan_transaction_views.xml',
        'views/product_product_views.xml',
        'views/floor_plan_dashboard_views.xml',
        'views/menu_views.xml',
        
        # Wizards
        'wizards/wizard_dealer_payment_views.xml',
        'wizards/wizard_investor_payout_views.xml',
        'wizards/wizard_topup_request_views.xml',
        'wizards/wizard_commission_transfer_views.xml',
    ],
    'demo': [
        # 'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
