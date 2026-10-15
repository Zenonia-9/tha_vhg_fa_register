# VHG Fixed Asset Register

This addon adds a native Odoo 19 accounting report based on the `FA Register Detail` workbook. It leaves the standard Depreciation Schedule unchanged.

Open it from **Accounting → Reporting → Other Reports → Fixed Asset Register**.

## Report behavior

- The report uses an as-of date. The date range starts on 1 April of the fiscal year containing the selected end date.
- The Apr–Mar depreciation columns show posted depreciation for months up to the selected date; later months are blank.
- Odoo's native comparison selector adds only comparative closing gross cost, accumulated depreciation, and net book value columns.
- Assets are grouped by Asset Group (not account), with assets lacking a group under **No Asset Group**. Search, unfolding, opening an asset, and PDF/XLSX export use the account-report interface.
- **All Departments**, beside All Journals, filters by the asset's current Department (the same source as the Dept column). Select one or more departments; an asset matching any selected department is included once. Click **All Departments** to clear the selection, including assets without a department. The selection persists through report reloads and applies to group/subclass totals, expanded assets, monthly depreciation, comparisons, and PDF/XLSX exports. The dropdown opens even when no departments exist and displays **No departments configured.**
- The report's first column is the generated `Sr No.` line label; workbook row 4 (the source column indices) is omitted.

## Field and value sources

The descriptive columns use native asset fields and the Studio fields already registered on `account.asset`. Department uses `department_info` when populated; otherwise it uses the asset's analytic distribution accounts in the **Department** analytic plan (including child plans). Other analytic plans are excluded from this fallback. The filter offers both explicit departments and Department analytic accounts; their model and ID are kept separate. The asset group's name is used for Asset Category, and the fixed asset account code is used for GL Code.

Opening/closing asset cost, additions, accumulated depreciation, disposal reductions, and net book value use Odoo's existing asset-report handler calculations. Monthly depreciation uses the same handler for each month. Useful life is derived from the asset's configured number of depreciation periods and period length.

False or unset descriptive values are rendered blank. Column V (Date) shows the asset's latest transfer date when recorded by `tha_asset_department_transfer`. Columns W (Transfer), X (Write Off), P (Remark), and AW (Remark) remain present with blank values until a data source is provided. The current asset/depreciation data has no reliable classification for transfer amounts and write-off events. The native asset report's disposal and depreciation reduction values populate Disposal and the accumulated-depreciation adjustment column.
