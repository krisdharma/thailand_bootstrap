import frappe
from frappe.utils import random_string


def make_thai_company(country="Thailand", chart_of_accounts="Standard with Numbers"):
	"""Create a throwaway Company for tests. `country` is a parameter (not
	hardcoded to Thailand) so tests can prove the hook is inert for
	non-Thai companies (see test_provision.test_non_thai_company_is_untouched).
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
	item.item_group = "All Item Groups"
	item.stock_uom = "Nos"
	item.is_stock_item = is_stock_item
	item.insert(ignore_permissions=True)
	return item.name


def make_test_customer():
	suffix = random_string(6).upper()
	customer = frappe.new_doc("Customer")
	customer.customer_name = f"_Test Thai Customer {suffix}"
	customer.customer_group = "All Customer Groups"
	customer.territory = "All Territories"
	customer.insert(ignore_permissions=True)
	return customer.name
