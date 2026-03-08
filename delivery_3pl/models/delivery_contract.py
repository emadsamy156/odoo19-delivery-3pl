from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class DeliveryContract(models.Model):
    _name = 'delivery.contract'
    _description = 'Company Contract (Versioned)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'company_id, version desc'

    company_id = fields.Many2one('delivery.company', string='Company', required=True, tracking=True, ondelete='cascade')
    branch_id = fields.Many2one('delivery.company.branch', string='Branch', tracking=True,
                                 domain="[('company_id', '=', company_id)]")
    contract_number = fields.Char(string='Contract Number', required=True, tracking=True)
    version = fields.Integer(string='Version', default=1, required=True, tracking=True)
    contract_type = fields.Selection([
        ('parcel', 'Parcel Contract (عقد طرود)'),
        ('service', 'Service Contract (عقد خدمات)'),
        ('other', 'Other'),
    ], string='Contract Type', default='parcel', required=True, tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', required=True, tracking=True)

    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    settlement_cycle = fields.Selection([
        ('weekly', 'Weekly'),
        ('semi_monthly', 'Semi-Monthly'),
        ('monthly', 'Monthly'),
    ], string='Settlement Cycle', default='monthly', required=True, tracking=True)
    commission_rate = fields.Float(string='Commission Rate (%)', digits=(5, 2), tracking=True)
    penalty_policy = fields.Text(string='Penalty Policy')
    deposit_policy = fields.Text(string='Deposit Policy')
    payment_terms_days = fields.Integer(string='Payment Terms (Days)', default=30)
    auto_renew = fields.Boolean(string='Auto-Renew', default=False)
    column_mapping = fields.Text(string='Excel Column Mapping (JSON)')
    notes = fields.Text(string='Notes')

    pricing_rule_ids = fields.One2many('delivery.pricing.rule', 'contract_id', string='Pricing Rules')
    pricing_rule_count = fields.Integer(compute='_compute_pricing_rule_count')
    settlement_ids = fields.One2many('delivery.settlement', 'contract_id', string='Settlements')
    import_session_ids = fields.One2many('delivery.import.session', 'contract_id', string='Import Sessions')
    validity_criteria_ids = fields.One2many('delivery.validity.criteria', 'contract_id', string='Validity Criteria')
    experience_config_ids = fields.One2many('delivery.experience.score.config', 'contract_id', string='Experience Score Config')
    company_target_ids = fields.One2many('delivery.company.target', 'contract_id', string='Company Targets')

    display_name_computed = fields.Char(compute='_compute_display_name_computed', store=False)

    def _compute_pricing_rule_count(self):
        for rec in self:
            rec.pricing_rule_count = len(rec.pricing_rule_ids)

    @api.depends('contract_number', 'version', 'status', 'contract_type')
    def _compute_display_name_computed(self):
        for rec in self:
            type_label = dict(rec._fields['contract_type'].selection).get(rec.contract_type, '')
            rec.display_name_computed = f"{rec.contract_number} (v{rec.version}) - {rec.status} [{type_label}]"

    def name_get(self):
        result = []
        for rec in self:
            branch_label = f" [{rec.branch_id.branch_code}]" if rec.branch_id and rec.branch_id.branch_code else ""
            result.append((rec.id, f"{rec.contract_number}{branch_label} (v{rec.version})"))
        return result

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.branch_id = False
            return {'domain': {'branch_id': [('company_id', '=', self.company_id.id)]}}

    def action_activate(self):
        self.ensure_one()
        if self.status != 'draft':
            raise ValidationError('Only draft contracts can be activated.')
        domain = [
            ('company_id', '=', self.company_id.id),
            ('status', '=', 'active'),
            ('id', '!=', self.id),
        ]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))
        current_active = self.search(domain)
        current_active.write({'status': 'expired'})
        self.write({'status': 'active'})

    def action_terminate(self):
        self.ensure_one()
        if self.status != 'active':
            raise ValidationError('Only active contracts can be terminated.')
        self.write({'status': 'terminated'})

    def action_renew(self):
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id)]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))
        max_version = max(self.search(domain).mapped('version') or [0])
        today = fields.Date.today()
        new_contract = self.copy({
            'version': max_version + 1,
            'status': 'draft',
            'start_date': today,
            'end_date': today + relativedelta(years=1),
            'notes': f'Renewed from v{self.version}',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.contract',
            'res_id': new_contract.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.constrains('status', 'company_id', 'branch_id')
    def _check_single_active(self):
        for rec in self:
            if rec.status == 'active':
                domain = [
                    ('company_id', '=', rec.company_id.id),
                    ('status', '=', 'active'),
                ]
                if rec.branch_id:
                    domain.append(('branch_id', '=', rec.branch_id.id))
                active_count = self.search_count(domain)
                if active_count > 1:
                    branch_label = f" branch {rec.branch_id.name}" if rec.branch_id else ""
                    raise ValidationError(
                        f'Company {rec.company_id.name}{branch_label} can only have one active contract at a time.'
                    )
