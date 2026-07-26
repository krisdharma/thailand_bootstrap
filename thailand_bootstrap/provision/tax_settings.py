import frappe

VAT_FIELDS = (
	"sales_tax_account",
	"sales_tax_account_undue",
	"purchase_tax_account",
	"purchase_tax_account_undue",
)


def ensure(company, accounts, force=False):
	"""Idempotently ensure `company` has a row in Thai Tax Settings pointing at
	the 4 VAT accounts. Returns (was_created, was_updated).
	"""
	settings = frappe.get_single("Thai Tax Settings")
	row = next((r for r in settings.company_accounts if r.company == company), None)

	was_created = False
	if row is None:
		row = settings.append("company_accounts", {"company": company})
		was_created = True

	was_updated = False
	for field in VAT_FIELDS:
		target = accounts[field]
		if row.get(field) != target:
			if was_created or force:
				row.set(field, target)
				was_updated = True

	if was_created or was_updated:
		row.custom_thailand_bootstrap = 1
		settings.save(ignore_permissions=True)

	return was_created, was_updated
