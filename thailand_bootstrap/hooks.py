from . import __version__ as app_version

app_name = "thailand_bootstrap"
app_title = "Thailand Bootstrap"
app_publisher = "Kris Dharma"
app_description = (
    "Automatically provisions Thai VAT/WHT chart of accounts, Thai Tax Settings, "
    "tax templates, and Withholding Tax Types for any Company with country=Thailand. "
    "Depends on erpnext_thailand; does not modify it."
)
app_email = "mr.krisdharma@gmail.com"
app_license = "MIT"
required_apps = ["erpnext", "erpnext_thailand"]

after_install = "thailand_bootstrap.install.after_install"

# Runs once before this app's test suite (frappe.testing.environment, the
# same hook frappe's own frappe.utils.install:before_tests uses) -- see
# thailand_bootstrap/tests/setup.py for what it does and why.
before_tests = "thailand_bootstrap.tests.setup.before_tests"

doc_events = {
    "Company": {
        # Deliberately on_update, not after_insert: ERPNext's own Company.on_update
        # (erpnext/setup/doctype/company/company.py) is what actually creates the
        # Chart of Accounts, and Document.hook()'s composer always runs the
        # controller's own on_update before this app's registered handler. Wiring
        # this to after_insert instead would fire before any accounts exist at
        # all, and every account-creation step would fail every time.
        "on_update": "thailand_bootstrap.api.on_company_created",
    }
}
