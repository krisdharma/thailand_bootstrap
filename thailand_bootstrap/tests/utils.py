import frappe
from frappe.utils import random_string


def make_thai_company(country="Thailand", chart_of_accounts="Standard with Numbers"):
	"""Create a throwaway Company for tests. `country` is a parameter (not
	hardcoded to Thailand) so tests can prove the hook is inert for
	non-Thai companies (see test_provision.test_non_thai_company_is_untouched).
	Global fixtures (Item Group, Territory, Customer Group, UOM, ...) are
	assumed to already exist -- see tests/setup.py's before_tests hook.
	"""
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
	suffix = random_string(6).upper()
	item = frappe.new_doc("Item")
	item.item_code = f"_Test Thai Item {suffix}"
	item.item_group = "Services"
	item.stock_uom = "Nos"
	item.is_stock_item = is_stock_item
	item.insert(ignore_permissions=True)
	return item.name


def make_company_address(company):
	"""erpnext_thailand hard-throws creating a Sales/Purchase Tax Invoice
	without a Company Billing/Tax Address (custom_api.py::
	update_company_tax_address) -- not just a soft default-fill, as
	validate_company_address on Payment Entry alone suggested. Needed by
	any real company before its first transaction, so the transactional
	smoke test needs it too. This is real, per-company setup, not a
	fixture gap -- unlike everything in tests/setup.py.
	"""
	address = frappe.new_doc("Address")
	address.address_title = company
	address.address_type = "Billing"
	address.address_line1 = "1 Test Street"
	address.city = "Bangkok"
	address.country = "Thailand"
	address.is_your_company_address = 1
	address.append("links", {"link_doctype": "Company", "link_name": company})
	address.insert(ignore_permissions=True)
	return address.name


def make_test_customer():
	"""Individual/Thailand are real Setup Wizard defaults (erpnext's
	get_preset_records: Customer Group leaves are Individual/Commercial/Non
	Profit/Government; the country-named Territory leaf is the install
	country itself) -- not test-only inventions.
	"""
	suffix = random_string(6).upper()
	customer = frappe.new_doc("Customer")
	customer.customer_name = f"_Test Thai Customer {suffix}"
	customer.customer_group = "Individual"
	customer.territory = "Thailand"
	customer.insert(ignore_permissions=True)
	return customer.name
