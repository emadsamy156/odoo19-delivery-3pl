/** @odoo-module */

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class DeliveryDashboard extends Component {
    static template = "delivery_3pl.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: null,
            loading: true,
            dateFrom: this._getFirstDayOfMonth(),
            dateTo: this._getToday(),
        });
        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    _getFirstDayOfMonth() {
        const d = new Date();
        return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
    }

    _getToday() {
        return new Date().toISOString().split('T')[0];
    }

    async loadDashboard() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "delivery.dashboard",
                "get_dashboard_data",
                [],
                { date_from: this.state.dateFrom, date_to: this.state.dateTo }
            );
            this.state.data = data;
        } catch (e) {
            console.error("Dashboard load error:", e);
        }
        this.state.loading = false;
    }

    async onDateChange() {
        await this.loadDashboard();
    }

    onDateFromChange(ev) {
        this.state.dateFrom = ev.target.value;
    }

    onDateToChange(ev) {
        this.state.dateTo = ev.target.value;
    }

    formatNumber(val) {
        if (val === undefined || val === null) return "0";
        return Number(val).toLocaleString("en-US");
    }

    formatCurrency(val) {
        if (val === undefined || val === null) return "0.00 SAR";
        return Number(val).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }) + " SAR";
    }

    getGrowthClass(val) {
        if (val > 0) return "text-success";
        if (val < 0) return "text-danger";
        return "text-muted";
    }

    getGrowthIcon(val) {
        if (val > 0) return "fa-arrow-up";
        if (val < 0) return "fa-arrow-down";
        return "fa-minus";
    }

    getStatusLabel(status) {
        const labels = {
            draft: _t("Draft"),
            pending: _t("Pending"),
            approved: _t("Approved"),
            locked: _t("Locked"),
        };
        return labels[status] || status;
    }

    getStatusBadgeClass(status) {
        const classes = {
            draft: "badge bg-secondary",
            pending_approval: "badge bg-warning text-dark",
            pending: "badge bg-warning text-dark",
            approved: "badge bg-success",
            locked: "badge bg-info",
        };
        return classes[status] || "badge bg-secondary";
    }

    get totalSettlements() {
        if (!this.state.data) return 0;
        const s = this.state.data.settlements_by_status;
        return (s.draft || 0) + (s.pending || 0) + (s.approved || 0) + (s.locked || 0);
    }

    openCompanies() {
        this.action.doAction("delivery_3pl.action_delivery_company");
    }

    openBranches() {
        this.action.doAction("delivery_3pl.action_delivery_branch");
    }

    openRiders() {
        this.action.doAction("delivery_3pl.action_delivery_rider");
    }

    openContracts() {
        this.action.doAction("delivery_3pl.action_delivery_contract");
    }

    openSettlements() {
        this.action.doAction("delivery_3pl.action_delivery_settlement");
    }

    openPenalties() {
        this.action.doAction("delivery_3pl.action_delivery_rider_penalty");
    }

    getBarWidth(value, maxValue) {
        if (!maxValue || maxValue === 0) return "0%";
        return Math.min(Math.round((value / maxValue) * 100), 100) + "%";
    }

    get maxCompanyOrders() {
        if (!this.state.data || !this.state.data.company_data) return 1;
        return Math.max(...this.state.data.company_data.map(c => c.orders), 1);
    }

    get maxCompanyGross() {
        if (!this.state.data || !this.state.data.company_data) return 1;
        return Math.max(...this.state.data.company_data.map(c => c.gross), 1);
    }

    get maxBranchOrders() {
        if (!this.state.data || !this.state.data.branch_data) return 1;
        return Math.max(...this.state.data.branch_data.map(b => b.orders), 1);
    }
}

registry.category("actions").add("delivery_3pl.dashboard", DeliveryDashboard);
