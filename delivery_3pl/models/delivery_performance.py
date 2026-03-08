from odoo import models, fields, api


class DeliveryDailyPerformance(models.Model):
    _name = 'delivery.daily.performance'
    _description = 'Daily Rider Performance (أداء يومي)'
    _inherit = ['mail.thread']
    _order = 'date desc, rider_id'

    branch_id = fields.Many2one('delivery.company.branch', string='Branch', required=True, tracking=True)
    company_id = fields.Many2one('delivery.company', string='Company', related='branch_id.company_id', store=True)
    rider_id = fields.Many2one('delivery.rider', string='Rider', required=True, tracking=True, ondelete='cascade')
    import_session_id = fields.Many2one('delivery.import.session', string='Import Session')
    date = fields.Date(string='Date', required=True, tracking=True)

    platform_account_id = fields.Char(string='Platform Account ID (معرف الحساب)',
                                       help='Account ID on the platform, may differ from rider if sub-rider')
    account_name = fields.Char(string='Account Name (مستخدم الحساب)')
    vehicle_type_company = fields.Selection([
        ('car', 'Private Car'),
        ('motorcycle', 'Bike'),
    ], string='Vehicle Type (Company)')
    vehicle_type_contract = fields.Selection([
        ('car', 'Car'),
        ('motorcycle', 'Bike'),
    ], string='Vehicle Type (Contract)')
    license_plate = fields.Char(string='License Plate (رقم اللوحة)')

    platform_target = fields.Integer(string='Platform Target (تارجيت)', default=0)
    accepted_orders = fields.Integer(string='Accepted Orders (المهام المقبولة)', default=0)
    delivered_orders = fields.Integer(string='Delivered Orders (المهام المُسلمة)', default=0)
    large_orders_completed = fields.Integer(string='Large Orders Completed (مهام الطلبات الكبيرة)', default=0)
    cancelled_orders = fields.Integer(string='Cancelled Orders (المهام المُلغاة)', default=0)
    rejected_orders = fields.Integer(string='Rejected Orders', default=0)

    valid_online_hours = fields.Float(string='Valid Online Hours', digits=(8, 2), default=0.0)
    peak_hours = fields.Float(string='Peak Hours', digits=(8, 2), default=0.0)
    total_online_hours = fields.Float(string='Total Online Hours', digits=(8, 2), default=0.0)

    is_valid_day = fields.Boolean(string='Valid Day (يوم صالح)', default=False)
    is_must_attend_day = fields.Boolean(string='Must Attend Day', default=False)
    validity_notes = fields.Char(string='Validity Notes')

    on_time_deliveries = fields.Integer(string='On-Time Deliveries', default=0)
    advance_deliveries = fields.Integer(string='Delivered in Advance', default=0)

    _sql_constraints = [
        ('unique_rider_date', 'unique(rider_id, date, branch_id)',
         'Only one performance record per rider per day per branch is allowed.'),
    ]


class DeliveryMonthlyPerformance(models.Model):
    _name = 'delivery.monthly.performance'
    _description = 'Monthly Rider Performance Summary (ملخص أداء شهري)'
    _inherit = ['mail.thread']
    _order = 'period_year desc, period_month desc, rider_id'

    branch_id = fields.Many2one('delivery.company.branch', string='Branch', required=True, tracking=True)
    company_id = fields.Many2one('delivery.company', string='Company', related='branch_id.company_id', store=True)
    rider_id = fields.Many2one('delivery.rider', string='Rider', required=True, tracking=True, ondelete='cascade')
    period_month = fields.Integer(string='Month', required=True)
    period_year = fields.Integer(string='Year', required=True)
    period_display = fields.Char(string='Period', compute='_compute_period_display', store=True)

    is_valid = fields.Boolean(string='Valid DA (صالح)', default=False, tracking=True)
    validity_reason = fields.Char(string='Validity Reason (السبب)', tracking=True)

    valid_days = fields.Integer(string='Valid Contact Days (أيام الاتصال الصالحة)', default=0)
    valid_hours = fields.Float(string='Valid Contact Hours (ساعات الاتصال الصالحة)', digits=(8, 2), default=0.0)
    valid_peak_hours = fields.Float(string='Valid Peak Hours (ساعات الذروة الصالحة)', digits=(8, 2), default=0.0)

    delivered_orders = fields.Integer(string='Delivered Orders (الطلبات المُسلمة)', default=0)
    accepted_orders = fields.Integer(string='Accepted Orders', default=0)
    cancelled_orders = fields.Integer(string='Cancelled Orders', default=0)
    on_time_deliveries = fields.Integer(string='On-Time Deliveries', default=0)
    advance_deliveries = fields.Integer(string='Delivered in Advance', default=0)

    on_time_rate = fields.Float(string='On-Time Delivery Rate', digits=(8, 4), compute='_compute_rates', store=True)
    cancellation_rate = fields.Float(string='Cancellation Rate', digits=(8, 4), compute='_compute_rates', store=True)
    advance_rate = fields.Float(string='Advance Delivery Rate', digits=(8, 4), compute='_compute_rates', store=True)
    experience_score = fields.Float(string='Experience Score', digits=(8, 4), tracking=True)
    performance_level = fields.Selection([
        ('A', 'Level A'),
        ('B', 'Level B'),
        ('C', 'Level C'),
        ('D', 'Level D'),
    ], string='Performance Level', tracking=True)

    order_base_amount = fields.Float(string='Order Base Pricing (التسعير حسب الطلب)', digits=(12, 2), default=0.0)
    capacity_incentive = fields.Float(string='Valid DA Capacity Incentive (حوافز سعة الطلب)', digits=(12, 2), default=0.0)
    experience_incentive = fields.Float(string='Experience Incentive (حوافز التسليم في الوقت)', digits=(12, 2), default=0.0)
    subsidy = fields.Float(string='Subsidy (الإعانة)', digits=(12, 2), default=0.0)
    dxg = fields.Float(string='DXG', digits=(12, 2), default=0.0)
    other_activities = fields.Float(string='Other Activities & Rewards (الأنشطة والمكافآت)', digits=(12, 2), default=0.0)
    deductions = fields.Float(string='Deductions (الخصم)', digits=(12, 2), default=0.0,
                               help='Negative value')
    food_damage_compensation = fields.Float(string='Food Damage Compensation (تعويض تلف الطعام)', digits=(12, 2), default=0.0,
                                              help='Negative value')
    other_adjustment = fields.Float(string='Other Adjustment (تعديل آخر)', digits=(12, 2), default=0.0)
    tips_excl_vat = fields.Float(string='Tips excl. VAT (البقشيش بدون ضريبة)', digits=(12, 2), default=0.0)

    total_revenue = fields.Float(string='Total Revenue', digits=(12, 2),
                                  compute='_compute_total_revenue', store=True)

    @api.depends('period_month', 'period_year')
    def _compute_period_display(self):
        months = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                  7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        for rec in self:
            rec.period_display = f"{months.get(rec.period_month, '?')} {rec.period_year}"

    @api.depends('delivered_orders', 'on_time_deliveries', 'accepted_orders',
                 'cancelled_orders', 'advance_deliveries')
    def _compute_rates(self):
        for rec in self:
            rec.on_time_rate = (rec.on_time_deliveries / rec.delivered_orders) if rec.delivered_orders else 0
            rec.cancellation_rate = (rec.cancelled_orders / rec.accepted_orders) if rec.accepted_orders else 0
            rec.advance_rate = (rec.advance_deliveries / rec.delivered_orders) if rec.delivered_orders else 0

    @api.depends('order_base_amount', 'capacity_incentive', 'experience_incentive',
                 'subsidy', 'dxg', 'other_activities', 'deductions',
                 'food_damage_compensation', 'other_adjustment', 'tips_excl_vat')
    def _compute_total_revenue(self):
        for rec in self:
            rec.total_revenue = (
                rec.order_base_amount + rec.capacity_incentive + rec.experience_incentive +
                rec.subsidy + rec.dxg + rec.other_activities +
                rec.deductions + rec.food_damage_compensation + rec.other_adjustment +
                rec.tips_excl_vat
            )

    _sql_constraints = [
        ('unique_rider_month', 'unique(rider_id, period_month, period_year, branch_id)',
         'Only one monthly performance record per rider per month per branch.'),
    ]
