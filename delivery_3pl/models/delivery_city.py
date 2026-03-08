from odoo import models, fields


class DeliveryCity(models.Model):
    _name = 'delivery.city'
    _description = 'Delivery City / Zone'
    _order = 'tier, name'

    name = fields.Char(string='City Name (EN)', required=True)
    name_ar = fields.Char(string='City Name (AR)')
    tier = fields.Selection([
        ('T1', 'T1 - Major City'),
        ('T2', 'T2 - Mid City'),
        ('T3', 'T3 - Small City'),
    ], string='Tier', default='T1', required=True)
    is_active = fields.Boolean(string='Active', default=True)

    def name_get(self):
        result = []
        for rec in self:
            label = f"{rec.name} ({rec.tier})"
            if rec.name_ar:
                label = f"{rec.name} / {rec.name_ar} ({rec.tier})"
            result.append((rec.id, label))
        return result
