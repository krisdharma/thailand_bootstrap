# Thailand Bootstrap

A first-party Frappe app that makes any ERPNext Company with `country = "Thailand"`
fully VAT/WHT-ready automatically, the moment it's created — no manual Chart of
Accounts, Thai Tax Settings, Tax Template, or Withholding Tax Type configuration
required afterward.

It depends on and provisions data *for* [`erpnext_thailand`](https://github.com/ecosoft-frappe/erpnext_thailand)
(Ecosoft's Thai localization app) — it does not modify erpnext_thailand or ERPNext
core in any way. Everything here uses public, documented extension points:
`doc_events`, `create_custom_fields`, and standard `frappe.get_doc(...).insert()`.

## Why this exists

`erpnext_thailand` ships zero company-scoped configuration automatically (confirmed
by reading its `hooks.py`/`install.py` in full — the only thing it installs by
itself is a global, non-company-scoped list of 15 Withholding Tax Type Of Income
codes). Every Chart of Accounts entry, Thai Tax Settings row, Tax Template, and
Withholding Tax Type has to be built by hand, per company, following the sequence
Ecosoft's own README describes.

This app turns that documented-but-manual sequence into idempotent, tested code
that runs automatically, so:
- there is no permanent "template Company" anywhere holding this configuration —
  a Golden Template / reference site can stay at true zero-Company,
- provisioning a new Thai company is not a clone-and-rename operation with an
  unverified rename cascade, it's just creating the Company normally,
- the exact recipe (which accounts, which templates, which WHT rates) lives in
  versioned JSON, not in institutional knowledge or a one-off manual runbook.

## What it does, concretely

On `Company.after_insert`, if `doc.country == "Thailand"`, it provisions:

1. **6 accounts** — Output VAT, Undue Output VAT, Input VAT, Undue Input VAT,
   Withholding Tax Receivable, Withholding Tax Payable (see
   `thailand_bootstrap/config/chart_of_accounts.json`).
2. **A Thai Tax Settings row** for the company, pointing at the 4 VAT accounts.
3. **Tax Templates** — Sales/Purchase, Product + Service/Undue variants, plus
   0%/Exempt Item Tax Templates (`config/tax_templates.json`).
4. **8 Withholding Tax Types** (1/2/3/5% × Pay/Receive) — see the note below on
   how these are modeled.

**Deliberately not automated** (matches the architecture review's own conclusion —
these are real, non-generic facts about the company, not VAT/WHT configuration):
the Company's Billing Address, its real Tax ID, and Supplier/Customer addresses.
`verify()` reports the missing Billing Address as a **warning**, never as a
provisioning failure, so it's never silently missed.

### Withholding Tax Type is modeled as a shared global record, not one-per-company

`Withholding Tax Type.title` is globally unique across the whole site (confirmed
in its doctype JSON — `autoname: field:title`, `unique: 1`). Its actual per-company
data lives in its own `accounts` child table (`Withholding Tax Type Account`,
fields `company` + `account`) — the same "one shared doc + one child row per
company" pattern `Thai Tax Settings` already uses. So this app creates each of the
8 WHT Type records **once, globally** (e.g. `WHT 3% (Pay)`), and for every new
Thai company just appends a row to its `accounts` table pointing at that
company's Withholding Tax Payable/Receivable account. This is a correction from
an earlier draft of this design that assumed per-company-suffixed titles — the
schema itself already solves this the same way Thai Tax Settings does.

## Public API (`thailand_bootstrap/api.py`)

```python
provision(company, force=False)   # idempotent; safe to call repeatedly
verify(company)                   # read-only report, {"ok": bool, "checks": [...], "warnings": [...]}
is_thailand_ready(company)        # bool convenience wrapper around verify()
deprovision(company, confirm=True)  # explicit teardown; hard-refuses if any GL Entry
                                     # references an account this module created
```

All four are whitelisted, so they're callable via `bench execute`, e.g.:

```sh
bench --site <site> execute thailand_bootstrap.api.provision --kwargs '{"company": "Acme Co"}'
bench --site <site> execute thailand_bootstrap.api.verify --kwargs '{"company": "Acme Co"}'
```

## Failure behavior

`on_company_created` (the `Company.after_insert` hook) **never raises** — Company
creation itself must never fail because of this module. If provisioning throws
partway through, it rolls back its own partial writes, logs the real error to
the Error Log, and leaves the company simply not-yet-Thailand-ready. `verify()`
will report that truthfully, and re-running `provision(company)` (idempotent —
every step is existence-checked before it writes anything) picks up wherever it
left off. This is a deliberate trade-off: fail-safe for Company creation over
fail-loud for provisioning. See `api.on_company_created`'s docstring.

## Extending the recipe

Adding a WHT rate, adjusting an account, or adding a template is a data change —
edit the relevant JSON under `thailand_bootstrap/config/`, not the provisioning
code in `thailand_bootstrap/provision/`. `provision(company, force=True)` repairs
Thai Tax Settings account references that have drifted from the recipe on an
already-provisioned company (accounts/templates/WHT types themselves are only
ever created-if-missing, never mutated in place).

The country check in `on_company_created` is a single `if` today. A second
country would be a `PROVISIONERS = {"Thailand": ..., "X": ...}` dispatch keyed
by `doc.country` — this app owns the Thailand recipe specifically, but the hook
mechanism generalizes without touching whatever Golden Template concept exists
elsewhere.

## Installing

Same as any other custom Frappe app in a multi-container bench: add it to
`apps.json`, rebuild the shared image, recreate the application containers,
then `bench --site <site> install-app thailand_bootstrap`. It has no doctypes
of its own to migrate — installation only runs `after_install` (adds the
`custom_thailand_bootstrap` tracking field to the 6 doctypes it writes to) and
registers the hook.

## Testing

```sh
bench --site <test-site> run-tests --app thailand_bootstrap
```

- `tests/test_provision.py` — automatic (hook) and manual provisioning, and that
  a non-Thai company is left completely untouched.
- `tests/test_idempotency.py` — three consecutive `provision()` calls produce
  zero duplicate rows.
- `tests/test_verify.py` — `verify()` actually catches corrupted/missing state,
  not just a rubber-stamp pass, and warns (without failing) on a missing
  Billing Address.
- `tests/test_transactional_smoke.py` — posts a real Sales Invoice against a
  provisioned company and confirms `erpnext_thailand`'s own GL-Entry-to-Tax-Invoice
  mechanism accepts it end to end. Scoped to the Product/due-VAT path only for
  now — see the module docstring for what's deliberately deferred (Service/Undue
  clearing via Payment Entry, and Withholding Tax deduction-on-payment) and why.

None of this has been executed against a real bench yet — it has only been
syntax-validated (`python3 -m py_compile`) and schema-grounded against the
actual installed `erpnext`/`erpnext_thailand` doctype definitions. Running
`run-tests` for real is the next step before this is installed anywhere.
