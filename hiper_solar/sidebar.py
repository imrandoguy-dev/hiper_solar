"""Put the sidebars set in Solar Settings on the desk.

Since Frappe v16.5x a module's sidebar is no longer read from its `Workspace Sidebar`. It is:

  1. the base: the `Sidebar` the app ships for the module (hiper_solar/solar/sidebar/solar and
     hiper_solar/solar_support/sidebar/solar_support), or one Frappe computes from the module;
  2. with the site's `Custom Sidebar` for that module applied on top.

So the Sidebar tab of Solar Settings is written into the site's Custom Sidebar for the Solar and
Solar Support modules. It is saved through Frappe's own `_save_customization`, the same code the
desk's "Edit Sidebar for everyone" uses, so the rows are stored exactly the way Frappe expects:
  - a row naming an item the base already has is a reference (it can change the label and icon),
  - a row the base does not have is an added item,
  - a base item left out of the table is hidden.

An empty table means the site never set its own sidebar, so the app's sidebar is left as it is.
On a Frappe without Custom Sidebar this does nothing.
"""

import frappe

# Solar Settings table -> module whose sidebar it sets
SIDEBAR_TABLES = (("sidebar_items", "Solar"), ("custom_support_sidebar_items", "Solar Support"))

LINK_TARGET_DOCTYPE = {
	"DocType": "DocType",
	"Workspace": "Workspace",
	"Report": "Report",
	"Page": "Page",
	"Dashboard": "Dashboard",
}


def custom_sidebar_supported() -> bool:
	return bool(frappe.db.exists("DocType", "Custom Sidebar")) and bool(
		frappe.db.exists("DocType", "Sidebar")
	)


def sync_custom_sidebars(settings) -> list[str]:
	"""Write each filled Solar Settings sidebar table into its module's site-wide Custom Sidebar.

	Returns the rows that were skipped (target missing on this site), for the caller to show.
	"""
	skipped = []
	if not custom_sidebar_supported():
		return skipped

	try:
		from frappe.desk.doctype.custom_sidebar.custom_sidebar import _save_customization, base_items
		from frappe.desk.doctype.sidebar.sidebar import item_key
	except ImportError:
		return skipped

	for field, module in SIDEBAR_TABLES:
		if not settings.meta.has_field(field) or not frappe.db.exists("Module Def", module):
			continue
		table = [r for r in (settings.get(field) or []) if r.get("enabled")]
		if not table:
			continue

		base = {item_key(item): item for item in base_items(module)}
		rows, used = [], set()

		for r in table:
			row = settings_row_to_item(r, module, skipped)
			if not row:
				continue
			key = item_key(row)
			if key in used:
				continue
			used.add(key)

			held = base.get(key)
			if held:
				# the base already has it: name it, and carry the label/icon (Frappe drops any
				# value equal to the base's, so only real changes are stored)
				ref = {
					"type": row["type"],
					"link_type": held.get("link_type"),
					"link_to": held.get("link_to"),
					"url": held.get("url"),
					"filters": held.get("filters"),
					"label": row.get("label"),
					"icon": row.get("icon"),
					"child": row.get("child", 0),
					"hidden": 0,
					"added": 0,
				}
				if row["type"] == "Section Break":
					ref["key"] = key
				rows.append(ref)
			else:
				rows.append({**row, "hidden": 0, "added": 1})

		# base items the table leaves out are hidden, so the sidebar shows only what was chosen
		for key, held in base.items():
			if key in used:
				continue
			hidden = {
				"type": held.get("type"),
				"link_type": held.get("link_type"),
				"link_to": held.get("link_to"),
				"url": held.get("url"),
				"filters": held.get("filters"),
				"child": held.get("child", 0),
				"hidden": 1,
				"added": 0,
			}
			if held.get("type") == "Section Break":
				hidden["key"] = key
			rows.append(hidden)

		_save_customization(module, rows, user=None)

	return skipped


def settings_row_to_item(r, module: str, skipped: list) -> dict | None:
	"""Turn one Solar Sidebar Link row into a sidebar item, or None if it cannot be shown."""
	is_section = r.get("type") == "Section Break"
	link_type = r.get("link_type") or "DocType"
	label = r.get("label") or ""

	if is_section:
		return {
			"type": "Section Break",
			"label": label,
			"icon": r.get("icon"),
			"child": 0,
			"collapsible": 1,
		}

	if link_type == "URL":
		if not r.get("url"):
			skipped.append(f"{module} > {label} (URL is empty)")
			return None
		return {
			"type": "Link",
			"label": label,
			"link_type": "URL",
			"url": r.get("url"),
			"icon": r.get("icon"),
			"child": frappe.utils.cint(r.get("child")),
			"collapsible": 1,
		}

	link_to = r.get("link_to")
	if not link_to:
		skipped.append(f"{module} > {label} (Link To is empty)")
		return None
	target = LINK_TARGET_DOCTYPE.get(link_type)
	if target and not frappe.db.exists(target, link_to):
		skipped.append(f"{module} > {label} ({link_type} '{link_to}' not on this site)")
		return None

	return {
		"type": "Link",
		"label": label,
		"link_type": link_type,
		"link_to": link_to,
		"icon": r.get("icon"),
		"child": frappe.utils.cint(r.get("child")),
		"collapsible": 1,
	}
