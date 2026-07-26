import frappe

from thailand_bootstrap.config import tax_templates as tax_template_recipe
from thailand_bootstrap.provision.accounts import company_abbr


def expected_template_name(company, spec):
	return f"{spec['title']} - {company_abbr(company)}"


def _build_doc(company, spec, accounts):
	account = accounts[spec["account_key"]]
	doctype = spec["doctype"]

	if doctype == "Item Tax Template":
		taxes_row = {"tax_type": account, "tax_rate": spec["rate"]}
	else:
		taxes_row = {
			"charge_type": spec.get("charge_type", "On Net Total"),
			"account_head": account,
			"rate": spec["rate"],
			"description": spec["title"],
		}

	return frappe.get_doc(
		{
			"doctype": doctype,
			"title": spec["title"],
			"company": company,
			"taxes": [taxes_row],
			"custom_thailand_bootstrap": 1,
		}
	)


def ensure_template(company, spec, accounts):
	"""Idempotently ensure one tax template exists for `company`.

	Returns (name, was_created).
	"""
	name = expected_template_name(company, spec)
	if frappe.db.exists(spec["doctype"], name):
		return name, False

	doc = _build_doc(company, spec, accounts)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return doc.name, True


def ensure_all(company, accounts):
	"""Ensure every tax template in the recipe exists for `company`.

	Returns (names: [str], created: [str]).
	"""
	names = []
	created = []
	for spec in tax_template_recipe():
		name, was_created = ensure_template(company, spec, accounts)
		names.append(name)
		if was_created:
			created.append(name)
	return names, created
