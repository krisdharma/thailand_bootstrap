import frappe
from frappe.tests.utils import FrappeTestCase

from thailand_bootstrap import api
from thailand_bootstrap.config import chart_of_accounts, tax_templates, withholding_tax_types
from thailand_bootstrap.tests.utils import make_thai_company


class TestProvision(FrappeTestCase):
	def test_new_thai_company_is_auto_provisioned(self):
		"""Company.after_insert should have already provisioned everything
		by the time make_thai_company() returns — no manual call needed.
		"""
		company = make_thai_company(country="Thailand")
		report = api.verify(company)
		self.assertTrue(report["ok"], report)

	def test_non_thai_company_is_untouched(self):
		company = make_thai_company(country="United States")
		report = api.verify(company)
		self.assertFalse(report["ok"])
		account_checks = [c for c in report["checks"] if c["name"].startswith("account:")]
		self.assertTrue(all(not c["ok"] for c in account_checks))

	def test_manual_provision_from_scratch_creates_every_recipe_item(self):
		# Created as a non-Thai company so the after_insert hook is a no-op —
		# this isolates the manual provision() path from the automatic one.
		company = make_thai_company(country="United States")
		frappe.db.set_value("Company", company, "country", "Thailand")

		result = api.provision(company)

		self.assertEqual(result["errors"], [])
		self.assertTrue(result["verification"]["ok"], result["verification"])

		expected_created_count = (
			len(chart_of_accounts())
			+ 1  # Thai Tax Settings row
			+ len(tax_templates())
			+ len(withholding_tax_types())  # each contributes a new global type or company row
		)
		self.assertEqual(len(result["created"]), expected_created_count)

		for spec in chart_of_accounts():
			self.assertTrue(
				frappe.db.exists("Account", {"account_name": spec["account_name"], "company": company})
			)

		for spec in tax_templates():
			self.assertTrue(
				frappe.db.exists(spec["doctype"], {"title": spec["title"], "company": company})
			)

		for spec in withholding_tax_types():
			self.assertTrue(
				frappe.db.exists(
					"Withholding Tax Type Account",
					{"parent": spec["title"], "company": company},
				)
			)

		self.assertTrue(frappe.db.exists("Thai Tax Settings Company", {"company": company}))
