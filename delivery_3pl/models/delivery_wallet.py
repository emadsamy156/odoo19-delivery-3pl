from odoo import models, fields


class DeliveryWalletTransaction(models.Model):
    _name = 'delivery.wallet.transaction'
    _description = 'Wallet Transaction'
    _order = 'create_date desc'

    rider_id = fields.Many2one('delivery.rider', string='Rider', required=True, ondelete='cascade')
    type = fields.Selection([
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('penalty', 'Penalty'),
        ('deposit', 'Deposit'),
        ('adjustment', 'Adjustment'),
    ], string='Type', required=True)
    amount = fields.Float(string='Amount (SAR)', digits=(12, 2), required=True)
    balance_before = fields.Float(string='Balance Before', digits=(12, 2), required=True)
    balance_after = fields.Float(string='Balance After', digits=(12, 2), required=True)
    reference = fields.Char(string='Reference')
    settlement_id = fields.Many2one('delivery.settlement', string='Settlement')
    description = fields.Text(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
