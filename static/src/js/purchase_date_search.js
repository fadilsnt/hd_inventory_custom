/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { DateTimeInput } from "@web/core/datetime/datetime_input";

export class DateSearch extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            startDate: false,
            endDate: false,
        });

        // 🔑 WAJIB: bind context
        this.onStartDateChanged = this.onStartDateChanged.bind(this);
        this.onEndDateChanged = this.onEndDateChanged.bind(this);
        this.onClickPrintExcel = this.onClickPrintExcel.bind(this);
    }

    // ========================
    // DATE HANDLER
    // ========================
    onStartDateChanged(date) {
        this.state.startDate = date ? this.formatDate(date) : false;
        this.applySearch();
    }

    onEndDateChanged(date) {
        this.state.endDate = date ? this.formatDate(date) : false;
        this.applySearch();
    }

    formatDate(date) {
        const { year, month, day } = date.c;
        return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    }

    // ========================
    // SEARCH MODEL
    // ========================
    applySearch() {
        const { domain, context } = this.loadContextAndDomain();
        this.env.searchModel._domain = domain;
        this.env.searchModel._context = context;
        this.env.searchModel.search();
    }

    loadContextAndDomain() {
        let domain = [];
        let context = { ...this.props.context };

        if (this.state.startDate) {
            domain.push(["create_date", ">=", this.state.startDate]);
            context.startDate = this.state.startDate;
        }

        if (this.state.endDate) {
            domain.push(["create_date", "<=", this.state.endDate]);
            context.endDate = this.state.endDate;
        }

        // gabung domain lama (selain create_date)
        const originDomain = this.getOriginDomain(this.props.domain);
        domain = [...domain, ...originDomain];

        return { domain, context };
    }

    getOriginDomain(domain) {
        if (!Array.isArray(domain)) return [];
        return domain.filter(
            (item) =>
                Array.isArray(item) &&
                item[0] !== "create_date"
        );
    }

    // ========================
    // XLSX EXPORT
    // ========================
    onClickPrintExcel() {
        const { startDate, endDate } = this.state;

        if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
            this.notification.add(
                "End Date tidak boleh lebih kecil dari Start Date",
                { title: "Tanggal tidak valid", type: "danger" }
            );
            return;
        }

        const params = new URLSearchParams();
        if (startDate) params.append("start_date", startDate);
        if (endDate) params.append("end_date", endDate);

        this.actionService.doAction({
            type: "ir.actions.act_url",
            url: `/purchase/xlsx_report?${params.toString()}`,
            target: "self",
        });
    }
}

DateSearch.components = { DateTimeInput };
DateSearch.template = "hd_inventory_custom.DateSearch";
