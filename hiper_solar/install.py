import frappe
from frappe.installer import update_site_config

MODULES = ["Solar", "Solar Support"]


def after_install():
	enable_server_scripts()
	create_module_defs()
	ensure_crm_desktop_icon()


def after_migrate():
	ensure_crm_desktop_icon()


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
