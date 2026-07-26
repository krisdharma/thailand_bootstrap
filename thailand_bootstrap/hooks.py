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

doc_events = {
    "Company": {
        "after_insert": "thailand_bootstrap.api.on_company_created",
    }
}
