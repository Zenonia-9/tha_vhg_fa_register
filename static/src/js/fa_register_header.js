/** @odoo-module **/

import { AccountReportHeader } from "@account_reports/components/account_report/header/header";
import { AccountReportLine } from "@account_reports/components/account_report/line/line";
import { patch } from "@web/core/utils/patch";

const MONTH_LABELS = new Set([
    "depreciation_apr", "depreciation_may", "depreciation_jun",
    "depreciation_jul", "depreciation_aug", "depreciation_sep",
    "depreciation_oct", "depreciation_nov", "depreciation_dec",
    "depreciation_jan", "depreciation_feb", "depreciation_mar",
]);

patch(AccountReportHeader.prototype, {
    get areMonthlyColumnsFolded() {
        return Boolean(this.controller.options.fa_register_months_folded);
    },

    toggleMonthlyColumns() {
        this.controller.options.fa_register_months_folded = !this.areMonthlyColumnsFolded;
    },

    isMonthlyDepreciation(column) {
        return MONTH_LABELS.has(column.expression_label);
    },
});

patch(AccountReportLine.prototype, {
    isMonthlyDepreciation(column) {
        return MONTH_LABELS.has(column.expression_label);
    },
});
