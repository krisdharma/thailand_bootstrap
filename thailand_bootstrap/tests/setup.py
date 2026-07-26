"""One-time test-environment bootstrap.

A site created via `bench new-site` + `install-app` never runs the Setup
Wizard, so it's missing every fixture the Wizard normally creates (Item
Group, Territory, Customer Group, UOM, Warehouse Type, Address Template,
Price Lists, Fiscal Year, Global Defaults, ...). Rather than this app
hand-reconstructing pieces of that fixture set itself -- which is not
this app's job and would need re-discovering again on every ERPNext
upgrade -- this calls the same officially supported, whitelisted entry
point a human completing the Setup Wizard UI calls:
`frappe.desk.page.setup_wizard.setup_wizard.setup_complete`. That is
frappe core's own pattern for exactly this situation: frappe's own
`frappe.utils.install.before_tests` does the same thing for its bare
test suite (it just omits the erpnext-specific keys below, since plain
frappe has no Company/Chart of Accounts stage to run).

Registered via hooks.py's `before_tests`, which `frappe.testing.environment`
runs exactly once before this app's test suite -- not once per test.
`setup_complete()` is also idempotent on its own (`frappe.is_setup_complete()`
short-circuits it), so re-running `bench run-tests` against an
already-set-up site is safe.

Verified against erpnext 16.29.0 by reading
erpnext/setup/setup_wizard/setup_wizard.py and
erpnext/setup/setup_wizard/operations/install_fixtures.py directly:
- install_company() requires company_name, company_abbr, currency,
  country, chart_of_accounts, fy_start_date, fy_end_date.
- install_defaults() additionally uses currency/company_name/country for
  Global Defaults, and creates "Standard Selling"/"Standard Buying" Price
  Lists in `currency`.
- create_or_update_user() (frappe core) no-ops without an `email` key, so
  omitting email/full_name/password does not create an extra test User.
If a future ERPNext version changes setup_complete()'s required args,
this needs re-verifying the same way, not re-guessed.
"""

import frappe
from frappe.utils import getdate, today


def before_tests():
	if frappe.is_setup_complete():
		return

	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

	year = getdate(today()).year
	setup_complete(
		{
			"language": "English",
			"country": "Thailand",
			"timezone": "Asia/Bangkok",
			"currency": "THB",
			"company_name": "_Test Setup Wizard Co",
			"company_abbr": "TSWC",
			"chart_of_accounts": "Standard with Numbers",
			"fy_start_date": f"{year}-01-01",
			"fy_end_date": f"{year}-12-31",
		}
	)
