from odoo import models, fields, api


class DeliveryPricingRule(models.Model):
    _name = 'delivery.pricing.rule'
    _description = 'Delivery Pricing Rule'
    _inherit = ['mail.thread']
    _order = 'company_id, branch_id, effective_from desc'

    company_id = fields.Many2one('delivery.company', string='Company', required=True, tracking=True, ondelete='cascade')
    branch_id = fields.Many2one('delivery.company.branch', string='Branch', tracking=True,
                                 domain="[('company_id', '=', company_id)]")
    contract_id = fields.Many2one('delivery.contract', string='Contract', tracking=True,
                                  domain="[('company_id', '=', company_id), ('status', '=', 'active'), '|', ('branch_id', '=', branch_id), ('branch_id', '=', False)]")
    city_id = fields.Many2one('delivery.city', string='City', tracking=True)
    name = fields.Char(string='Rule Name', required=True, tracking=True)
    pricing_type = fields.Selection([
        ('per_order', 'Per Order'),
        ('per_distance', 'Per Distance (KM)'),
        ('per_zone', 'Per Zone'),
        ('tiered', 'Tiered Slabs'),
        ('bonus', 'Bonus / Incentive'),
        ('penalty', 'Penalty / Deduction'),
        ('fixed_salary', 'Fixed Salary'),
        ('experience_incentive', 'Experience Incentive (حافز الخبرة)'),
        ('capacity_incentive', 'Valid DA Capacity Incentive (حافز السعة)'),
    ], string='Pricing Type', default='per_order', required=True, tracking=True)

    vehicle_type = fields.Selection([
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle / Bike'),
        ('all', 'All Vehicles'),
    ], string='Vehicle Type', default='all', tracking=True)
    rider_performance_level = fields.Selection([
        ('high_performance', 'High Performance'),
        ('active_basic', 'Active (Basic)'),
        ('all', 'All Levels'),
    ], string='Rider Performance Level', default='all', tracking=True)

    base_amount = fields.Float(string='Base Amount (SAR)', digits=(12, 2), required=True, tracking=True)
    per_km_amount = fields.Float(string='Per KM Amount (SAR)', digits=(12, 2))
    km_start_from = fields.Integer(string='KM Starts From', default=1,
                                    help='Per-KM charge starts after this KM (e.g., 2 means first 2 KM included in base)')
    max_km = fields.Integer(string='Max KM Cap', help='Maximum KM billed per order')

    daily_rate = fields.Float(string='Daily Rate (SAR)', digits=(12, 2),
                               help='Fixed salary: daily rate per rider')
    working_days = fields.Integer(string='Working Days/Month',
                                   help='Fixed salary: number of working days per month')
    monthly_total = fields.Float(string='Monthly Total (SAR)', digits=(12, 2),
                                  compute='_compute_monthly_total', store=True)

    fallback_per_order = fields.Float(string='Fallback Per Order (SAR)', digits=(12, 2),
                                       help='If KPI conditions not met, pay this per order instead of salary')
    bonus_threshold = fields.Integer(string='Bonus Threshold (Orders/Day)',
                                      help='Orders per day after which bonus applies')
    bonus_per_order = fields.Float(string='Bonus Per Extra Order (SAR)', digits=(12, 2),
                                    help='SAR per order above the bonus threshold')

    shift_adherence_min = fields.Float(string='Min Shift Adherence (%)', digits=(5, 2),
                                        help='Minimum shift adherence percentage for salary eligibility')
    on_time_delivery_min = fields.Float(string='Min On-Time Delivery (%)', digits=(5, 2),
                                         help='Minimum on-time delivery percentage for salary eligibility')
    order_acceptance_min = fields.Float(string='Min Order Acceptance (%)', digits=(5, 2),
                                         help='Minimum order acceptance percentage for salary eligibility')

    cod_rate = fields.Float(string='COD Rate (SAR)', digits=(12, 2),
                             help='Rate for Cash on Delivery orders')
    paid_rate = fields.Float(string='Paid Rate (SAR)', digits=(12, 2),
                              help='Rate for pre-paid orders')
    stacking_discount = fields.Float(string='Stacking Discount (SAR)', digits=(12, 2),
                                      help='Discount for stacked/bundled orders')

    order_rejection_free_daily = fields.Integer(string='Free Rejections/Day', default=2,
                                                  help='Number of free order rejections per day before penalty')
    order_rejection_penalty = fields.Float(string='Rejection Penalty (SAR)', digits=(12, 2), default=50.0,
                                            help='Penalty per rejected order after free limit')

    min_orders = fields.Integer(string='Min Orders')
    max_orders = fields.Integer(string='Max Orders')
    bonus_amount = fields.Float(string='Bonus Amount (SAR)', digits=(12, 2))

    slab_ids = fields.One2many('delivery.pricing.slab', 'pricing_rule_id', string='Pricing Slabs')
    slab_count = fields.Integer(compute='_compute_slab_count')

    incentive_level_ids = fields.One2many('delivery.incentive.level', 'pricing_rule_id', string='Incentive Levels')
    incentive_level_count = fields.Integer(compute='_compute_incentive_level_count')

    effective_from = fields.Date(string='Effective From', required=True)
    effective_to = fields.Date(string='Effective To')
    is_active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    @api.depends('daily_rate', 'working_days')
    def _compute_monthly_total(self):
        for rec in self:
            rec.monthly_total = (rec.daily_rate or 0) * (rec.working_days or 0)

    def _compute_slab_count(self):
        for rec in self:
            rec.slab_count = len(rec.slab_ids)

    def _compute_incentive_level_count(self):
        for rec in self:
            rec.incentive_level_count = len(rec.incentive_level_ids)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.branch_id = False
            active_contract = self.env['delivery.contract'].search([
                ('company_id', '=', self.company_id.id),
                ('status', '=', 'active'),
            ], limit=1)
            self.contract_id = active_contract.id if active_contract else False

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.branch_id:
            self.city_id = self.branch_id.city_id
            active_contract = self.env['delivery.contract'].search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', self.branch_id.id),
                ('status', '=', 'active'),
            ], limit=1)
            if active_contract:
                self.contract_id = active_contract.id


class DeliveryPricingSlab(models.Model):
    _name = 'delivery.pricing.slab'
    _description = 'Pricing Tier Slab'
    _order = 'sequence, from_orders'

    pricing_rule_id = fields.Many2one('delivery.pricing.rule', string='Pricing Rule',
                                       required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=1)
    from_orders = fields.Integer(string='From Orders', required=True)
    to_orders = fields.Integer(string='To Orders', help='Leave empty for unlimited')
    price_per_order = fields.Float(string='Price Per Order (SAR)', digits=(12, 2), required=True)
    max_payout = fields.Float(string='Max Payout (SAR)', digits=(12, 2),
                               help='Maximum payout for this tier')
    label = fields.Char(string='Tier Label')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    def name_get(self):
        result = []
        for rec in self:
            to_label = str(rec.to_orders) if rec.to_orders else '∞'
            result.append((rec.id, f"{rec.from_orders} – {to_label} @ {rec.price_per_order} SAR"))
        return result
