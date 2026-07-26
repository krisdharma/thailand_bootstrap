import frappe

from thailand_bootstrap.provision import accounts, tax_settings, tax_templates, withholding_tax
from thailand_bootstrap.verify import verify as _verify

TRIGGER_COUNTRY = "Thailand"


@frappe.whitelist()
def provision(company, force=False):
	"""Idempotently provision every Thai VAT/WHT configuration item for
	`company`: 6 accounts, the Thai Tax Settings row, tax templates, and the
	8 Withholding Tax Types (as company rows on the shared global records).

	Safe to call repeatedly — only creates what's missing. With
	`force=True`, also repairs Thai Tax Settings account references that
	drifted from the recipe (accounts/templates/WHT types themselves are
	never mutated once created, only created-if-missing).

	Returns a structured result dict; never raises to a hook caller (see
	on_company_created) but does raise to a direct/manual caller so a
	`bench execute` invocation surfaces the real error.
	"""
	force = frappe.utils.cint(force)
	result = {
		"company": company,
		"created": [],
		"already_present": [],
		"errors": [],
	}

	try:
		account_names, created_accounts = accounts.ensure_all(company)
		result["created"].extend(created_accounts)
		result["already_present"].extend(
			name for name in account_names.values() if name not in created_accounts
		)

		settings_created, settings_updated = tax_settings.ensure(company, account_names, force=force)
		if settings_created:
			result["created"].append("Thai Tax Settings row")
		elif settings_updated:
			result["created"].append("Thai Tax Settings row (repaired)")
		else:
			result["already_present"].append("Thai Tax Settings row")

		template_names, created_templates = tax_templates.ensure_all(company, account_names)
		result["created"].extend(created_templates)
		result["already_present"].extend(
			name for name in template_names if name not in created_templates
		)

		wht_names, created_wht_types, added_wht_rows = withholding_tax.ensure_all(company, account_names)
		result["created"].extend(created_wht_types)
		result["created"].extend(f"{name} (company row)" for name in added_wht_rows)
		result["already_present"].extend(
			name for name in wht_names if name not in created_wht_types and name not in added_wht_rows
		)

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(
			title=f"Thailand Bootstrap: provisioning failed for {company}",
			message=frappe.get_traceback(),
		)
		result["errors"].append(str(e))
		raise

	result["verification"] = _verify(company)
	return result


@frappe.whitelist()
def verify(company):
	"""Read-only. See thailand_bootstrap.verify.verify for the report shape."""
	return _verify(company)


@frappe.whitelist()
def is_thailand_ready(company):
	return _verify(company)["ok"]


@frappe.whitelist()
def deprovision(company, confirm=False):
	"""Explicit, rarely-used teardown. Only for a company that never had
	real transactions post against the accounts this module created — hard
	refuses otherwise. Deletes only documents this module tagged
	(custom_thailand_bootstrap=1), never anything else.
	"""
	if not frappe.utils.cint(confirm):
		frappe.throw("deprovision() requires confirm=True — this is a destructive, rarely-used operation.")

	tagged_accounts = frappe.get_all(
		"Account",
		filters={"company": company, "custom_thailand_bootstrap": 1},
		pluck="name",
	)
	for account in tagged_accounts:
		gl_count = frappe.db.count("GL Entry", {"account": account})
		if gl_count:
			frappe.throw(
				f"Refusing to deprovision '{company}': account '{account}' has {gl_count} "
				"GL Entries against it. This company has real transactions and can no "
				"longer be safely torn down."
			)

	deleted = []
	for doctype, filters in (
		("Withholding Tax Type Account", {"company": company, "custom_thailand_bootstrap": 1}),
		("Sales Taxes and Charges Template", {"company": company, "custom_thailand_bootstrap": 1}),
		("Purchase Taxes and Charges Template", {"company": company, "custom_thailand_bootstrap": 1}),
		("Item Tax Template", {"company": company, "custom_thailand_bootstrap": 1}),
	):
		for name in frappe.get_all(doctype, filters=filters, pluck="name"):
			frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
			deleted.append(f"{doctype}: {name}")

	settings = frappe.get_single("Thai Tax Settings")
	row = next((r for r in settings.company_accounts if r.company == company), None)
	if row is not None:
		settings.company_accounts.remove(row)
		settings.save(ignore_permissions=True)
		deleted.append("Thai Tax Settings row")

	for account in tagged_accounts:
		frappe.delete_doc("Account", account, ignore_permissions=True)
		deleted.append(f"Account: {account}")

	return {"company": company, "deleted": deleted}


def on_company_created(doc, method=None):
	"""Company.after_insert hook. Deliberately never raises — Company
	creation itself must never fail because of this module. A company left
	not-yet-provisioned (e.g. because provisioning threw) is truthfully
	reported as such by verify()/is_thailand_ready(), and can be finished
	later with `provision(company, force=True)`.
	"""
	if doc.country != TRIGGER_COUNTRY:
		return

	try:
		provision(doc.name)
	except Exception:
		# provision() already rolled back its own changes and logged the
		# underlying error (see its own except-block) — just swallow it
		# here so Company creation itself always succeeds.
		pass
