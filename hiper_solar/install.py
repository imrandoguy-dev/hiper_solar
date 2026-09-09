import frappe
from frappe.installer import update_site_config

MODULES = ["Solar", "Solar Support"]


def after_install():
	enable_server_scripts()
	create_module_defs()


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
