from odoo import models, fields, api


class DeliveryIncentiveLevel(models.Model):
    _name = 'delivery.incentive.level'
    _description = 'Incentive Performance Level (A/B/C/D)'
    _order = 'pricing_rule_id, sequence'

    pricing_rule_id = fields.Many2one('delivery.pricing.rule', string='Pricing Rule',
                                       required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    level = fields.Selection([
        ('A', 'Level A'),
        ('B', 'Level B'),
        ('C', 'Level C'),
        ('D', 'Level D'),
    ], string='Performance Level', required=True)
    range_from = fields.Float(string='Range From (%)', digits=(5, 2),
                               help='For Experience: rider rank percentage from. For Capacity: min valid DAs')
    range_to = fields.Float(string='Range To (%)', digits=(5, 2),
                             help='For Experience: rider rank percentage to. For Capacity: max valid DAs')
    bike_amount = fields.Float(string='Bike Amount (SAR)', digits=(12, 2),
                                help='Incentive amount per valid DA for Bike riders')
    car_amount = fields.Float(string='Car Amount (SAR)', digits=(12, 2),
                               help='Incentive amount per valid DA for Car riders')
    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"Level {rec.level}: Bike {rec.bike_amount} / Car {rec.car_amount} SAR"))
        return result


class DeliveryValidityCriteria(models.Model):
    _name = 'delivery.validity.criteria'
    _description = 'Valid DA Criteria (شروط صلاحية المندوب)'
    _inherit = ['mail.thread']
    _order = 'contract_id'

    contract_id = fields.Many2one('delivery.contract', string='Contract', tracking=True, ondelete='cascade')
    branch_id = fields.Many2one('delivery.company.branch', string='Branch', tracking=True)
    company_id = fields.Many2one('delivery.company', string='Company', tracking=True)
    name = fields.Char(string='Criteria Name', required=True, default='Default Validity Criteria')
    is_active = fields.Boolean(string='Active', default=True)

    min_daily_online_hours = fields.Float(string='Min Daily Online Hours', digits=(5, 2), default=10.0,
                                           help='Minimum total daily online time within scheduled shifts')
    min_valid_days = fields.Integer(string='Min Valid Days/Month', default=26,
                                     help='Minimum number of valid days in a month')
    must_attend_first_days = fields.Integer(string='Must Attend First N Days', default=3,
                                             help='Number of must-attend days at start of month')
    must_attend_last_days = fields.Integer(string='Must Attend Last N Days', default=4,
                                            help='Number of must-attend days at end of month')
    must_attend_min_valid = fields.Integer(string='Min Valid Must-Attend Days', default=6,
                                            help='Minimum valid days out of total must-attend days (e.g. 6 out of 7)')
    min_monthly_orders = fields.Integer(string='Min Monthly Orders', default=300,
                                          help='Minimum number of orders in a month to be valid')
    min_orders_must_attend_day = fields.Integer(string='Min Orders on Must-Attend Day', default=6,
                                                  help='Minimum orders to complete on a must-attend day to become valid')
    min_calendar_pct_mid_month = fields.Float(string='Min Calendar % (Mid-Month Join)', digits=(5, 2), default=90.0,
                                               help='If rider joins mid-month, min % of calendar days they must be present')
    validity_pct_threshold = fields.Float(string='Validity % Threshold', digits=(5, 2), default=99.0,
                                           help='Overall validity percentage threshold')
    require_self_delivery = fields.Boolean(string='Require Self Delivery', default=True,
                                            help='Rider must be a self-delivery rider (compliant)')
    facial_verification_min_pct = fields.Float(string='Min Facial Verification %', digits=(5, 2), default=80.0,
                                                help='Min % of online active days rider must pass facial verification')
    max_cheating_rider_pct = fields.Float(string='Max Cheating Rider %', digits=(5, 2), default=10.0,
                                           help='If partner has this % or more cheating riders, all disqualified')
    duplicate_iqama_policy = fields.Selection([
        ('first_only', 'Only First Registration Valid'),
        ('all_valid', 'All Valid'),
    ], string='Duplicate Iqama Policy', default='first_only')
    notes = fields.Text(string='Notes')


class DeliveryExperienceScoreConfig(models.Model):
    _name = 'delivery.experience.score.config'
    _description = 'Experience Score Calculation Config'
    _inherit = ['mail.thread']
    _order = 'contract_id'

    contract_id = fields.Many2one('delivery.contract', string='Contract', tracking=True, ondelete='cascade')
    branch_id = fields.Many2one('delivery.company.branch', string='Branch', tracking=True)
    company_id = fields.Many2one('delivery.company', string='Company', tracking=True)
    name = fields.Char(string='Config Name', required=True, default='Experience Score Config')
    is_active = fields.Boolean(string='Active', default=True)

    on_time_delivery_weight = fields.Float(string='On-Time Delivery Weight (%)', digits=(5, 2), default=38.0,
                                            help='Weight of on-time delivery rate in experience score')
    cancellation_rate_weight = fields.Float(string='Cancellation Rate (D Liability) Weight (%)', digits=(5, 2), default=50.0,
                                             help='Weight of (1 - cancellation rate) in experience score')
    advance_delivery_weight = fields.Float(string='Delivered in Advance Weight (%)', digits=(5, 2), default=12.0,
                                            help='Weight of (1 - delivered in advance rate) in experience score')
    min_orders_for_ranking = fields.Integer(string='Min Orders to Enter Ranking', default=100,
                                              help='Minimum orders for rider to be included in experience ranking pool')
    only_valid_da_eligible = fields.Boolean(string='Only Valid DA Eligible', default=True,
                                             help='Only valid DAs are entitled to experience incentive')
    notes = fields.Text(string='Notes')
