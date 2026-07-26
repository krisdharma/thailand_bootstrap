import frappe

from thailand_bootstrap.config import withholding_tax_types as wht_recipe

DOCTYPE = "Withholding Tax Type"


def ensure_type(company, spec, accounts):
	"""Idempotently ensure one Withholding Tax Type exists, with a company
	account row for `company`. Withholding Tax Type is a *global* doctype
	(title is unique across the whole site, not per company) — the correct
	per-company element is a row in its own `accounts` child table, mirroring
	how Thai Tax Settings itself is structured. Returns (name, was_created,
	was_updated).
	"""
	title = spec["title"]
	account = accounts[spec["account_key"]]

	if not frappe.db.exists(DOCTYPE, title):
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE,
				"title": title,
				"percent": spec["percent"],
				"for_payment_type": spec["for_payment_type"],
				"accounts": [
					{
						"company": company,
						"account": account,
						"custom_thailand_bootstrap": 1,
					}
				],
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		return doc.name, True, False

	doc = frappe.get_doc(DOCTYPE, title)
	row = next((r for r in doc.accounts if r.company == company), None)
	if row is not None:
		return doc.name, False, False

	row = doc.append("accounts", {"company": company, "account": account})
	row.custom_thailand_bootstrap = 1
	doc.save(ignore_permissions=True)
	return doc.name, False, True


def ensure_all(company, accounts):
	"""Ensure every WHT Type in the recipe has a company row for `company`.

	Returns (names: [str], created_types: [str], added_company_rows: [str]).
	"""
	names = []
	created_types = []
	added_company_rows = []
	for spec in wht_recipe():
		name, was_created, was_updated = ensure_type(company, spec, accounts)
		names.append(name)
		if was_created:
			created_types.append(name)
		elif was_updated:
			added_company_rows.append(name)
	return names, created_types, added_company_rows
