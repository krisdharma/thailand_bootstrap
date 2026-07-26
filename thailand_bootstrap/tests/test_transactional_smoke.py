"""Exercises erpnext_thailand's own engine against accounts this module
provisioned — the exact gap the architecture review flagged as unverified
in the previous (Thailand Template Co clone-and-rename) design: nobody had
ever actually posted a real transaction against config produced by that
mechanism. This proves get_thai_tax_settings() resolves for a company
this module provisioned, and that the GL Entry -> Sales Tax Invoice
auto-creation hook in erpnext_thailand/custom/custom_api.py accepts our
Output VAT account.

Scope note: only the Product/due-VAT path (Sales Invoice -> GL Entry ->
Sales Tax Invoice) is covered here. The Service/Undue path (Payment Entry
undue-clearing) and Withholding Tax deduction-on-payment are deliberately
left for a follow-up test once this has been run against a real bench —
writing that against Payment Entry's deduction-row schema without being
able to execute and inspect it here would be exactly the kind of
unverified assumption this module was built to eliminate.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from thailand_bootstrap import api
from thailand_bootstrap.tests.utils import make_test_customer, make_test_item, make_thai_company


class TestTransactionalSmoke(FrappeTestCase):
	def test_product_sales_invoice_posts_output_vat_and_creates_tax_invoice(self):
		company = make_thai_company(country="Thailand")
		self.assertTrue(api.verify(company)["ok"])

		accounts = self._account_names(company)

		income_account = frappe.db.get_value(
			"Account", {"company": company, "root_type": "Income", "is_group": 0}, "name"
		)
		self.assertTrue(income_account, "Standard CoA template should have created a default Income account")

		item = make_test_item(is_stock_item=0)
		customer = make_test_customer()

		si = frappe.new_doc("Sales Invoice")
		si.customer = customer
		si.company = company
		si.posting_date = today()
		si.due_date = today()
		si.append(
			"items",
			{
				"item_code": item,
				"qty": 1,
				"rate": 1000,
				"income_account": income_account,
			},
		)
		si.append(
			"taxes",
			{
				"charge_type": "On Net Total",
				"account_head": accounts["sales_tax_account"],
				"rate": 7,
				"description": "VAT 7%",
			},
		)
		si.insert(ignore_permissions=True)
		si.submit()

		gl_hit = frappe.db.exists(
			"GL Entry",
			{
				"voucher_type": "Sales Invoice",
				"voucher_no": si.name,
				"account": accounts["sales_tax_account"],
			},
		)
		self.assertTrue(gl_hit, "Expected a GL Entry against the Output VAT account for this invoice")

		tax_invoice = frappe.db.exists(
			"Sales Tax Invoice",
			{"voucher_type": "Sales Invoice", "voucher_no": si.name},
		)
		self.assertTrue(
			tax_invoice,
			"erpnext_thailand should have auto-created a Sales Tax Invoice for this GL Entry",
		)

	def _account_names(self, company):
		from thailand_bootstrap.config import chart_of_accounts
		from thailand_bootstrap.provision.accounts import expected_account_name

		return {
			spec["key"]: expected_account_name(company, spec) for spec in chart_of_accounts()
		}
