# NCF Floor Plan Financing Module

## Overview
Comprehensive floor plan financing solution for vehicle dealers with crowdfunding support.

## Features
- Multi-investor vehicle funding
- VIN-based vehicle tracking
- Automated interest calculation (daily cron)
- Approval workflow (Draft → Submitted → Approved → Funded)
- Segregated bank accounts (Platform vs Client Funds)
- Complete accounting integration
- Dealer repayment management
- Top-up funding support
- Commission tracking and distribution

## Installation
1. Copy module to Odoo addons directory
2. Update app list
3. Install "NCF Floor Plan Financing"
4. Configure chart of accounts (auto-created on install)

## Usage
1. Create investor partners (mark as "Floor Plan Investor")
2. Create dealer partners (mark as "Floor Plan Dealer")
3. Create vehicle products with VIN numbers
4. Create funding agreements
5. Submit and approve agreements
6. Fund vehicles and transfer to dealers
7. Interest calculated daily automatically
8. Process dealer payments
9. Distribute interest to investors
10. Track repayments to completion

## Technical Details
- **Odoo Version**: 19.0
- **Dependencies**: base, account, product
- **License**: LGPL-3
