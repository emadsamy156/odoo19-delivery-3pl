from odoo import models, fields, api


class DeliveryCompanyBranch(models.Model):
    _name = 'delivery.company.branch'
    _description = 'Company Branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'company_id, name'

    company_id = fields.Many2one('delivery.company', string='Company', required=True,
                                  tracking=True, ondelete='cascade')
    city_id = fields.Many2one('delivery.city', string='City', tracking=True)
    name = fields.Char(string='Branch Name (EN)', required=True, tracking=True)
    name_ar = fields.Char(string='Branch Name (AR)')
    branch_code = fields.Char(string='Branch Code', tracking=True)
    contact_person = fields.Char(string='Contact Person')
    contact_phone = fields.Char(string='Contact Phone')
    is_active = fields.Boolean(string='Active', default=True, tracking=True)

    contract_ids = fields.One2many('delivery.contract', 'branch_id', string='Contracts')
    rider_ids = fields.One2many('delivery.rider', 'branch_id', string='Riders')
    pricing_rule_ids = fields.One2many('delivery.pricing.rule', 'branch_id', string='Pricing Rules')
    settlement_ids = fields.One2many('delivery.settlement', 'branch_id', string='Settlements')
    import_session_ids = fields.One2many('delivery.import.session', 'branch_id', string='Imports')

    contract_count = fields.Integer(compute='_compute_contract_count')
    rider_count = fields.Integer(compute='_compute_rider_count')
    active_contract_id = fields.Many2one(
        'delivery.contract', string='Active Contract',
        compute='_compute_active_contract', store=False,
    )

    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = len(rec.contract_ids)

    def _compute_rider_count(self):
        for rec in self:
            rec.rider_count = len(rec.rider_ids)

    @api.depends('contract_ids', 'contract_ids.status')
    def _compute_active_contract(self):
        for rec in self:
            active = rec.contract_ids.filtered(lambda c: c.status == 'active')
            rec.active_contract_id = active.sorted('version', reverse=True)[:1]

    def name_get(self):
        result = []
        for rec in self:
            label = rec.name
            if rec.branch_code:
                label = f"[{rec.branch_code}] {rec.name}"
            result.append((rec.id, label))
        return result

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Contracts - {self.name}',
            'res_model': 'delivery.contract',
            'view_mode': 'tree,form',
            'domain': [('branch_id', '=', self.id)],
            'context': {
                'default_company_id': self.company_id.id,
                'default_branch_id': self.id,
            },
        }

    def action_view_riders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Riders - {self.name}',
            'res_model': 'delivery.rider',
            'view_mode': 'tree,form',
            'domain': [('branch_id', '=', self.id)],
            'context': {
                'default_primary_company_id': self.company_id.id,
                'default_branch_id': self.id,
            },
        }
