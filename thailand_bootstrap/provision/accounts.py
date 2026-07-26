import frappe

from thailand_bootstrap.config import chart_of_accounts


def company_abbr(company):
	return frappe.get_cached_value("Company", company, "abbr")


def expected_account_name(company, spec):
	return f"{spec['account_name']} - {company_abbr(company)}"


def _find_root_account(company, root_type):
	return frappe.db.get_value(
		"Account",
		{
			"company": company,
			"root_type": root_type,
			"is_group": 1,
			"parent_account": ["is", "not set"],
		},
		"name",
	)


def _find_or_create_parent_group(company, spec):
	abbr = company_abbr(company)
	for candidate in spec["parent_group_candidates"]:
		name = f"{candidate} - {abbr}"
		if frappe.db.exists("Account", name):
			return name, False

	default = spec["parent_group_default"]
	root_account = _find_root_account(company, default["root_type"])
	if not root_account:
		frappe.throw(
			f"Cannot provision Thai tax accounts for '{company}': no root {default['root_type']} "
			"group account found. Does this Company have a Chart of Accounts?"
		)

	group = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": default["account_name"],
			"company": company,
			"parent_account": root_account,
			"root_type": default["root_type"],
			"is_group": 1,
		}
	)
	group.flags.ignore_mandatory = True
	group.insert(ignore_permissions=True)
	return group.name, True


def ensure_account(company, spec):
	"""Idempotently ensure one account from the recipe exists for `company`.

	Returns (account_name, was_created).
	"""
	name = expected_account_name(company, spec)
	if frappe.db.exists("Account", name):
		return name, False

	parent_account, _ = _find_or_create_parent_group(company, spec)

	account = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": spec["account_name"],
			"company": company,
			"parent_account": parent_account,
			"root_type": spec["root_type"],
			"account_type": spec["account_type"],
			"is_group": 0,
			"tax_rate": spec.get("tax_rate"),
			"custom_thailand_bootstrap": 1,
		}
	)
	account.flags.ignore_mandatory = True
	account.insert(ignore_permissions=True)
	return account.name, True


def ensure_all(company):
	"""Ensure every account in the recipe exists for `company`.

	Returns (accounts: {key: account_name}, created: [account_name, ...]).
	"""
	accounts = {}
	created = []
	for spec in chart_of_accounts():
		name, was_created = ensure_account(company, spec)
		accounts[spec["key"]] = name
		if was_created:
			created.append(name)
	return accounts, created
