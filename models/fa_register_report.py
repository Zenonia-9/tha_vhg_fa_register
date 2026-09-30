from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.tools import format_date


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def tha_vhg_attach_fa_register_management_menu(self):
        """Attach the register to an existing shared Management Reports root."""
        own_root = self.env.ref("tha_vhg_bs_ext.menu_vhg_management_reports")
        shared_root = self.search([
            ("id", "!=", own_root.id),
            ("name", "=", "Management Reports"),
            ("parent_id", "=", self.env.ref("account.menu_finance_configuration").id),
        ], order="id", limit=1)
        target_root = shared_root or own_root
        self.env.ref("tha_vhg_fa_register.menu_action_account_report_fa_register").parent_id = target_root


MONTH_EXPRESSION_LABELS = (
    "depreciation_apr", "depreciation_may", "depreciation_jun",
    "depreciation_jul", "depreciation_aug", "depreciation_sep",
    "depreciation_oct", "depreciation_nov", "depreciation_dec",
    "depreciation_jan", "depreciation_feb", "depreciation_mar",
)
COMPARE_LABELS = (
    ("cost_closing", "assets_date_to", "Total Amt (c/d)"),
    ("depreciation_closing", "depre_date_to", "Closing Accumulated Dep;"),
    ("net_book_value", "balance", "NBV"),
)


class FixedAssetRegisterReportHandler(models.AbstractModel):
    _name = "tha.vhg.fa.register.report.handler"
    _inherit = "account.asset.report.handler"
    _description = "Fixed Asset Register Report Handler"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options)

        options["assets_grouping_field"] = "asset_group_id"
        as_of_date = fields.Date.to_date(options["date"]["date_to"])
        fiscal_year_start = date(as_of_date.year if as_of_date.month >= 4 else as_of_date.year - 1, 4, 1)
        options["date"]["date_from"] = fields.Date.to_string(fiscal_year_start)
        options["date"]["date_to"] = fields.Date.to_string(as_of_date)
        options["date"]["currency_table_period_key"] = (
            f"{options['date']['date_from']}_{options['date']['date_to']}"
        )
        for column in options["columns"]:
            if column["expression_label"] == "net_book_value":
                column["name"] = _(
                    "NBV as at %(date)s",
                    date=format_date(self.env, as_of_date),
                )

        original_groups = options["column_groups"]
        primary_group_key = next(iter(original_groups))
        primary_group = original_groups[primary_group_key]
        primary_date = primary_group["forced_options"].setdefault("date", {})
        primary_date.update(options["date"])
        primary_date["currency_table_period_key"] = (
            f"{options['date']['date_from']}_{options['date']['date_to']}"
        )

        comparison_columns = []
        comparisons = []
        for group_key in list(original_groups)[1:]:
            group_date = original_groups[group_key]["forced_options"].get("date", {})
            comparison_date = group_date.get("date_to")
            if not comparison_date:
                continue
            comparisons.append(comparison_date)
            formatted_date = format_date(self.env, comparison_date)
            for target_label, _source_label, display_name in COMPARE_LABELS:
                expression_label = f"comparison_{target_label}_{len(comparisons)}"
                comparison_columns.append({
                    "name": f"{display_name} ({formatted_date})",
                    "column_group_key": primary_group_key,
                    "expression_label": expression_label,
                    "sortable": False,
                    "figure_type": "monetary",
                    "blank_if_zero": True,
                    "style": "text-align: center; white-space: nowrap;",
                })

        options["fa_register_comparison_dates"] = comparisons
        options["column_groups"] = {primary_group_key: primary_group}
        options["columns"] = [
            column for column in options["columns"]
            if column["column_group_key"] == primary_group_key
        ] + comparison_columns

        primary_headers = []
        for header_level in options.get("column_headers", []):
            filtered_level = []
            for header in header_level:
                header_date = header.get("forced_options", {}).get("date")
                if header_date and header_date.get("date_to") != fields.Date.to_string(as_of_date):
                    continue
                if header_date:
                    header["name"] = _("As of %(date)s", date=format_date(self.env, as_of_date))
                filtered_level.append(header)
            if filtered_level:
                primary_headers.append(filtered_level)
        options["column_headers"] = primary_headers

        monthly_start = 2 + 3 + 12 + 8 + 4 + 2
        monthly_count = len(MONTH_EXPRESSION_LABELS)
        column_sections = [
            (2, ""),
            (3, _("User")),
            (12, _("Characteristics")),
            (8, _("Assets")),
            (4, _("Useful Life")),
            (2, _("Depreciation")),
            (monthly_count, _("Monthly Depreciation")),
            (3, _("Depreciation")),
            (1, _("Book Value")),
            (1, _("Remark")),
        ]
        section_headers = []
        column_offset = 0
        for colspan, name in column_sections:
            if column_offset >= len(options["columns"]):
                break
            colspan = min(colspan, len(options["columns"]) - column_offset)
            header = {"name": name, "colspan": colspan}
            if column_offset == monthly_start:
                header["expression_label"] = MONTH_EXPRESSION_LABELS[0]
            section_headers.append(header)
            column_offset += colspan
        if column_offset < len(options["columns"]):
            section_headers.append({
                "name": _("Comparison"),
                "colspan": len(options["columns"]) - column_offset,
            })
        options["custom_columns_subheaders"] = section_headers
        options["custom_display_config"]["templates"].pop(
            "AccountReportFilters",
            None,
        )
        options["custom_display_config"]["templates"]["AccountReportHeader"] = (
            "tha_vhg_fa_register.FixedAssetRegisterHeader"
        )
        options["custom_display_config"]["templates"]["AccountReportLine"] = (
            "tha_vhg_fa_register.FixedAssetRegisterLine"
        )

    def _dynamic_lines_generator(
        self, report, options, all_column_groups_expression_totals, warnings=None
    ):
        date_to = fields.Date.to_date(options["date"]["date_to"])
        date_from = fields.Date.to_date(options["date"]["date_from"])
        year_lines = self._query_register_lines(options, date_from, date_to)
        if not year_lines:
            return []

        month_lines = {}
        for month_index in range(12):
            month_start = date_from + relativedelta(months=month_index)
            if month_start > date_to:
                continue
            month_end = month_start.replace(
                day=monthrange(month_start.year, month_start.month)[1]
            )
            month_lines[month_index] = self._query_register_lines(
                options, month_start, min(month_end, date_to)
            )

        comparison_data = []
        for comparison_date in options.get("fa_register_comparison_dates", []):
            comparison_as_of = fields.Date.to_date(comparison_date)
            comparison_start = date(
                comparison_as_of.year if comparison_as_of.month >= 4 else comparison_as_of.year - 1,
                4,
                1,
            )
            comparison_data.append(self._query_register_lines(
                options, comparison_start, comparison_as_of
            ))

        asset_ids = [asset_id for _account_id, asset_id, _group_id, _values in year_lines]
        assets = self.env["account.asset"].browse(asset_ids)
        assets_by_id = {asset.id: asset for asset in assets}
        month_values_by_asset = {
            month_index: {
                asset_id: values
                for _account_id, asset_id, _group_id, values in lines
            }
            for month_index, lines in month_lines.items()
        }
        comparison_values_by_asset = [
            {
                asset_id: values
                for _account_id, asset_id, _group_id, values in lines
            }
            for lines in comparison_data
        ]

        detail_lines = []
        for account_id, asset_id, asset_group_id, values in year_lines:
            asset = assets_by_id[asset_id]
            row_values = self._get_asset_column_values(
                asset,
                values,
                month_values_by_asset,
                comparison_values_by_asset,
                date_to,
            )
            columns = []
            for column in options["columns"]:
                value = row_values.get(column["expression_label"])
                columns.append(report._build_column_dict(
                    value,
                    column,
                    options=options,
                    currency=asset.currency_id if column.get("figure_type") == "monetary" else None,
                ))

            detail_lines.append({
                "id": report._get_generic_line_id("account.asset", asset_id),
                "name": "",
                "level": 1,
                "columns": columns,
                "unfoldable": False,
                "unfolded": False,
                "caret_options": "account_asset_line",
                "assets_account_id": account_id,
                "assets_asset_group_id": asset_group_id,
                "_is_asset_detail": True,
            })

        lines = self._group_register_lines(report, options, detail_lines)
        sequence = 0
        for line in lines:
            if line.pop("_is_asset_detail", False):
                sequence += 1
                line["name"] = str(sequence)

        if detail_lines:
            total_columns = []
            for column_index, column in enumerate(options["columns"]):
                if column.get("figure_type") != "monetary":
                    value = None
                else:
                    value = sum(
                        detail["columns"][column_index].get("no_format") or 0.0
                        for detail in detail_lines
                    )
                total_columns.append(report._build_column_dict(
                    value,
                    column,
                    options=options,
                ))
            lines.append({
                "id": report._get_generic_line_id(None, None, markup="total"),
                "level": 1,
                "name": _("Total"),
                "columns": total_columns,
                "unfoldable": False,
                "unfolded": False,
            })

        return [(0, line) for line in lines]

    def _query_register_lines(self, options, date_from, date_to):
        period_options = {
            **options,
            "date": {
                **options["date"],
                "date_from": fields.Date.to_string(date_from),
                "date_to": fields.Date.to_string(date_to),
            },
        }
        return super()._query_lines(period_options)

    def _get_asset_column_values(
        self, asset, values, month_values, comparison_values, as_of_date
    ):
        def optional_field_value(field_name):
            if field_name not in asset._fields:
                return None
            value = asset[field_name]
            return None if value is False else value

        method_period = int(asset.method_period or "1")
        total_life_months = asset.method_number * method_period
        monthly_depreciation = 0.0
        related_assets = asset | asset.children_ids
        remaining_months = 0
        for related_asset in related_assets:
            related_period_months = int(related_asset.method_period or "1")
            future_moves = related_asset.depreciation_move_ids.filtered(
                lambda move: move.date
                and move.date > as_of_date
                and move.state != "cancel"
                and move.asset_number_days is not False
            ).sorted("date")
            remaining_months += len(future_moves) * related_period_months
            if future_moves:
                monthly_depreciation += (
                    future_moves[0].depreciation_value
                    / related_period_months
                )

        row_values = {
            "acquisition_date": asset.acquisition_date or None,
            "asset_code": optional_field_value("x_studio_asset_code"),
            "department": ", ".join(asset.department_info.mapped("name"))
            if "department_info" in asset._fields else None,
            "unit": optional_field_value("x_studio_unit"),
            "location": optional_field_value("x_studio_location"),
            "vendor_name": optional_field_value("x_studio_vendor_name"),
            "contact": optional_field_value("x_studio_contact"),
            "item_name": asset.name,
            "brand_name": optional_field_value("x_studio_brand_name"),
            "model_no": optional_field_value("x_studio_model_no"),
            "serial_no": optional_field_value("x_studio_serial_no"),
            "size": optional_field_value("x_studio_size"),
            "color": optional_field_value("x_studio_color"),
            "quantity": optional_field_value("x_studio_quantity"),
            "remark": None,
            "prorata_date": asset.prorata_date or None,
            "gl_code": asset.account_asset_id.code or None,
            "asset_category": asset.asset_group_id.name or None,
            "cost_opening": values.get("assets_date_from"),
            "purchase": values.get("assets_plus"),
            "movement_date": None,
            "transfer": None,
            "write_off": None,
            "disposal": values.get("assets_minus"),
            "cost_closing": values.get("assets_date_to"),
            "life_total_years": total_life_months / 12.0 if total_life_months else 0.0,
            "life_total_months": total_life_months,
            "life_remaining_years": remaining_months / 12.0,
            "life_remaining_months": remaining_months,
            "depreciation_per_month": monthly_depreciation,
            "depreciation_opening": values.get("depre_date_from"),
            "depreciation_total": values.get("depre_plus"),
            "depreciation_adjustments": values.get("depre_minus"),
            "depreciation_closing": values.get("depre_date_to"),
            "net_book_value": values.get("balance"),
            "remark_end": None,
        }

        for month_index, asset_values_by_id in month_values.items():
            expression_label = MONTH_EXPRESSION_LABELS[month_index]
            month_asset_values = asset_values_by_id.get(asset.id)
            row_values[expression_label] = (
                month_asset_values.get("depre_plus")
                if month_asset_values else None
            )

        for comparison_index, values_by_asset in enumerate(comparison_values, start=1):
            comparison_asset_values = values_by_asset.get(asset.id, {})
            for target_label, source_label, _display_name in COMPARE_LABELS:
                row_values[f"comparison_{target_label}_{comparison_index}"] = (
                    comparison_asset_values.get(source_label)
                )
        return row_values

    def _group_register_lines(self, report, options, detail_lines):
        grouping_field = options.get("assets_grouping_field", "none")
        if grouping_field == "none":
            return detail_lines

        model = "account.account" if grouping_field == "account_id" else "account.asset.group"
        group_values = {}
        for line in detail_lines:
            group_id = line.get(
                "assets_account_id" if grouping_field == "account_id"
                else "assets_asset_group_id"
            )
            group_values.setdefault(group_id, []).append(line)

        group_records = self.env[model].browse(
            [group_id for group_id in group_values if group_id]
        )
        records_by_id = {record.id: record for record in group_records}
        result = []
        unfolded_ids = set(options.get("unfolded_lines", []))
        for group_record_id, children in group_values.items():
            group_record = records_by_id.get(group_record_id)
            group_line_id = (
                report._get_generic_line_id(model, group_record.id)
                if group_record
                else report._get_generic_line_id(None, None, markup="no_asset_group")
            )
            is_unfolded = options.get("unfold_all") or group_line_id in unfolded_ids
            if not group_record:
                name = _("No Asset Group")
            elif grouping_field == "account_id":
                name = f"{group_record.code} {group_record.name}"
            else:
                name = group_record.name
            group_columns = []
            for column_index, column in enumerate(options["columns"]):
                if column.get("figure_type") != "monetary":
                    value = None
                else:
                    value = sum(
                        child["columns"][column_index].get("no_format") or 0.0
                        for child in children
                    )
                group_columns.append(report._build_column_dict(
                    value,
                    column,
                    options=options,
                ))

            result.append({
                "id": group_line_id,
                "name": name,
                "level": 1,
                "columns": group_columns,
                "unfoldable": True,
                "unfolded": is_unfolded,
            })
            for child in children:
                child["id"] = report._get_generic_line_id(
                    "account.asset",
                    report._get_res_id_from_line_id(child["id"], "account.asset"),
                    parent_line_id=group_line_id,
                )
                child["parent_id"] = group_line_id
                child["level"] = 2
                result.append(child)

        return result
