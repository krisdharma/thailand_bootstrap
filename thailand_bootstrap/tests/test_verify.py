import frappe
from frappe.tests.utils import FrappeTestCase

from thailand_bootstrap import api
from thailand_bootstrap.tests.utils import make_thai_company


class TestVerify(FrappeTestCase):
	def test_verify_passes_after_provisioning(self):
		company = make_thai_company(country="Thailand")
		report = api.verify(company)
		self.assertTrue(report["ok"], report)
		self.assertEqual(report["checks"], [c for c in report["checks"] if c["ok"]])

	def test_verify_catches_a_deleted_wht_account_row(self):
		company = make_thai_company(country="Thailand")
		self.assertTrue(api.verify(company)["ok"])

		row_name = frappe.db.get_value(
			"Withholding Tax Type Account",
			{"company": company, "parent": "WHT 3% (Pay)"},
			"name",
		)
		frappe.delete_doc("Withholding Tax Type Account", row_name, ignore_permissions=True, force=True)

		report = api.verify(company)
		self.assertFalse(report["ok"])
		failed = [c["name"] for c in report["checks"] if not c["ok"]]
		self.assertIn("wht:WHT 3% (Pay)", failed)

	def test_verify_catches_a_repointed_template(self):
		company = make_thai_company(country="Thailand")
		self.assertTrue(api.verify(company)["ok"])

		abbr = frappe.get_cached_value("Company", company, "abbr")
		template_name = f"VAT 7% - Product (Output) - {abbr}"
		frappe.delete_doc(
			"Sales Taxes and Charges Template", template_name, ignore_permissions=True, force=True
		)

		report = api.verify(company)
		self.assertFalse(report["ok"])
		failed = [c["name"] for c in report["checks"] if not c["ok"]]
		self.assertIn("template:VAT 7% - Product (Output)", failed)

	def test_verify_warns_but_does_not_fail_without_company_address(self):
		company = make_thai_company(country="Thailand")
		report = api.verify(company)
		self.assertTrue(report["ok"])
		self.assertTrue(any("Billing Address" in w for w in report["warnings"]))
