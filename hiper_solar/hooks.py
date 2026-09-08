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

# Doctypes the app owns end to end.
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

# Standard doctypes the app extends.
EXTENDED_DOCTYPES = [
	"Customer",
	"Project",
	"Quotation",
	"Sales Order",
	"Serial No",
	"Stock Entry",
	"Issue",
]

# Custom Fields are named explicitly. Filtering by `dt` alone would sweep in
# fields belonging to india_compliance, hrms and crm that sit on the same
# doctypes, and shipping those would fight with their owning apps.
SOLAR_CUSTOM_FIELDS = [
	"Customer-custom_work_stage",
	"Customer-custom_customer_work_stage",
	"Customer-custom_payment_summary",
	"Customer-custom_attachment_gallery",
	"Customer-custom_commissioning_checks",
	"Customer-custom_support_center",
	"Customer-custom_support_center_html",
	"Installation-material_tab",
	"Installation-site_warehouse",
	"Installation-return_warehouse",
	"Installation-material_status",
	"Installation-materials",
	"Installation-total_transferred_qty",
	"Installation-total_used_qty",
	"Installation-total_balance_qty",
	"Installation-consumption_stock_entry",
	"Installation-return_stock_entry",
	"Installation-custom_document_previews",
	"Installation-workflow_state",
	"Issue-workflow_state",
	"KSEB Paper Works-workflow_state",
	"Paper Work-workflow_state",
	"Product Delivery Item-batch_serial_section",
	"Product Delivery Item-has_serial_no",
	"Product Delivery Item-has_batch_no",
	"Product Delivery Item-is_stock_item",
	"Product Delivery Item-select_serial_batch",
	"Product Delivery Item-serial_batch_summary",
	"Product Delivery Item-batch_allocation",
	"Project-custom_miscellaneous_expense",
	"Project-custom_total_other_costs",
	"Project-custom_total_cost",
	"Project-custom_budget_remaining",
	"Project-custom_budget_used_percent",
	"Project Commission-commissioning_tab",
	"Project Commission-commissioning_checklist",
	"Project Commission-checks_summary",
	"Project Commission-test_results_section",
	"Project Commission-dc_voltage",
	"Project Commission-ac_voltage",
	"Project Commission-column_break_test_1",
	"Project Commission-earthing_resistance",
	"Project Commission-insulation_resistance",
	"Project Commission-column_break_test_2",
	"Project Commission-generation_at_test",
	"Project Commission-meter_reading",
	"Project Commission-inverter_serial_numbers",
	"Project Commission-acceptance_section",
	"Project Commission-tested_by",
	"Project Commission-customer_acceptance",
	"Project Commission-workflow_state",
	"Sales Order-site_visit",
	"Serial No-custom_project",
	"Serial No-custom_customer",
	"Serial No-custom_installation",
	"Serial No-custom_consumed_date",
	"Serial No-custom_warranty_period",
	"Serial No-custom_warranty_period_unit",
	"Serial No-custom_warranty_status",
	"Serial No-custom_amc_period",
	"Serial No-custom_amc_period_unit",
	"Serial No-custom_amc_start_date",
	"Serial No-custom_amc_status",
	"Site Visit-workflow_state",
	"Solar Loan-workflow_state",
	"Stock Entry-installation",
	"Stock Entry-custom_projects",
	"Stock Entry-product_delivery",
	"Subsidy-workflow_state",
]

SOLAR_CLIENT_SCRIPTS = [
	"Customer Support Center",
	"Customer Payment Summary",
	"Customer Attachment Gallery",
	"Customer Work Stage Dashboard",
	"Customer Commissioning Checklist",
	"Installation - Create Paper Work",
	"Installation - Document Previews",
	"Installation - Material Consumption",
	"Installation - Total Project Cost Sync",
	"KSEB - Create Project Commission",
	"Paper Work - Create Subsidy and KSEB",
	"Product Delivery - Item Tracking Flags",
	"Product Delivery - Totals and Stock Transfer",
	"Project - Create Product Delivery",
	"Project - Total Cost Live Calculation",
	"Project Commission - Commissioning Checklist",
	"Quotation - Create Loan and Site Visit",
	"Sales Order - Trim Create Menu and Add Product Delivery",
	"Serial No - Warranty and Customer",
	"Site Visit - Create Sales Order",
	"Solar Loan - Create Site Visit",
	"Subsidy - Create KSEB",
]

SOLAR_SERVER_SCRIPTS = [
	"Stock Entry - Stamp Serial Consumed Date",
	"Stock Entry - Update Installation Material",
	"Stock Entry - Revert Installation Material",
	"Stock Entry - Mark Product Delivery Transferred",
	"Stock Entry - Revert Product Delivery Transfer",
	"Serial No - Warranty Dates and Status",
	"Project - Total Cost and Budget",
	"Project Commission - Enforce Commissioning Evidence",
]

SOLAR_WORKSPACES = [
	"Solar",
	"Solar Dashboard",
	"Solar Support",
	"Solar Support Dashboard",
]

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["name", "in", SOLAR_CUSTOM_FIELDS]],
	},
	{
		"dt": "Property Setter",
		"filters": [["doc_type", "in", SOLAR_DOCTYPES + EXTENDED_DOCTYPES]],
	},
	{
		"dt": "Client Script",
		"filters": [["name", "in", SOLAR_CLIENT_SCRIPTS]],
	},
	{
		"dt": "Server Script",
		"filters": [["name", "in", SOLAR_SERVER_SCRIPTS]],
	},
	{
		"dt": "Workflow",
		"filters": [["document_type", "in", SOLAR_DOCTYPES + ["Issue"]]],
	},
	{
		"dt": "Workflow State",
	},
	{
		"dt": "Workflow Action Master",
	},
	{
		"dt": "Custom HTML Block",
		"filters": [["name", "in", ["Solar Dashboard", "Support Dashboard"]]],
	},
	{
		"dt": "Workspace",
		"filters": [["name", "in", SOLAR_WORKSPACES]],
	},
	{
		"dt": "Print Format",
		"filters": [["name", "in", ["Quotation Swiss"]]],
	},
]
