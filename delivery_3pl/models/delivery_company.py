from odoo import models, fields, api


class DeliveryCompany(models.Model):
    _name = 'delivery.company'
    _description = 'Delivery Company (Platform)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Company Name (EN)', required=True, tracking=True)
    name_ar = fields.Char(string='Company Name (AR)')
    logo = fields.Binary(string='Logo')
    contact_email = fields.Char(string='Contact Email')
    contact_phone = fields.Char(string='Contact Phone')
    settlement_cycle = fields.Selection([
        ('weekly', 'Weekly'),
        ('semi_monthly', 'Semi-Monthly'),
        ('monthly', 'Monthly'),
    ], string='Default Settlement Cycle', default='monthly', required=True, tracking=True)
    is_active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')

    branch_ids = fields.One2many('delivery.company.branch', 'company_id', string='Branches')
    contract_ids = fields.One2many('delivery.contract', 'company_id', string='Contracts')
    rider_ids = fields.One2many('delivery.rider', 'primary_company_id', string='Riders')
    settlement_ids = fields.One2many('delivery.settlement', 'company_id', string='Settlements')
    pricing_rule_ids = fields.One2many('delivery.pricing.rule', 'company_id', string='Pricing Rules')

    branch_count = fields.Integer(compute='_compute_branch_count', string='Branches')
    contract_count = fields.Integer(compute='_compute_contract_count', string='Contracts')
    rider_count = fields.Integer(compute='_compute_rider_count', string='Riders')

    def _compute_branch_count(self):
        for rec in self:
            rec.branch_count = len(rec.branch_ids)

    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = len(rec.contract_ids)

    def _compute_rider_count(self):
        for rec in self:
            rec.rider_count = len(rec.rider_ids)

    def action_view_branches(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Branches - {self.name}',
            'res_model': 'delivery.company.branch',
            'view_mode': 'tree,form',
            'domain': [('company_id', '=', self.id)],
            'context': {'default_company_id': self.id},
        }

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Contracts - {self.name}',
            'res_model': 'delivery.contract',
            'view_mode': 'tree,form',
            'domain': [('company_id', '=', self.id)],
            'context': {'default_company_id': self.id},
        }

    def action_view_riders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Riders - {self.name}',
            'res_model': 'delivery.rider',
            'view_mode': 'tree,form',
            'domain': [('primary_company_id', '=', self.id)],
            'context': {'default_primary_company_id': self.id},
        }
