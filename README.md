# Hiper Solar

Solar installation lifecycle management for ERPNext v16, by Hipersign Technologies.

It packages the whole solar pipeline, workspaces, dashboards and quotation print
formats, so a new customer site is one `install-app` rather than a manual rebuild.

```
Lead → Site Visit → Quotation (from a Solar Package) → Solar Loan → Sales Order → Project
     → Product Delivery → Installation → KSEB → Paper Work → Project Commission → Subsidy
```

## Install

On Press (install.hipersign.com): add the app to the bench, then **Fetch Latest
Updates → Deploy**, then update the sites. On a plain bench:

```bash
bench get-app https://github.com/imrandoguy-dev/hiper_solar
bench --site <site> install-app hiper_solar
```

Requires `erpnext`. Frappe CRM (`crm`) is optional; when it is installed the app adds a
**Frappe CRM** icon to the desktop.

`after_install` turns on `server_script_enabled` in `site_config.json`, because the app's
Server Scripts never run without it. If that fails (permissions), set it by hand:

```json
"server_script_enabled": 1
```

## What you get

### Modules and desktop
- **Solar** and **Solar Support** modules, each with a workspace, a dashboard workspace
  (Solar Dashboard, Solar Support Dashboard) and a Workspace Sidebar.
- Desktop tiles for Solar and Solar Support with their own icons (`public/icons/desktop_icons`),
  created automatically. No more "Add to desktop" by hand. A **Frappe CRM** tile is added on
  every install and migrate when CRM is present.
- **Modules switcher**: a floating **Modules** button on every desk page (or **Alt+M**) that
  jumps between Organization, Solar, Solar Support, Accounting, Assets, Buying, CRM,
  Projects, Selling, Stock, Frappe CRM and HR, each opening with its own sidebar. Users only
  see the areas they can open. It can be minimised to an icon strip or closed to the button.
  (`public/js/module_navigator.js`, loaded through `app_include_js`.)

### Doctypes (module Solar)
| Area | Doctypes |
|---|---|
| Pipeline | Site Visit, Solar Loan, Product Delivery, Installation, Paper Work, KSEB Paper Works, Project Commission, Subsidy |
| Masters | KSEB Office, Solar Package Template |
| Print | Quotation Notes Template, Print Image Slot, Quotation Print Image, Print Extra Page |
| Child tables | Site Visit Photo, Loan Repayment Schedule, Product Delivery Item, Product Delivery Batch Allocation, Installation Material, Installation Checklist Item, Installation Issue, Paper Work Document, Commissioning Check, Subsidy Disbursement, Solar Document, Solar Package Template Item |

**Solar Support** adds warranty and AMC tracking on Serial No, the Customer Support Center
tab, the Item Wise Stock Movement report and the Support Dashboard.

### Sales flow
- **Lead → Site Visit → Quotation**: create buttons along the chain. A Site Visit creates a
  Quotation, not a Sales Order. Site Visit uses a plain status (Draft / Approved), without a
  workflow.
- **Solar Package Template**: a ready list of panels, inverter and accessories with prices.
  Pick one on a Quotation to load its items.
- **Notes**: pick a **Notes Template** on the Quotation (Terms tab) to fill *Notes (on print)*.
  If the Quotation has none, the Company's *Default Quotation Notes* print instead.
  Terms work the ERPNext way, through Terms and Conditions; the Company's default selling
  terms fill in automatically.
- Workflows: Solar Loan, Installation, Paper Work, KSEB Paper Work, Project Commission,
  Subsidy, Issue.

### Quotation print formats
| Format | Layout |
|---|---|
| **Solar Quotation Green** | One A4 page: header photo, customer, items table, totals, MNRE subsidy, notes, terms, signature and seal, bank, offices. |
| **Solar Quotation Green Compact** | One-page summary without an items table: package title, totals, Pay To, **Scan & Pay QR** with UPI ID, notes and terms. |
| **Right Img** | Right Image 3-page proposal (cover, products and specifications, pricing). Page artwork ships in `public/images/right_image/`. |
| **Quotation Swiss** | Classic layout. |

All four use the site's data: company name and logo, addresses linked to the Company, the
default company Bank Account, and the Company's *Quotation Print* fields (tagline,
signatory, signatory phone, UPI ID, default notes).

### Print Images (Quotation → Print Images tab)
Choose the print format you are going to print. The tab shows only what that format needs:

- **Image slots**: one box per image (e.g. Header Image, Signature, Seal, Payment QR,
  Cover Image). Upload, change or remove each one. A slot with a **Default** badge uses the
  format's standard image. Managers can save the current images as the defaults.
- **Extra pages**: full-page images (brochure, datasheet, warranty card…) printed as a
  whole A4 page at the page number you give. The format's own pages fill the other numbers
  in order. Default pages can be replaced or skipped on one quotation.

To give a new print format images, add rows to **Print Format → Image Slots** (and, for
whole pages, **Extra Pages**). The template reads them from `doc.custom_print_images` and
`doc.custom_print_extra_pages`; see Solar Quotation Green for the pattern. A slot can also
store its image in an existing Quotation field (*Store in Quotation Field*), which is how
older formats with their own photo fields keep working.

Images uploaded from the tab are saved as public files, so they always appear in PDFs.

## Repository layout

```
hiper_solar/
  hooks.py                 fixture lists (what ships), app_include_js, install hooks
  install.py               after_install / after_migrate (server scripts, module defs, CRM tile)
  solar/doctype/           Solar doctypes
  solar_support/           Solar Support module
  desktop_icon/            desktop tiles
  fixtures/                custom fields, property setters, client and server scripts,
                           workflows, workspaces, sidebars, dashboards, print formats
  public/icons/            desktop tile SVGs
  public/images/           app logo, Right Image artwork
  public/js/               module_navigator.js
  patches/                 data patches run on migrate
```

## Changing the app

Most of the app is fixtures, so the usual loop is: change it on the demo site
(solar.hipersignerp.cloud), export the record into the matching file in `fixtures/`, add its
name to the list in `hooks.py` if it is new, commit, push to `main`, then deploy through Press.

Things worth knowing:
- Fixtures are added and updated on migrate, never deleted. To remove something from sites,
  delete it there (or write a patch).
- A fixture only overwrites a site's copy when the file's `modified` is newer than the
  site's.
- Public workspaces that have both a module and an app set, but no JSON file in the app, are
  deleted by migrate. The Solar Support workspaces ship with module and app cleared for that
  reason.
- Desktop tiles are drawn from `public/icons/desktop_icons/<solid|subtle>/<label>.svg` or a
  logo URL. The `icon` field alone is not shown.
- The app must not hardcode a company name or warehouse. Read them from the document or the
  Company.

### Rebuilding from a site
This app was extracted from a live site. To extend that extraction:

1. Take a backup and work on a copy of production, not production itself.
2. Enable developer mode: `bench --site <site> set-config developer_mode 1`
3. For each custom doctype, open it, uncheck **Custom**, set **Module** to `Solar`
   (or `Solar Support`) and save. Frappe writes its files into this app.
4. `bench --site <site> export-fixtures --app hiper_solar`
5. Commit.
