import frappe

from thailand_bootstrap.config import chart_of_accounts, tax_templates, withholding_tax_types
from thailand_bootstrap.provision.accounts import expected_account_name
from thailand_bootstrap.provision.tax_templates import expected_template_name


def _check(checks, name, ok, detail=""):
	checks.append({"name": name, "ok": bool(ok), "detail": detail})


def verify(company):
	"""Read-only verification that `company` is fully Thai-tax-ready.

	Returns {"company": ..., "ok": bool, "checks": [...], "warnings": [...]}.
	"""
	checks = []
	warnings = []

	account_names = {}
	for spec in chart_of_accounts():
		name = expected_account_name(company, spec)
		exists = frappe.db.exists("Account", name)
		_check(checks, f"account:{spec['key']}", exists, name)
		if exists:
			account_names[spec["key"]] = name

	for spec in tax_templates():
		name = expected_template_name(company, spec)
		_check(checks, f"template:{spec['title']}", frappe.db.exists(spec["doctype"], name), name)

	for spec in withholding_tax_types():
		title = spec["title"]
		has_row = frappe.db.exists(
			"Withholding Tax Type Account",
			{"parent": title, "parenttype": "Withholding Tax Type", "company": company},
		)
		_check(checks, f"wht:{title}", has_row, title)

	settings_row_exists = frappe.db.exists("Thai Tax Settings Company", {"company": company})
	_check(checks, "thai_tax_settings_row", settings_row_exists, company)

	resolves = False
	resolve_detail = ""
	try:
		from erpnext_thailand.custom.custom_api import get_thai_tax_settings

		get_thai_tax_settings(company)
		resolves = True
	except Exception as e:
		resolve_detail = str(e)
	_check(checks, "get_thai_tax_settings_resolves", resolves, resolve_detail)

	has_address = frappe.db.exists(
		"Dynamic Link",
		{
			"link_doctype": "Company",
			"link_name": company,
			"parenttype": "Address",
		},
	)
	if not has_address:
		warnings.append(
			f"No Company Billing Address exists for '{company}' yet. This is expected — "
			"Thailand Bootstrap deliberately does not create it, since a real Address "
			"is genuinely company-specific data, not VAT/WHT configuration. Tax Invoice "
			"generation will fail until one is added with is_your_company_address=1."
		)

	ok = all(c["ok"] for c in checks)
	return {"company": company, "ok": ok, "checks": checks, "warnings": warnings}
