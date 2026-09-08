import frappe

SUPPORT_CONTENT = (
	'[{"id":"HOEnlt9aR9","type":"header","data":{"text":"<span class=\\"h2\\">Solar Support Module</span>","col":12}},'
	'{"id":"oxhWhXp9b2","type":"header","data":{"text":"<span class=\\"h4\\"><b>Reports &amp; Masters</b></span>","col":12}},'
	'{"id":"Ff8Ab3nLLN","type":"card","data":{"card_name":"Issues","col":4}},'
	'{"id":"_lndiuJTVP","type":"card","data":{"card_name":"Maintenance","col":4}},'
	'{"id":"N8aA2afWfi","type":"card","data":{"card_name":"Warranty","col":4}},'
	'{"id":"M5fxGuFwUR","type":"card","data":{"card_name":"Settings","col":4}},'
	'{"id":"xKH0kO9q4P","type":"card","data":{"card_name":"Reports","col":4}}]'
)

# (type, label, link_type, link_to, onboard, is_query_report, dependencies)
SUPPORT_LINKS = [
	("Card Break", "Issues", "DocType", None, 0, 0, None),
	("Link", "Issue", "DocType", "Issue", 1, 0, None),
	("Link", "Issue Type", "DocType", "Issue Type", 0, 0, None),
	("Link", "Issue Priority", "DocType", "Issue Priority", 0, 0, None),
	("Card Break", "Maintenance", "DocType", None, 0, 0, None),
	("Link", "Maintenance Schedule", "DocType", "Maintenance Schedule", 0, 0, None),
	("Link", "Maintenance Visit", "DocType", "Maintenance Visit", 0, 0, None),
	("Link", "Service Level Agreement", "DocType", "Service Level Agreement", 0, 0, None),
	("Card Break", "Warranty", "DocType", None, 0, 0, None),
	("Link", "Warranty Claim", "DocType", "Warranty Claim", 0, 0, None),
	("Link", "Serial No", "DocType", "Serial No", 0, 0, None),
	("Card Break", "Settings", "DocType", None, 0, 0, None),
	("Link", "Support Settings", "DocType", "Support Settings", 0, 0, None),
	("Card Break", "Reports", "DocType", None, 0, 0, None),
	(
		"Link",
		"First Response Time for Issues",
		"Report",
		"First Response Time for Issues",
		0,
		1,
		"Issue",
	),
]

DASHBOARD_CONTENT = (
	'[{"id":"ssdblk01","type":"custom_block",'
	'"data":{"custom_block_name":"Support Dashboard","col":12}}]'
)


def build():
	for name in ("Solar Support", "Solar Support Dashboard"):
		if frappe.db.exists("Workspace", name):
			frappe.delete_doc("Workspace", name, force=True, ignore_permissions=True)

	ws = frappe.new_doc("Workspace")
	ws.name = "Solar Support"
	ws.label = "Solar Support"
	ws.title = "Solar Support"
	ws.module = "Solar Support"
	ws.app = "hiper_solar"
	ws.type = "Workspace"
	ws.link_type = "DocType"
	ws.icon = "support"
	ws.custom_header_icon = "support"
	ws.indicator_color = "green"
	ws.public = 1
	ws.sequence_id = 0
	ws.content = SUPPORT_CONTENT
	for idx, (ltype, label, link_type, link_to, onboard, qr, deps) in enumerate(SUPPORT_LINKS, start=1):
		ws.append(
			"links",
			{
				"idx": idx,
				"type": ltype,
				"label": label,
				"link_type": link_type,
				"link_to": link_to,
				"onboard": onboard,
				"is_query_report": qr,
				"dependencies": deps,
				"hidden": 0,
				"link_count": 0,
			},
		)
	ws.insert(ignore_permissions=True)

	dash = frappe.new_doc("Workspace")
	dash.name = "Solar Support Dashboard"
	dash.label = "Solar Support Dashboard"
	dash.title = "Solar Support Dashboard"
	dash.module = "Solar Support"
	dash.app = "hiper_solar"
	dash.type = "Workspace"
	dash.link_type = "DocType"
	dash.icon = "chart"
	dash.indicator_color = "green"
	dash.public = 1
	dash.sequence_id = 1
	dash.content = DASHBOARD_CONTENT
	dash.append(
		"custom_blocks",
		{"idx": 1, "custom_block_name": "Support Dashboard"},
	)
	dash.insert(ignore_permissions=True)

	frappe.db.commit()
	print("Created:", frappe.db.get_all("Workspace", filters={"module": "Solar Support"}, pluck="name"))


build()
