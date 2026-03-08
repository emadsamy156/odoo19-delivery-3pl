from odoo import models, fields


class DeliveryPenaltyType(models.Model):
    _name = 'delivery.penalty.type'
    _description = 'Penalty Type'
    _order = 'name'

    name = fields.Char(string='Penalty Name (EN)', required=True)
    name_ar = fields.Char(string='Penalty Name (AR)')
    default_amount = fields.Float(string='Default Amount (SAR)', digits=(12, 2))
    is_percentage = fields.Boolean(string='Is Percentage', default=False)
    description = fields.Text(string='Description')


class DeliveryDepositType(models.Model):
    _name = 'delivery.deposit.type'
    _description = 'Deposit Type'
    _order = 'name'

    name = fields.Char(string='Deposit Name (EN)', required=True)
    name_ar = fields.Char(string='Deposit Name (AR)')
    default_amount = fields.Float(string='Default Amount (SAR)', digits=(12, 2))
    is_refundable = fields.Boolean(string='Refundable', default=True)
    description = fields.Text(string='Description')


class DeliveryRiderPenalty(models.Model):
    _name = 'delivery.rider.penalty'
    _description = 'Rider Penalty'
    _order = 'date desc'

    rider_id = fields.Many2one('delivery.rider', string='Rider', required=True, ondelete='cascade')
    penalty_type_id = fields.Many2one('delivery.penalty.type', string='Penalty Type')
    amount = fields.Float(string='Amount (SAR)', digits=(12, 2), required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    reason = fields.Text(string='Reason')
    settlement_id = fields.Many2one('delivery.settlement', string='Settlement')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('applied', 'Applied'),
        ('waived', 'Waived'),
    ], string='Status', default='pending')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
