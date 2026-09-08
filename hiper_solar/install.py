import frappe

MODULES = ["Solar", "Solar Support"]


def after_install():
	create_module_defs()


def create_module_defs():
	"""Module Defs normally arrive via modules.txt, but creating them
	explicitly makes the app safe to install on a site where a stale
	Module Def of the same name already exists."""
	for module_name in MODULES:
		if frappe.db.exists("Module Def", module_name):
			continue

		doc = frappe.new_doc("Module Def")
		doc.module_name = module_name
		doc.app_name = "hiper_solar"
		doc.custom = 0
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
