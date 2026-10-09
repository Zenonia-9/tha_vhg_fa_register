{
    "name": "VHG Fixed Asset Register",
    "summary": "Native accounting report matching the Victoria Hospital fixed asset register.",
        "version": "19.0.1.0.10",
    "category": "Accounting/Accounting",
    "author": "Thein Htoo Aung",
    "license": "LGPL-3",
    "depends": [
        "account_asset",
        "account_reports",
        "tha_vhg_bs_ext",
        "tha_vhg_asset_subclass",
        "tha_asset_department_transfer",
        "tha_vhg_daily_cash_register",
    ],
    "data": [
        "data/fa_register_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tha_vhg_fa_register/static/src/xml/fa_register_header.xml",
            "tha_vhg_fa_register/static/src/js/fa_register_header.js",
            "tha_vhg_fa_register/static/src/scss/fa_register_header.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
