/** @odoo-module **/

import { AccountReportHeader } from "@account_reports/components/account_report/header/header";
import { patch } from "@web/core/utils/patch";

patch(AccountReportHeader.prototype, {
    get areMonthlyColumnsFolded() {
        return Boolean(this.controller.options.fa_register_months_folded);
    },

    toggleMonthlyColumns() {
        this.controller.options.fa_register_months_folded = !this.areMonthlyColumnsFolded;
    },
});
