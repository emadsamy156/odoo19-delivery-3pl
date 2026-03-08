from odoo import models, fields, api


class DeliveryCompanyTarget(models.Model):
    _name = 'delivery.company.target'
    _description = 'Company Target (تارجيت الشركة)'
    _inherit = ['mail.thread']
    _order = 'year desc, month desc'

    company_id = fields.Many2one('delivery.company', string='Company', required=True, tracking=True, ondelete='cascade')
    branch_id = fields.Many2one('delivery.company.branch', string='Branch', tracking=True,
                                 domain="[('company_id', '=', company_id)]")
    contract_id = fields.Many2one('delivery.contract', string='Contract', tracking=True,
                                  domain="[('company_id', '=', company_id), ('status', '=', 'active')]")
    month = fields.Integer(string='Month', required=True)
    year = fields.Integer(string='Year', required=True)
    period_display = fields.Char(string='Period', compute='_compute_period_display', store=True)

    level_a_min_valid_das = fields.Integer(string='Level A: Min Valid DAs', default=120)
    level_a_max_valid_das = fields.Integer(string='Level A: Max Valid DAs', default=130)
    level_b_min_valid_das = fields.Integer(string='Level B: Min Valid DAs', default=100)
    level_b_max_valid_das = fields.Integer(string='Level B: Max Valid DAs', default=119)
    level_c_min_valid_das = fields.Integer(string='Level C: Min Valid DAs', default=90)
    level_c_max_valid_das = fields.Integer(string='Level C: Max Valid DAs', default=99)
    level_d_below = fields.Integer(string='Level D: Below', default=90,
                                    help='If valid DAs below this number = Level D (no incentive)')

    level_a_bike_amount = fields.Float(string='Level A Bike Incentive (SAR)', digits=(12, 2), default=2000)
    level_a_car_amount = fields.Float(string='Level A Car Incentive (SAR)', digits=(12, 2), default=2500)
    level_b_bike_amount = fields.Float(string='Level B Bike Incentive (SAR)', digits=(12, 2), default=1200)
    level_b_car_amount = fields.Float(string='Level B Car Incentive (SAR)', digits=(12, 2), default=2000)
    level_c_bike_amount = fields.Float(string='Level C Bike Incentive (SAR)', digits=(12, 2), default=900)
    level_c_car_amount = fields.Float(string='Level C Car Incentive (SAR)', digits=(12, 2), default=1700)

    actual_valid_das = fields.Integer(string='Actual Valid DAs', compute='_compute_actuals', store=False)
    actual_total_riders = fields.Integer(string='Total Riders', compute='_compute_actuals', store=False)
    achieved_level = fields.Char(string='Achieved Level', compute='_compute_actuals', store=False)
    target_met = fields.Boolean(string='Target Met?', compute='_compute_actuals', store=False)

    tga_excl_vat = fields.Float(string='TGA excl. VAT (SAR)', digits=(12, 2), default=0.0,
                                 help='Total Gross Amount excluding VAT')
    total_due = fields.Float(string='Total Amount Due (SAR)', digits=(12, 2), default=0.0,
                              help='Total amount due from platform')

    keeta_base_rate = fields.Float(string='Platform Base Rate (النسبة الأساسية)', digits=(12, 2), default=0.0)
    keeta_ontime_rate = fields.Float(string='Platform On-Time Rate (نسبة التوصيل في الوقت)', digits=(12, 2), default=0.0)
    keeta_shift_rate = fields.Float(string='Platform Shift Rate (نسبة أوقات الدوام)', digits=(12, 2), default=0.0)

    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    @api.depends('period_display')
    def _compute_period_display(self):
        months = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                  7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        for rec in self:
            rec.period_display = f"{months.get(rec.month, '?')} {rec.year}"

    def _compute_actuals(self):
        for rec in self:
            domain = [('is_valid_da', '=', True), ('status', '=', 'active')]
            total_domain = [('status', '=', 'active')]
            if rec.branch_id:
                domain.append(('branch_id', '=', rec.branch_id.id))
                total_domain.append(('branch_id', '=', rec.branch_id.id))
            elif rec.company_id:
                domain.append(('primary_company_id', '=', rec.company_id.id))
                total_domain.append(('primary_company_id', '=', rec.company_id.id))
            rec.actual_valid_das = self.env['delivery.rider'].search_count(domain)
            rec.actual_total_riders = self.env['delivery.rider'].search_count(total_domain)
            valid = rec.actual_valid_das
            if valid >= rec.level_a_min_valid_das:
                rec.achieved_level = 'A'
                rec.target_met = True
            elif valid >= rec.level_b_min_valid_das:
                rec.achieved_level = 'B'
                rec.target_met = True
            elif valid >= rec.level_c_min_valid_das:
                rec.achieved_level = 'C'
                rec.target_met = True
            else:
                rec.achieved_level = 'D'
                rec.target_met = False

    _sql_constraints = [
        ('unique_target_month', 'unique(company_id, branch_id, month, year)',
         'Only one target per company/branch per month.'),
    ]


class DeliveryRiderDeduction(models.Model):
    _name = 'delivery.rider.deduction'
    _description = 'Rider Deduction (خصومات المندوب)'
    _inherit = ['mail.thread']
    _order = 'year desc, month desc, rider_id'

    rider_id = fields.Many2one('delivery.rider', string='Rider', required=True, tracking=True, ondelete='cascade')
    branch_id = fields.Many2one('delivery.company.branch', string='Branch',
                                 related='rider_id.branch_id', store=True)
    company_id = fields.Many2one('delivery.company', string='Company',
                                  related='rider_id.primary_company_id', store=True)
    settlement_id = fields.Many2one('delivery.settlement', string='Settlement')
    month = fields.Integer(string='Month', required=True)
    year = fields.Integer(string='Year', required=True)
    period_display = fields.Char(string='Period', compute='_compute_period_display', store=True)

    fuel_deduction = fields.Float(string='Fuel Deduction (خصم بنزين)', digits=(12, 2), default=0.0)
    car_rent = fields.Float(string='Car Rent (إيجار سيارة)', digits=(12, 2), default=0.0)
    housing = fields.Float(string='Housing (سكن)', digits=(12, 2), default=0.0)
    car_installment = fields.Float(string='Car Installment (قسط سيارة)', digits=(12, 2), default=0.0)
    advance_salary = fields.Float(string='Advance / Loan (سلف)', digits=(12, 2), default=0.0)
    food_allowance = fields.Float(string='Food Allowance (تغذية)', digits=(12, 2), default=0.0)
    other_deduction = fields.Float(string='Other Deduction (أخرى)', digits=(12, 2), default=0.0)
    total_deduction = fields.Float(string='Total Deduction', digits=(12, 2),
                                    compute='_compute_total_deduction', store=True)

    collection_amount = fields.Float(string='Collection from Platform (مبلغ التحصيل)', digits=(12, 2), default=0.0,
                                      help='Amount collected from platform for this rider')
    is_active_rider = fields.Boolean(string='Active Rider (فعال)', default=True)

    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    @api.depends('month', 'year')
    def _compute_period_display(self):
        months = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                  7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        for rec in self:
            rec.period_display = f"{months.get(rec.month, '?')} {rec.year}"

    @api.depends('fuel_deduction', 'car_rent', 'housing', 'car_installment',
                 'advance_salary', 'food_allowance', 'other_deduction')
    def _compute_total_deduction(self):
        for rec in self:
            rec.total_deduction = (
                rec.fuel_deduction + rec.car_rent + rec.housing +
                rec.car_installment + rec.advance_salary + rec.food_allowance +
                rec.other_deduction
            )
