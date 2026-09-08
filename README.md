# Hiper Solar

Solar installation lifecycle management for ERPNext v16.

Packages the full pipeline — Quotation → Solar Loan → Site Visit → Sales Order →
Project → Product Delivery → Stock Entry → Installation → Paper Work →
Subsidy + KSEB → Project Commission — so a new customer site is one
`install-app` rather than a manual rebuild.

## Contents

**Module: Solar** — 9 master doctypes and 10 child tables, the Solar workspace,
the Quotation Swiss print format.

**Module: Solar Support** — warranty and AMC tracking on Serial No, the Customer
Support Center tab, the Item Wise Stock Movement report, the Solar Support
workspace.

**Fixtures** — custom fields, property setters, workflows, client scripts,
server scripts, dashboards.

## Install

```bash
bench get-app hiper_solar <repo-url>
bench --site <site> install-app hiper_solar
```

Requires `erpnext`. Server Scripts must be enabled in `site_config.json`:

```json
"server_script_enabled": 1
```

## Building the app from an existing site

This app was extracted from a live site. To re-run or extend that extraction:

1. Install this skeleton on the source site.
2. Enable developer mode: `bench --site <site> set-config developer_mode 1`
3. For each custom doctype, open it in the UI, uncheck **Custom**, set
   **Module** to `Solar` (or `Solar Support`), and save. Frappe writes the
   `.json` and controller files into this app.
4. Export per-doctype customisations:
   `bench --site <site> export-customizations --doctype "Customer" --module "Solar"`
5. Export the remaining fixtures:
   `bench --site <site> export-fixtures --app hiper_solar`
6. Commit.

Step 3 is the only destructive one. Take a backup first, and prefer a clone of
production over production itself.

## Site-specific configuration

Nothing in this app should hardcode a company name or warehouse suffix. Defaults
live in the **Solar Settings** single doctype and scripts read from it.
