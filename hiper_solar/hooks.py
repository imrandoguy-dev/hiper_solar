app_name = "hiper_solar"
app_title = "Hiper Solar"
app_publisher = "Hipersign Technologies"
app_description = "Solar installation lifecycle management for ERPNext"
app_email = "support@hipersignerp.com"
app_license = "mit"

required_apps = ["erpnext"]

# Installation
# ------------
after_install = "hiper_solar.install.after_install"

# Includes in <head>
# ------------------
# app_include_css = "/assets/hiper_solar/css/hiper_solar.css"
# app_include_js = "/assets/hiper_solar/js/hiper_solar.js"

# Fixtures
# --------
# Everything that lives as data rather than code. Populated by
#   bench --site <site> export-fixtures --app hiper_solar
#
# The `name` filters below are deliberately explicit: filtering only by `dt`
# would sweep in Custom Fields belonging to india_compliance, hrms and others
# that happen to sit on the same doctypes. Each list is regenerated whenever
# fixtures are re-exported.

SOLAR_DOCTYPES = [
	"Solar Loan",
	"Site Visit",
	"Product Delivery",
	"Installation",
	"Paper Work",
	"Subsidy",
	"KSEB Office",
	"KSEB Paper Works",
	"Project Commission",
]

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["name", "in", []]],
	},
	{
		"dt": "Property Setter",
		"filters": [["name", "in", []]],
	},
	{
		"dt": "Client Script",
		"filters": [["name", "in", []]],
	},
	{
		"dt": "Server Script",
		"filters": [["name", "in", []]],
	},
	{
		"dt": "Workflow",
		"filters": [["document_type", "in", SOLAR_DOCTYPES]],
	},
	{
		"dt": "Workflow State",
		"filters": [["name", "in", []]],
	},
	{
		"dt": "Workflow Action Master",
		"filters": [["name", "in", []]],
	},
	{
		"dt": "Custom HTML Block",
		"filters": [["name", "in", []]],
	},
	{
		"dt": "Workspace",
		"filters": [["name", "in", ["Solar", "Solar Support"]]],
	},
	{
		"dt": "Workspace Sidebar",
		"filters": [["name", "in", ["Solar", "Solar Support"]]],
	},
	{
		"dt": "Print Format",
		"filters": [["name", "in", ["Quotation Swiss"]]],
	},
]
