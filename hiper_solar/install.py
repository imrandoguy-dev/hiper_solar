import json
import os

import frappe
from frappe.installer import update_site_config

MODULES = ["Solar", "Solar Support"]


def after_install():
	enable_server_scripts()
	create_module_defs()
	ensure_crm_desktop_icon()
	seed_solar_settings()


def before_migrate():
	backup_sidebars()


def after_migrate():
	ensure_crm_desktop_icon()
	seed_solar_settings()
	reapply_solar_settings()


def enable_server_scripts():
	"""The app ships 8 Server Scripts that drive stock movement, warranty dates
	and project costing. Frappe refuses to execute any Server Script unless
	`server_script_enabled` is set in site_config.json, so without this they
	install silently and then never run — the hardest kind of failure to spot,
	because nothing errors, the numbers are just wrong.
	"""
	if frappe.conf.get("server_script_enabled"):
		return

	try:
		update_site_config("server_script_enabled", 1)
	except Exception:
		frappe.log_error(
			title="hiper_solar: could not enable server scripts",
			message="Set 'server_script_enabled': 1 in site_config.json manually.",
		)


def create_module_defs():
	"""Module Defs normally arrive via modules.txt, but creating them
	explicitly makes the app safe to install on a site where a stale
	Module Def of the same name already exists — which is the case on any
	site where the Solar workspace was built by hand before the app existed.
	"""
	for module_name in MODULES:
		existing = frappe.db.get_value(
			"Module Def", module_name, ["app_name", "package", "custom"], as_dict=True
		)

		if existing:
			# A hand-made Module Def points at the wrong app and often carries a
			# `package`, which redirects doctype exports away from this app.
			if existing.app_name != "hiper_solar" or existing.package or existing.custom:
				frappe.db.set_value(
					"Module Def",
					module_name,
					{"app_name": "hiper_solar", "package": None, "custom": 0},
				)
			continue

		doc = frappe.new_doc("Module Def")
		doc.module_name = module_name
		doc.app_name = "hiper_solar"
		doc.custom = 0
		doc.insert(ignore_permissions=True)

	frappe.db.commit()


def ensure_crm_desktop_icon():
	"""Put Frappe CRM on the v16 desktop when it is installed.

	The Solar and Solar Support icons ship as files in hiper_solar/desktop_icon and
	are synced by Frappe itself. The CRM icon cannot ship that way because CRM is
	optional, so it is created here. Frappe only builds an app icon from
	`add_to_apps_screen` at the moment that app is installed, and on our sites it
	has repeatedly ended up missing, so this checks on every install and migrate.
	"""
	if "crm" not in frappe.get_installed_apps():
		return

	try:
		if frappe.db.exists("Desktop Icon", {"icon_type": "App", "app": "crm"}):
			return

		label = "Frappe CRM"
		values = {
			"label": label,
			"icon_type": "App",
			"link_type": "External",
			"link": "/crm",
			"app": "crm",
			"logo_url": "/assets/crm/images/logo.svg",
			"bg_color": "gray",
			"hidden": 0,
			"idx": 2,
		}

		# Frappe may already have made a workspace-link icon called "Frappe CRM"
		# for CRM's own workspace; the label is the docname, so reuse that record.
		if frappe.db.exists("Desktop Icon", label):
			icon = frappe.get_doc("Desktop Icon", label)
			icon.update(values)
			icon.link_to = None
			icon.save(ignore_permissions=True)
		else:
			icon = frappe.new_doc("Desktop Icon")
			icon.update(values)
			icon.insert(ignore_permissions=True)

		frappe.db.commit()
		frappe.cache.delete_value("desktop_icons")
	except Exception:
		frappe.log_error(title="hiper_solar: could not create the Frappe CRM desktop icon")


def seed_solar_settings():
	"""Fill Solar Settings with the standard Create Buttons, Features, Approval Steps
	and Solar Package sections the first time the app lands on a site.

	Runs only while the Create Buttons table is empty, so a site that has already
	set up its own Solar Settings is never touched. Everything is read from the
	site as it is now, so seeding changes nothing on its own:
	  - a Feature is listed only if at least one of its scripts exists here, and is
	    marked On only if one of those scripts is already enabled;
	  - an Approval Step is listed only if the Workflow exists, with its current
	    Active state;
	  - Create Buttons are listed only for documents that exist on this site;
	  - the sectioned Solar Package layout starts switched off;
	  - the Sidebar tab is left empty (use Load > Load Current Sidebar), so saving
	    Solar Settings never rewrites a site's own sidebar by surprise.
	"""
	try:
		if not frappe.db.exists("DocType", "Solar Settings"):
			return
		if frappe.db.count("Solar Create Button", {"parent": "Solar Settings"}):
			return

		path = os.path.join(
			os.path.dirname(__file__), "solar", "doctype", "solar_settings", "solar_settings_defaults.json"
		)
		with open(path) as f:
			defaults = json.load(f)

		doc = frappe.get_single("Solar Settings")
		doc.target_sidebar = doc.target_sidebar or "Solar"

		for row in defaults.get("create_buttons", []):
			if frappe.db.exists("DocType", row["document"]) and (
				not row.get("creates") or frappe.db.exists("DocType", row["creates"])
			):
				doc.append("create_buttons", row)

		def names(text):
			return [n.strip() for n in (text or "").split("\n") if n.strip()]

		for row in defaults.get("features", []):
			client = [n for n in names(row.get("client_scripts")) if frappe.db.exists("Client Script", n)]
			server = [n for n in names(row.get("server_scripts")) if frappe.db.exists("Server Script", n)]
			if not client and not server:
				continue
			on = any(frappe.db.get_value("Client Script", n, "enabled") for n in client) or any(
				not frappe.db.get_value("Server Script", n, "disabled") for n in server
			)
			doc.append("features", dict(row, enabled=1 if on else 0))

		for wf in defaults.get("workflows", []):
			if frappe.db.exists("Workflow", wf):
				doc.append(
					"workflows",
					{
						"workflow": wf,
						"document_type": frappe.db.get_value("Workflow", wf, "document_type"),
						"is_active": frappe.db.get_value("Workflow", wf, "is_active"),
					},
				)

		package = defaults.get("package", {})
		if doc.meta.has_field("custom_package_sections") and not doc.get("custom_package_sections"):
			doc.custom_package_sections_enabled = 0
			for key in ("custom_main_section_title", "custom_main_section_subtitle", "custom_main_section_color"):
				if not doc.get(key):
					doc.set(key, package.get(key))
			for row in package.get("custom_package_sections", []):
				doc.append("custom_package_sections", row)

		doc.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="hiper_solar: could not seed Solar Settings")


# ---------------------------------------------------------------------------
# Keeping each site's own Solar Settings through app updates
# ---------------------------------------------------------------------------
# The app ships the Solar / Solar Support sidebars, property setters (e.g. the default
# Quotation print format) and scripts as fixtures, and every migrate writes those over the
# site's copies. A site's own choices live in Solar Settings instead, so after the fixtures
# are synced the settings are saved once more, which applies them again:
#   - before_migrate keeps a copy of both sidebars exactly as the site has them, so a site
#     that never saved its sidebar in Solar Settings still gets its own order back;
#   - new links the app adds to a sidebar are merged into the site's own order, after the
#     same item they follow in the app; a link the site hid or removed is not brought back;
#   - a saved link whose target no longer exists is skipped and listed, never an error.

SIDEBAR_FIELDS = (("sidebar_items", "Solar"), ("custom_support_sidebar_items", "Solar Support"))
SIDEBAR_ROW_KEYS = ("type", "label", "link_type", "link_to", "url", "icon", "child")


def _sidebar_backup_path():
	return frappe.get_site_path("private", "hiper_solar_sidebar_backup.json")


def _sidebar_names():
	"""The sidebar each Solar Settings table writes to."""
	names = {}
	for field, default in SIDEBAR_FIELDS:
		names[field] = default
	try:
		if frappe.db.exists("DocType", "Solar Settings"):
			names["sidebar_items"] = frappe.db.get_single_value("Solar Settings", "target_sidebar") or "Solar"
	except Exception:
		pass
	return names


def backup_sidebars():
	"""Copy the Solar sidebars as this site has them, before the app's fixtures replace them."""
	try:
		out = {}
		for sb_name in set(_sidebar_names().values()):
			if not frappe.db.exists("Workspace Sidebar", sb_name):
				continue
			items = frappe.get_all(
				"Workspace Sidebar Item",
				filters={"parent": sb_name, "parenttype": "Workspace Sidebar"},
				fields=list(SIDEBAR_ROW_KEYS),
				order_by="idx asc",
			)
			out[sb_name] = [dict(i) for i in items]
		if out:
			path = _sidebar_backup_path()
			os.makedirs(os.path.dirname(path), exist_ok=True)
			with open(path, "w") as f:
				json.dump(out, f, indent=1, default=str)
	except Exception:
		frappe.log_error(title="hiper_solar: could not back up the Solar sidebars before migrate")


def _link_key(item):
	if item.get("type") == "Section Break":
		return "section|" + (item.get("label") or "")
	if item.get("link_type") == "URL":
		return "url|" + (item.get("url") or "")
	return (item.get("link_type") or "DocType") + "|" + (item.get("link_to") or "")


def _merge_app_links(rows, app_items, known, sb_name):
	"""Add links the app has and this site has never been offered, keeping the site's order."""
	present = [_link_key(r) for r in rows]
	for n, item in enumerate(app_items):
		key = _link_key(item)
		mark = sb_name + "::" + key
		if key in present:
			known.add(mark)
			continue
		if mark in known:
			# offered on an earlier update and since removed by this site: leave it out
			continue
		pos = 0
		for prev in reversed(app_items[:n]):
			if _link_key(prev) in present:
				pos = present.index(_link_key(prev)) + 1
				break
		is_section = item.get("type") == "Section Break"
		rows.insert(
			pos,
			{
				"enabled": 1,
				"type": "Section Break" if is_section else "Link",
				"label": item.get("label"),
				"link_type": item.get("link_type") or "DocType",
				"link_to": None if is_section else item.get("link_to"),
				"url": item.get("url"),
				"icon": item.get("icon"),
				"child": 0 if is_section else (item.get("child") or 0),
			},
		)
		present.insert(pos, key)
		known.add(mark)
	return rows


def reapply_solar_settings():
	"""Save Solar Settings once more after the fixtures are synced, so this site's own
	sidebars, field changes, default print formats, names and switches are applied again."""
	if not frappe.db.exists("DocType", "Solar Settings"):
		return
	path = _sidebar_backup_path()
	try:
		backup = {}
		if os.path.exists(path):
			with open(path) as f:
				backup = json.load(f) or {}

		app_sidebars = {}
		fixture = os.path.join(os.path.dirname(__file__), "fixtures", "workspace_sidebar.json")
		if os.path.exists(fixture):
			with open(fixture) as f:
				for sb in json.load(f):
					app_sidebars[sb.get("name")] = sb.get("items") or []

		doc = frappe.get_single("Solar Settings")
		has_known = doc.meta.has_field("custom_known_app_links")
		known = set(json.loads(doc.get("custom_known_app_links") or "[]") or []) if has_known else set()
		names = _sidebar_names()

		for field, _default in SIDEBAR_FIELDS:
			if not doc.meta.has_field(field):
				continue
			sb_name = names[field]
			rows = [dict({"enabled": r.enabled}, **{k: r.get(k) for k in SIDEBAR_ROW_KEYS}) for r in doc.get(field)]
			if not rows and backup.get(sb_name):
				rows = [dict({"enabled": 1}, **{k: i.get(k) for k in SIDEBAR_ROW_KEYS}) for i in backup[sb_name]]
			if not rows:
				# this site never had its own copy of this sidebar: the app's sidebar stays
				continue
			doc.set(field, _merge_app_links(rows, app_sidebars.get(sb_name, []), known, sb_name))

		if has_known:
			doc.custom_known_app_links = json.dumps(sorted(known), indent=1)

		# Server scripts are switched off while a migrate runs; this one save has to run them,
		# because they are what applies the settings. A link to something the update removed
		# must not stop the save: the Apply script skips such links and lists them.
		was_migrating = frappe.flags.in_migrate
		frappe.flags.in_migrate = False
		try:
			doc.flags.ignore_links = True
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)
		finally:
			frappe.flags.in_migrate = was_migrating
		frappe.db.commit()
		if os.path.exists(path):
			os.remove(path)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="hiper_solar: could not re-apply Solar Settings after migrate")
