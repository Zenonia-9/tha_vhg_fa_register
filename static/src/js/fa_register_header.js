/** @odoo-module **/

import { AccountReportHeader } from "@account_reports/components/account_report/header/header";
import { AccountReportLine } from "@account_reports/components/account_report/line/line";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

const MONTH_LABELS = new Set([
    "depreciation_apr", "depreciation_may", "depreciation_jun",
    "depreciation_jul", "depreciation_aug", "depreciation_sep",
    "depreciation_oct", "depreciation_nov", "depreciation_dec",
    "depreciation_jan", "depreciation_feb", "depreciation_mar",
]);

patch(AccountReportFilters.prototype, {
    get thaDepartmentFilterName() {
        const selected = this.controller.cachedFilterOptions.tha_departments.filter(
            (department) => department.selected
        );
        return selected.length ? selected.map((department) => department.name).join(", ") : _t("All Departments");
    },

    thaSelectDepartment(department) {
        department.selected = !department.selected;
        this.applyFilters("tha_departments");
    },

    thaClearDepartments() {
        for (const department of this.controller.cachedFilterOptions.tha_departments) {
            department.selected = false;
        }
        this.applyFilters("tha_departments");
    },
});

patch(AccountReportHeader.prototype, {
    get areMonthlyColumnsFolded() {
        return Boolean(this.controller.options.fa_register_months_folded);
    },

    async toggleMonthlyColumns() {
        this.controller.options.fa_register_months_folded = !this.areMonthlyColumnsFolded;
        await this.controller.reload("fa_register_months_folded", this.controller.options);
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
