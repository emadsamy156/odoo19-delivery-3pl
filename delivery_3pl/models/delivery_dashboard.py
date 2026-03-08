from odoo import models, fields, api
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class DeliveryDashboard(models.AbstractModel):
    _name = 'delivery.dashboard'
    _description = 'Delivery Dashboard Data Provider'

    @api.model
    def get_dashboard_data(self, date_from=False, date_to=False):
        today = date.today()
        if not date_from:
            date_from = today.replace(day=1)
        else:
            date_from = fields.Date.from_string(date_from)
        if not date_to:
            date_to = today
        else:
            date_to = fields.Date.from_string(date_to)

        prev_start = date_from - relativedelta(months=1)
        prev_end = date_to - relativedelta(months=1)

        Company = self.env['delivery.company']
        Branch = self.env['delivery.company.branch']
        Rider = self.env['delivery.rider']
        Contract = self.env['delivery.contract']
        Settlement = self.env['delivery.settlement']

        total_companies = Company.search_count([('is_active', '=', True)])
        total_branches = Branch.search_count([('is_active', '=', True)])
        total_riders = Rider.search_count([])
        active_riders = Rider.search_count([('status', '=', 'active')])
        inactive_riders = Rider.search_count([('status', '=', 'inactive')])
        suspended_riders = Rider.search_count([('status', '=', 'suspended')])
        active_contracts = Contract.search_count([('status', '=', 'active')])

        settlements = Settlement.search([
            ('period_start', '>=', date_from),
            ('period_end', '<=', date_to),
        ])
        total_orders = sum(s.total_orders for s in settlements)
        total_gross = sum(s.gross_amount for s in settlements)
        total_net = sum(s.net_amount for s in settlements)
        total_penalties = sum(s.penalties for s in settlements)
        total_bonuses = sum(s.bonuses for s in settlements)

        prev_settlements = Settlement.search([
            ('period_start', '>=', prev_start),
            ('period_end', '<=', prev_end),
        ])
        prev_orders = sum(s.total_orders for s in prev_settlements)
        prev_gross = sum(s.gross_amount for s in prev_settlements)
        prev_net = sum(s.net_amount for s in prev_settlements)

        orders_growth = self._calc_growth(total_orders, prev_orders)
        gross_growth = self._calc_growth(total_gross, prev_gross)
        net_growth = self._calc_growth(total_net, prev_net)

        settlements_by_status = {
            'draft': Settlement.search_count([('status', '=', 'draft')]),
            'pending': Settlement.search_count([('status', '=', 'pending_approval')]),
            'approved': Settlement.search_count([('status', '=', 'approved')]),
            'locked': Settlement.search_count([('status', '=', 'locked')]),
        }

        company_data = []
        companies = Company.search([('is_active', '=', True)], limit=20)
        for comp in companies:
            comp_settlements = settlements.filtered(lambda s: s.company_id.id == comp.id)
            company_data.append({
                'id': comp.id,
                'name': comp.name,
                'name_ar': comp.name_ar or comp.name,
                'branches': len(comp.branch_ids.filtered('is_active')),
                'riders': len(comp.rider_ids.filtered(lambda r: r.status == 'active')),
                'contracts': len(comp.contract_ids.filtered(lambda c: c.status == 'active')),
                'orders': sum(s.total_orders for s in comp_settlements),
                'gross': sum(s.gross_amount for s in comp_settlements),
                'net': sum(s.net_amount for s in comp_settlements),
            })

        branch_data = []
        branches = Branch.search([('is_active', '=', True)], limit=30)
        for br in branches:
            br_settlements = settlements.filtered(lambda s: s.branch_id.id == br.id)
            branch_data.append({
                'id': br.id,
                'name': br.name,
                'company': br.company_id.name,
                'riders': len(br.rider_ids.filtered(lambda r: r.status == 'active')),
                'orders': sum(s.total_orders for s in br_settlements),
                'gross': sum(s.gross_amount for s in br_settlements),
            })

        recent_settlements = Settlement.search([], order='create_date desc', limit=10)
        recent_list = []
        for s in recent_settlements:
            recent_list.append({
                'id': s.id,
                'number': s.settlement_number,
                'company': s.company_id.name,
                'branch': s.branch_id.name or '-',
                'status': s.status,
                'period': '%s → %s' % (
                    fields.Date.to_string(s.period_start),
                    fields.Date.to_string(s.period_end),
                ),
                'orders': s.total_orders,
                'gross': s.gross_amount,
                'net': s.net_amount,
            })

        Penalty = self.env['delivery.rider.penalty']
        total_penalty_count = Penalty.search_count([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])

        return {
            'kpis': {
                'total_companies': total_companies,
                'total_branches': total_branches,
                'total_riders': total_riders,
                'active_riders': active_riders,
                'inactive_riders': inactive_riders,
                'suspended_riders': suspended_riders,
                'active_contracts': active_contracts,
                'total_orders': total_orders,
                'total_gross': round(total_gross, 2),
                'total_net': round(total_net, 2),
                'total_penalties': round(total_penalties, 2),
                'total_bonuses': round(total_bonuses, 2),
                'orders_growth': orders_growth,
                'gross_growth': gross_growth,
                'net_growth': net_growth,
                'penalty_count': total_penalty_count,
            },
            'settlements_by_status': settlements_by_status,
            'company_data': company_data,
            'branch_data': branch_data,
            'recent_settlements': recent_list,
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
        }

    def _calc_growth(self, current, previous):
        if previous and previous > 0:
            return round(((current - previous) / previous) * 100, 1)
        elif current > 0:
            return 100.0
        return 0.0
