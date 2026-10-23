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


def after_migrate():
	ensure_crm_desktop_icon()
	seed_solar_settings()


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
