from odoo import models, fields, api


class DeliveryRiderType(models.Model):
    _name = 'delivery.rider.type'
    _description = 'Rider Type'
    _order = 'name'

    name = fields.Char(string='Type Name (EN)', required=True)
    name_ar = fields.Char(string='Type Name (AR)')
    type = fields.Selection([
        ('internal', 'Internal Rider'),
        ('subcontract', 'Subcontract Rider'),
    ], string='Type', default='internal', required=True)
    has_deposit = fields.Boolean(string='Requires Deposit', default=False)
    has_penalties = fields.Boolean(string='Has Penalties', default=True)
    has_wallet = fields.Boolean(string='Has Wallet', default=True)
    description = fields.Text(string='Description')


class DeliveryRider(models.Model):
    _name = 'delivery.rider'
    _description = 'Delivery Rider (Independent Contractor)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    name = fields.Char(string='Full Name (EN)', tracking=True)
    name_ar = fields.Char(string='Full Name (AR)')
    phone = fields.Char(string='Phone Number', required=True, tracking=True)
    national_id = fields.Char(string='National ID / Iqama', tracking=True)
    platform_account_id = fields.Char(string='Platform Account ID (معرف الحساب)', tracking=True,
                                       help='Account ID on the delivery platform (e.g. Keeta account ID)')
    rider_type_id = fields.Many2one('delivery.rider.type', string='Rider Type', tracking=True)
    rider_type = fields.Selection(related='rider_type_id.type', string='Type Category', store=True)
    primary_company_id = fields.Many2one('delivery.company', string='Primary Company', tracking=True)
    branch_id = fields.Many2one('delivery.company.branch', string='Branch', tracking=True,
                                 domain="[('company_id', '=', primary_company_id)]")
    city_id = fields.Many2one('delivery.city', string='City', tracking=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ], string='Status', default='active', required=True, tracking=True)

    vehicle_type = fields.Selection([
        ('car', 'Car (Private Car)'),
        ('motorcycle', 'Motorcycle / Bike'),
    ], string='Vehicle Type', tracking=True)
    license_plate = fields.Char(string='License Plate (رقم اللوحة)')

    join_date = fields.Date(string='Join Date')
    work_start_date = fields.Date(string='Work Start Date (تاريخ بداية العمل)', tracking=True)
    work_end_date = fields.Date(string='Work End Date (تاريخ نهاية العمل)', tracking=True)
    parent_rider_id = fields.Many2one('delivery.rider', string='Parent Rider (for subcontract)',
                                       help='If this rider works as a sub-rider under another rider account')

    is_self_delivery = fields.Boolean(string='Self Delivery Rider', default=True, tracking=True,
                                       help='Rider is compliant (Ajeer Share/Sponsored/Saudi)')
    is_valid_da = fields.Boolean(string='Valid DA (صالح)', default=False, tracking=True)
    validity_reason = fields.Char(string='Validity Reason / Status', tracking=True)
    experience_score = fields.Float(string='Experience Score', digits=(8, 4), tracking=True)
    performance_level = fields.Selection([
        ('A', 'Level A'),
        ('B', 'Level B'),
        ('C', 'Level C'),
        ('D', 'Level D'),
    ], string='Performance Level', tracking=True)
    valid_days_count = fields.Integer(string='Valid Days (T-Valid)', tracking=True)
    facial_verification_pass = fields.Boolean(string='Facial Verification Passed', default=True)

    wallet_balance = fields.Float(string='Wallet Balance', digits=(12, 2), default=0.0)
    deposit_amount = fields.Float(string='Deposit Amount', digits=(12, 2), default=0.0)
    notes = fields.Text(string='Notes')

    wallet_transaction_ids = fields.One2many('delivery.wallet.transaction', 'rider_id', string='Wallet Transactions')
    penalty_ids = fields.One2many('delivery.rider.penalty', 'rider_id', string='Penalties')
    settlement_item_ids = fields.One2many('delivery.settlement.item', 'rider_id', string='Settlement Items')
    daily_performance_ids = fields.One2many('delivery.daily.performance', 'rider_id', string='Daily Performance')
    monthly_performance_ids = fields.One2many('delivery.monthly.performance', 'rider_id', string='Monthly Performance')
    deduction_ids = fields.One2many('delivery.rider.deduction', 'rider_id', string='Deductions')

    penalty_count = fields.Integer(compute='_compute_penalty_count')
    transaction_count = fields.Integer(compute='_compute_transaction_count')
    daily_perf_count = fields.Integer(compute='_compute_daily_perf_count')
    monthly_perf_count = fields.Integer(compute='_compute_monthly_perf_count')

    def _compute_penalty_count(self):
        for rec in self:
            rec.penalty_count = len(rec.penalty_ids)

    def _compute_transaction_count(self):
        for rec in self:
            rec.transaction_count = len(rec.wallet_transaction_ids)

    def _compute_daily_perf_count(self):
        for rec in self:
            rec.daily_perf_count = len(rec.daily_performance_ids)

    def _compute_monthly_perf_count(self):
        for rec in self:
            rec.monthly_perf_count = len(rec.monthly_performance_ids)

    def name_get(self):
        result = []
        for rec in self:
            label = rec.name or rec.name_ar or rec.platform_account_id or 'Rider'
            if rec.name and rec.name_ar:
                label = f"{rec.name} / {rec.name_ar}"
            elif rec.name_ar and not rec.name:
                label = rec.name_ar
            if rec.platform_account_id:
                label = f"{label} [{rec.platform_account_id}]"
            valid_tag = " ✓" if rec.is_valid_da else ""
            result.append((rec.id, f"{label}{valid_tag}"))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            riders = self.search([('platform_account_id', '=', name)] + args, limit=1)
            if not riders:
                riders = self.search([('phone', '=', name)] + args, limit=1)
            if not riders:
                riders = self.search([
                    '|', '|',
                    ('name', operator, name),
                    ('name_ar', operator, name),
                    ('platform_account_id', operator, name),
                ] + args, limit=limit)
            if len(riders) > 1 and operator == '=':
                riders = riders[:1]
            return riders.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    @api.onchange('primary_company_id')
    def _onchange_company_id(self):
        if self.primary_company_id:
            self.branch_id = False

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.branch_id:
            self.city_id = self.branch_id.city_id

    def action_view_wallet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Wallet - {self.name}',
            'res_model': 'delivery.wallet.transaction',
            'view_mode': 'tree,form',
            'domain': [('rider_id', '=', self.id)],
            'context': {'default_rider_id': self.id},
        }

    def action_view_penalties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Penalties - {self.name}',
            'res_model': 'delivery.rider.penalty',
            'view_mode': 'tree,form',
            'domain': [('rider_id', '=', self.id)],
            'context': {'default_rider_id': self.id},
        }

    def action_view_daily_performance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Daily Performance - {self.name}',
            'res_model': 'delivery.daily.performance',
            'view_mode': 'tree,form',
            'domain': [('rider_id', '=', self.id)],
            'context': {'default_rider_id': self.id},
        }

    def action_view_monthly_performance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Monthly Performance - {self.name}',
            'res_model': 'delivery.monthly.performance',
            'view_mode': 'tree,form',
            'domain': [('rider_id', '=', self.id)],
            'context': {'default_rider_id': self.id},
        }
