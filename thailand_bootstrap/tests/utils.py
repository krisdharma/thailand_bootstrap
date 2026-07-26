import frappe
from frappe.utils import random_string

# These are normally created by the Setup Wizard's install-fixtures step.
# A site created via `bench new-site` + `install-app` (as any CI/test site
# is) never runs that step, so they don't exist yet — ensure them here
# rather than assuming a Setup-Wizard-completed site, so this suite is
# self-contained and safe to run against any fresh site.
# (doctype, name, the field its autoname is keyed off — None means the
# bare `name` is used directly, e.g. Warehouse Type's autoname is "Prompt")
_PREREQUISITES = (
	("Warehouse Type", "Transit", None, {}),
	("Item Group", "All Item Groups", "item_group_name", {"is_group": 1}),
	("UOM", "Nos", "uom_name", {}),
	("Customer Group", "All Customer Groups", "customer_group_name", {"is_group": 1}),
	("Territory", "All Territories", "territory_name", {"is_group": 1}),
)


def _ensure_global_prerequisites():
	for doctype, name, name_field, extra_fields in _PREREQUISITES:
		if frappe.db.exists(doctype, name):
			continue
		fields = {"doctype": doctype, **extra_fields}
		fields[name_field if name_field else "name"] = name
		doc = frappe.get_doc(fields)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)


def make_thai_company(country="Thailand", chart_of_accounts="Standard with Numbers"):
	"""Create a throwaway Company for tests. `country` is a parameter (not
	hardcoded to Thailand) so tests can prove the hook is inert for
	non-Thai companies (see test_provision.test_non_thai_company_is_untouched).
	"""
	_ensure_global_prerequisites()
	suffix = random_string(6).upper()
	company = frappe.new_doc("Company")
	company.company_name = f"_Test Thai Co {suffix}"
	company.abbr = f"TT{suffix[:3]}"
	company.default_currency = "THB"
	company.country = country
	company.chart_of_accounts = chart_of_accounts
	company.insert(ignore_permissions=True)
	return company.name


def make_test_item(is_stock_item=0):
	_ensure_global_prerequisites()
	suffix = random_string(6).upper()
	item = frappe.new_doc("Item")
	item.item_code = f"_Test Thai Item {suffix}"
	item.item_group = "All Item Groups"
	item.stock_uom = "Nos"
	item.is_stock_item = is_stock_item
	item.insert(ignore_permissions=True)
	return item.name


def make_test_customer():
	_ensure_global_prerequisites()
	suffix = random_string(6).upper()
	customer = frappe.new_doc("Customer")
	customer.customer_name = f"_Test Thai Customer {suffix}"
	customer.customer_group = "All Customer Groups"
	customer.territory = "All Territories"
	customer.insert(ignore_permissions=True)
	return customer.name
