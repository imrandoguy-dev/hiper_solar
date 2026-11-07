# Copyright (c) 2026, Hipersign Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SolarSettings(Document):
	def on_update(self):
		# Frappe v16 draws the desk sidebar from the module's Sidebar + the site's Custom Sidebar,
		# not from Workspace Sidebar, so the Sidebar tab is also written there (see hiper_solar/sidebar.py).
		# A problem here must never stop Solar Settings from saving.
		from hiper_solar.sidebar import sync_custom_sidebars

		frappe.db.savepoint("hiper_solar_sidebar")
		try:
			sync_custom_sidebars(self)
		except Exception:
			frappe.db.rollback(save_point="hiper_solar_sidebar")
			frappe.log_error(title="hiper_solar: could not apply the Solar Settings sidebar")
			frappe.msgprint(
				"The sidebar could not be applied. Everything else was saved. See Error Log for details.",
				title="Solar Settings",
				indicator="orange",
			)
