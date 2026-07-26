import frappe
from frappe.tests.utils import FrappeTestCase

from thailand_bootstrap import api
from thailand_bootstrap.tests.utils import make_thai_company


class TestIdempotency(FrappeTestCase):
	def test_repeated_provision_creates_no_duplicates(self):
		company = make_thai_company(country="Thailand")  # hook already ran once

		before = self._snapshot(company)

		second = api.provision(company)
		self.assertEqual(second["created"], [])

		third = api.provision(company)
		self.assertEqual(third["created"], [])

		after = self._snapshot(company)
		self.assertEqual(before, after)

	def _snapshot(self, company):
		return {
			"accounts": frappe.db.count("Account", {"company": company}),
			"sales_templates": frappe.db.count("Sales Taxes and Charges Template", {"company": company}),
			"purchase_templates": frappe.db.count(
				"Purchase Taxes and Charges Template", {"company": company}
			),
			"item_tax_templates": frappe.db.count("Item Tax Template", {"company": company}),
			"wht_type_accounts": frappe.db.count("Withholding Tax Type Account", {"company": company}),
			"thai_tax_settings_rows": frappe.db.count("Thai Tax Settings Company", {"company": company}),
		}
