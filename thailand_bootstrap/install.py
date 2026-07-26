import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

TAGGED_DOCTYPES = [
	"Account",
	"Sales Taxes and Charges Template",
	"Purchase Taxes and Charges Template",
	"Item Tax Template",
	"Withholding Tax Type Account",
	"Thai Tax Settings Company",
]

CUSTOM_FIELDS = {
	doctype: [
		{
			"fieldname": "custom_thailand_bootstrap",
			"fieldtype": "Check",
			"label": "Created by Thailand Bootstrap",
			"read_only": 1,
			"default": "0",
			"no_copy": 1,
			"print_hide": 1,
		}
	]
	for doctype in TAGGED_DOCTYPES
}


def after_install():
	try:
		click.secho("Setting up Thailand Bootstrap...", fg="green")
		create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
		click.secho("Thailand Bootstrap ready — new Companies with country=Thailand will be auto-provisioned.", fg="green")
	except Exception as e:
		BUG_REPORT_URL = "https://github.com/krisdharma/thailand_bootstrap/issues/new"
		click.secho(
			"Thailand Bootstrap installation failed."
			f" Please retry `bench install-app thailand_bootstrap` or file an issue at {BUG_REPORT_URL}.",
			fg="bright_red",
		)
		raise e
