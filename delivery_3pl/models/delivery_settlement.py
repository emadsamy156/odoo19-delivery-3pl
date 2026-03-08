from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DeliverySettlement(models.Model):
    _name = 'delivery.settlement'
    _description = 'Delivery Settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    company_id = fields.Many2one('delivery.company', string='Company', required=True, tracking=True, ondelete='cascade')
    branch_id = fields.Many2one('delivery.company.branch', string='Branch', tracking=True,
                                 domain="[('company_id', '=', company_id)]")
    contract_id = fields.Many2one('delivery.contract', string='Contract', tracking=True,
                                  domain="[('company_id', '=', company_id), ('status', '=', 'active'), '|', ('branch_id', '=', branch_id), ('branch_id', '=', False)]")
    settlement_number = fields.Char(string='Settlement Number', required=True, tracking=True)
    period_start = fields.Date(string='Period Start', required=True)
    period_end = fields.Date(string='Period End', required=True)
    cycle = fields.Selection([
        ('weekly', 'Weekly'),
        ('semi_monthly', 'Semi-Monthly'),
        ('monthly', 'Monthly'),
    ], string='Settlement Cycle', default='monthly', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
    ], string='Status', default='draft', required=True, tracking=True)
    total_orders = fields.Integer(string='Total Orders', default=0)
    gross_amount = fields.Float(string='Gross Amount', digits=(12, 2), default=0.0, tracking=True)

    order_base_total = fields.Float(string='Order Base Total', digits=(12, 2), default=0.0)
    capacity_incentive_total = fields.Float(string='Capacity Incentive Total', digits=(12, 2), default=0.0)
    experience_incentive_total = fields.Float(string='Experience Incentive Total', digits=(12, 2), default=0.0)
    subsidy_total = fields.Float(string='Subsidy Total', digits=(12, 2), default=0.0)
    dxg_total = fields.Float(string='DXG Total', digits=(12, 2), default=0.0)
    tips_total = fields.Float(string='Tips Total (excl. VAT)', digits=(12, 2), default=0.0)

    penalties = fields.Float(string='Penalties', digits=(12, 2), default=0.0)
    bonuses = fields.Float(string='Bonuses', digits=(12, 2), default=0.0)
    adjustments = fields.Float(string='Adjustments', digits=(12, 2), default=0.0)
    vat_amount = fields.Float(string='VAT Amount (مبلغ الضريبة)', digits=(12, 2), default=0.0)
    net_amount = fields.Float(string='Net Amount', digits=(12, 2), default=0.0,
                              compute='_compute_net_amount', store=True, tracking=True)
    approved_by = fields.Many2one('res.users', string='Approved By')
    approved_at = fields.Datetime(string='Approved At')
    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    valid_rider_count = fields.Integer(string='Valid Riders (صالح)', default=0)
    invalid_rider_count = fields.Integer(string='Invalid Riders (غير صالح)', default=0)

    item_ids = fields.One2many('delivery.settlement.item', 'settlement_id', string='Settlement Items')
    item_count = fields.Integer(compute='_compute_item_count')

    @api.depends('gross_amount', 'penalties', 'bonuses', 'adjustments', 'vat_amount')
    def _compute_net_amount(self):
        for rec in self:
            rec.net_amount = rec.gross_amount - rec.penalties + rec.bonuses + rec.adjustments - rec.vat_amount

    def _compute_item_count(self):
        for rec in self:
            rec.item_count = len(rec.item_ids)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.branch_id = False
            active_contract = self.env['delivery.contract'].search([
                ('company_id', '=', self.company_id.id),
                ('status', '=', 'active'),
            ], limit=1)
            if active_contract:
                self.contract_id = active_contract.id
                self.cycle = active_contract.settlement_cycle

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.branch_id:
            active_contract = self.env['delivery.contract'].search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', self.branch_id.id),
                ('status', '=', 'active'),
            ], limit=1)
            if active_contract:
                self.contract_id = active_contract.id
                self.cycle = active_contract.settlement_cycle

    def action_submit_for_approval(self):
        self.ensure_one()
        if self.status != 'draft':
            raise ValidationError('Only draft settlements can be submitted for approval.')
        self.write({'status': 'pending_approval'})

    def action_approve(self):
        self.ensure_one()
        if self.status != 'pending_approval':
            raise ValidationError('Only pending settlements can be approved.')
        self.write({
            'status': 'approved',
            'approved_by': self.env.user.id,
            'approved_at': fields.Datetime.now(),
        })

    def action_lock(self):
        self.ensure_one()
        if self.status != 'approved':
            raise ValidationError('Only approved settlements can be locked.')
        self.write({'status': 'locked'})

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.status == 'locked':
            raise ValidationError('Locked settlements cannot be reset.')
        self.write({
            'status': 'draft',
            'approved_by': False,
            'approved_at': False,
        })


class DeliverySettlementItem(models.Model):
    _name = 'delivery.settlement.item'
    _description = 'Settlement Line Item (Per Rider)'
    _order = 'rider_id'

    settlement_id = fields.Many2one('delivery.settlement', string='Settlement', required=True, ondelete='cascade')
    rider_id = fields.Many2one('delivery.rider', string='Rider', required=True)
    is_valid_da = fields.Boolean(string='Valid DA (صالح)', default=False)
    validity_reason = fields.Char(string='Validity Reason')

    orders = fields.Integer(string='Orders', default=0)
    gross_amount = fields.Float(string='Gross Amount', digits=(12, 2), default=0.0)

    order_base_amount = fields.Float(string='Order Base Pricing', digits=(12, 2), default=0.0)
    capacity_incentive = fields.Float(string='Capacity Incentive (حوافز سعة الطلب)', digits=(12, 2), default=0.0)
    experience_incentive = fields.Float(string='Experience Incentive (حوافز التسليم)', digits=(12, 2), default=0.0)
    subsidy = fields.Float(string='Subsidy (الإعانة)', digits=(12, 2), default=0.0)
    dxg = fields.Float(string='DXG', digits=(12, 2), default=0.0)
    other_activities = fields.Float(string='Other Activities (الأنشطة والمكافآت)', digits=(12, 2), default=0.0)
    food_damage = fields.Float(string='Food Damage (تعويض تلف الطعام)', digits=(12, 2), default=0.0,
                                help='Negative value')
    tips_excl_vat = fields.Float(string='Tips excl. VAT (البقشيش)', digits=(12, 2), default=0.0)

    penalties = fields.Float(string='Penalties', digits=(12, 2), default=0.0)
    bonuses = fields.Float(string='Bonuses', digits=(12, 2), default=0.0)
    deposits = fields.Float(string='Deposits', digits=(12, 2), default=0.0)
    adjustments = fields.Float(string='Adjustments', digits=(12, 2), default=0.0)
    net_amount = fields.Float(string='Net Amount', digits=(12, 2), default=0.0,
                              compute='_compute_net_amount', store=True)
    notes = fields.Text(string='Notes')

    @api.depends('gross_amount', 'penalties', 'bonuses', 'deposits', 'adjustments')
    def _compute_net_amount(self):
        for rec in self:
            rec.net_amount = rec.gross_amount - rec.penalties + rec.bonuses - rec.deposits + rec.adjustments
