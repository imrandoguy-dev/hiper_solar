"""Bring Site Visit in line with the TBH reference site.

On TBH the Site Visit workflow and its `workflow_state` field were removed,
and the Status field now uses: Draft / Approved / On Hold / Cancelled
(shipped as a Property Setter). Fixtures only add or update records, they
never delete them, so sites that installed an earlier version of this app
still carry the old workflow. Left in place it would keep forcing the old
states, and records saved as "Not visited" / "Visited" would fail the new
Select validation on their next save.
"""

import frappe

STATUS_MAP = {
	"": "Draft",
	"Not visited": "Draft",
	"Visited": "Approved",
}


def execute():
	if frappe.db.exists("Workflow", "Site Visit"):
		frappe.delete_doc("Workflow", "Site Visit", ignore_permissions=True, force=True)

	if frappe.db.exists("Custom Field", "Site Visit-workflow_state"):
		frappe.delete_doc("Custom Field", "Site Visit-workflow_state", ignore_permissions=True, force=True)

	if not frappe.db.has_column("Site Visit", "status"):
		return

	for old, new in STATUS_MAP.items():
		if old:
			filters = {"status": old}
		else:
			filters = {"status": ["in", ["", None]]}
		names = frappe.get_all("Site Visit", filters=filters, pluck="name")
		for name in names:
			frappe.db.set_value("Site Visit", name, "status", new, update_modified=False)

	frappe.clear_cache(doctype="Site Visit")
