"""Convert the site's custom doctypes into app-owned, file-based doctypes.

Requires developer_mode = 1. With developer mode on, saving a DocType whose
`custom` flag is 0 causes Frappe to write its .json and controller files into
the owning app's module folder.

Run once, on a throwaway copy of production. Never on a live site.
"""

import frappe

TARGET_MODULE = "Solar"

# Parents first, then child tables. Order does not strictly matter, but keeping
# masters first makes the output easier to read.
DOCTYPES = [
	"Solar Loan",
	"Site Visit",
	"Product Delivery",
	"Installation",
	"Paper Work",
	"Subsidy",
	"KSEB Office",
	"KSEB Paper Works",
	"Project Commission",
	"Loan Repayment Schedule",
	"Site Visit Photo",
	"Product Delivery Item",
	"Product Delivery Batch Allocation",
	"Installation Material",
	"Installation Checklist Item",
	"Installation Issue",
	"Paper Work Document",
	"Subsidy Disbursement",
	"Commissioning Check",
]


def convert():
	if not frappe.conf.get("developer_mode"):
		print("developer_mode is off. Enable it first:")
		print("  bench --site <site> set-config developer_mode 1")
		return

	if not frappe.db.exists("Module Def", TARGET_MODULE):
		print(f"Module Def '{TARGET_MODULE}' does not exist. Install hiper_solar first.")
		return

	converted, skipped, failed = [], [], []

	for name in DOCTYPES:
		if not frappe.db.exists("DocType", name):
			skipped.append((name, "not found"))
			continue

		doc = frappe.get_doc("DocType", name)

		if not doc.custom and doc.module == TARGET_MODULE:
			skipped.append((name, "already app-owned"))
			continue

		try:
			doc.custom = 0
			doc.module = TARGET_MODULE
			doc.save(ignore_permissions=True)
			converted.append(name)
		except Exception as e:
			failed.append((name, str(e)[:120]))

	frappe.db.commit()

	print(f"\nConverted ({len(converted)}):")
	for n in converted:
		print("  ", n)

	if skipped:
		print(f"\nSkipped ({len(skipped)}):")
		for n, why in skipped:
			print("  ", n, "-", why)

	if failed:
		print(f"\nFailed ({len(failed)}):")
		for n, why in failed:
			print("  ", n, "-", why)


convert()
