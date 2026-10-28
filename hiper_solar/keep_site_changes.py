"""Keep each site's own changes to the app's records through app updates.

Every `bench migrate` re-imports the app's fixtures with force=True: Frappe deletes the
site's copy of every Client Script, Server Script, Workflow, Custom Field, Property Setter,
HTML block, Print Format and Workspace the app ships and inserts the app's version again.
Re-importing a Workflow also switches every other Workflow on the same document off.
So anything a client changed in those records was silently lost on every update.

What this does (both steps never stop a migrate; problems are logged):

before_migrate -> snapshot()
    For every record the app ships, compare the site's copy with the app's new version.
      - same                                  -> nothing to do
      - different, site changed it AFTER the  -> "kept": the site's version is saved and put
        app last changed it                      back after the import
      - different, app changed it later       -> normal app update, the app's version wins
      - deleted on the site after the app     -> "removed": deleted again after the import
        last changed it
    On/off switches (Client Script enabled, Server Script disabled, Workflow active) are
    saved for every app script and for every Workflow on a document the app ships a
    Workflow for, so a site's own Workflow copy stays the active one.
    Every record that differs is also written to private/hiper_solar_backups/ so nothing
    is ever lost without a copy.

after_migrate -> restore()   (runs after the fixtures are imported, before Solar Settings
                              is applied again, so Solar Settings still has the last word)

Solar Settings > App Updates shows what was kept, and lets the site take the app's version
for one record ("use app version") or for everything ("reset") on the next update.
"""

import glob
import json
import os

import frappe
from frappe.utils import get_datetime, now

KEEP_DOCTYPES = (
	"Client Script",
	"Server Script",
	"Workflow",
	"Custom Field",
	"Property Setter",
	"Custom HTML Block",
	"Print Format",
	"Workspace",
)
# switched on/off by Solar Settings (Features, Approval Steps) or by hand; a different
# switch alone is not a "change" of the record, it is saved and restored on its own
TOGGLE_FIELD = {"Client Script": "enabled", "Server Script": "disabled", "Workflow": "is_active"}

META_KEYS = {
	"name",
	"doctype",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"idx",
	"docstatus",
	"lft",
	"rgt",
	"old_parent",
	"migration_hash",
	"_user_tags",
	"_comments",
	"_assign",
	"_liked_by",
	"_seen",
}
CHILD_META = META_KEYS | {"parent", "parentfield", "parenttype"}

SNAPSHOT_FILE = "hiper_solar_keep.json"
BACKUP_DIR = "hiper_solar_backups"


# ---------------------------------------------------------------------------
# comparing (pure, no database)
# ---------------------------------------------------------------------------


def key_of(doctype, name):
	return doctype + "|" + name


def _val(v):
	if v is None or v is False:
		return ""
	if v is True:
		return "1"
	if isinstance(v, (int, float)):
		if float(v) == int(v):
			v = int(v)
		s = str(v)
	else:
		s = str(v).replace("\r\n", "\n").strip()
	return "" if s in ("0", "0.0", "None") else s


def _norm_row(row, keys):
	return {k: _val(row.get(k)) for k in keys}


def normalise(doc, like):
	"""The parts of `doc` that matter, compared field by field with the app's record `like`.

	Only fields the app's record has are compared, so fields a newer Frappe adds to a
	doctype never count as a change. Child tables are compared row by row in order."""
	out = {}
	skip = META_KEYS | {TOGGLE_FIELD.get(like.get("doctype"), "")}
	for k, ref in like.items():
		if k in skip or k.startswith("__"):
			continue
		v = doc.get(k)
		if isinstance(ref, list) or isinstance(v, list):
			ref_rows = ref if isinstance(ref, list) else []
			rows = v if isinstance(v, list) else []
			keys = set()
			for r in ref_rows or rows:
				keys |= {kk for kk in r if kk not in CHILD_META and not kk.startswith("__")}
			keys = sorted(keys)
			out[k] = [_norm_row(r, keys) for r in rows]
		else:
			out[k] = _val(v)
	return out


def differs(site_doc, app_doc):
	return normalise(site_doc, app_doc) != normalise(app_doc, app_doc)


def changed_fields(site_doc, app_doc):
	a = normalise(site_doc, app_doc)
	b = normalise(app_doc, app_doc)
	return sorted(k for k in b if a.get(k) != b.get(k))


def classify(app_doc, site_doc, deleted_on, use_app):
	"""What to do with one app record.

	app_doc   the record as the app ships it now
	site_doc  the site's copy (None if the site does not have it)
	deleted_on when the site deleted it (None if never deleted)
	use_app   the site asked for the app's version of this record
	"""
	app_mod = get_datetime(app_doc.get("modified") or "1900-01-01")
	if site_doc is None:
		if deleted_on and get_datetime(deleted_on) > app_mod and not use_app:
			return "removed"
		return "new"
	if not differs(site_doc, app_doc):
		return "same"
	if get_datetime(site_doc.get("modified") or "1900-01-01") > app_mod:
		return "replace" if use_app else "keep"
	return "app_update"


# ---------------------------------------------------------------------------
# site helpers
# ---------------------------------------------------------------------------


def app_records():
	"""Every record in this app's fixtures whose doctype is kept, by key."""
	folder = os.path.join(os.path.dirname(__file__), "fixtures")
	out = {}
	for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
		try:
			with open(path) as f:
				docs = json.load(f)
		except Exception:
			continue
		for d in docs if isinstance(docs, list) else [docs]:
			if isinstance(d, dict) and d.get("doctype") in KEEP_DOCTYPES and d.get("name"):
				out[key_of(d["doctype"], d["name"])] = d
	return out


def _settings_value(field, default=None):
	try:
		if not frappe.db.exists("DocType", "Solar Settings"):
			return default
		if not frappe.get_meta("Solar Settings").has_field(field):
			return default
		v = frappe.db.get_single_value("Solar Settings", field)
		return default if v is None else v
	except Exception:
		return default


def _use_app_keys():
	try:
		return set(json.loads(_settings_value("custom_use_app_version", "") or "[]") or [])
	except Exception:
		return set()


def _deleted_on(doctype, name):
	try:
		rows = frappe.get_all(
			"Deleted Document",
			filters={"deleted_doctype": doctype, "deleted_name": name, "restored": 0},
			fields=["creation"],
			order_by="creation desc",
			limit=1,
		)
		return rows[0].creation if rows else None
	except Exception:
		return None


def _site_dict(doctype, name):
	return frappe.get_doc(doctype, name).as_dict(convert_dates_to_str=True)


def _path(name):
	return frappe.get_site_path("private", name)


# ---------------------------------------------------------------------------
# before_migrate
# ---------------------------------------------------------------------------


def snapshot():
	try:
		reset_all = frappe.utils.cint(_settings_value("custom_reset_to_app", 0))
		use_app = _use_app_keys()
		records = app_records()

		kept, removed, replaced, backups = {}, [], [], {}
		for key, app_doc in records.items():
			dt, name = app_doc["doctype"], app_doc["name"]
			try:
				if not frappe.db.exists("DocType", dt):
					continue
				site_doc = _site_dict(dt, name) if frappe.db.exists(dt, name) else None
				deleted_on = None if site_doc else _deleted_on(dt, name)
				what = classify(app_doc, site_doc, deleted_on, reset_all or key in use_app)
				if site_doc is not None and what in ("keep", "replace", "app_update"):
					backups[key] = site_doc
				if what == "keep":
					kept[key] = site_doc
				elif what == "removed":
					removed.append({"doctype": dt, "name": name, "deleted_on": str(deleted_on)})
				elif what == "replace":
					replaced.append({"doctype": dt, "name": name, "modified": site_doc.get("modified")})
			except Exception:
				frappe.log_error(title="hiper_solar: could not check " + key + " before migrate")

		toggles = {}
		for key, app_doc in records.items():
			dt = app_doc["doctype"]
			if dt in ("Client Script", "Server Script") and frappe.db.exists(dt, app_doc["name"]):
				f = TOGGLE_FIELD[dt]
				toggles[key] = frappe.db.get_value(dt, app_doc["name"], f)
		wf_doctypes = sorted({d["document_type"] for d in records.values() if d["doctype"] == "Workflow"})
		if wf_doctypes:
			for w in frappe.get_all(
				"Workflow", filters={"document_type": ["in", wf_doctypes]}, fields=["name", "is_active"]
			):
				toggles[key_of("Workflow", w.name)] = w.is_active

		data = {
			"at": now(),
			"kept": kept,
			"removed": removed,
			"replaced": replaced,
			"toggles": toggles,
		}
		os.makedirs(_path(""), exist_ok=True)
		with open(_path(SNAPSHOT_FILE), "w") as f:
			json.dump(data, f, indent=1, default=str)

		if backups:
			os.makedirs(_path(BACKUP_DIR), exist_ok=True)
			stamp = now().replace(" ", "_").replace(":", "")[:17]
			with open(os.path.join(_path(BACKUP_DIR), "before_update_" + stamp + ".json"), "w") as f:
				json.dump(backups, f, indent=1, default=str)
	except Exception:
		frappe.log_error(title="hiper_solar: could not save this site's own changes before migrate")


# ---------------------------------------------------------------------------
# after_migrate
# ---------------------------------------------------------------------------


def _clean(saved):
	data = {}
	for k, v in saved.items():
		if k in META_KEYS or k.startswith("__"):
			continue
		if isinstance(v, list):
			v = [{kk: vv for kk, vv in r.items() if kk not in CHILD_META and not kk.startswith("__")} for r in v]
		data[k] = v
	return data


def _put_back(saved):
	dt, name = saved["doctype"], saved["name"]
	data = _clean(saved)
	if frappe.db.exists(dt, name):
		doc = frappe.get_doc(dt, name)
		for k, v in data.items():
			doc.set(k, v)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_links = True
		doc.flags.ignore_mandatory = True
		doc.save()
	else:
		doc = frappe.get_doc(dict(data, doctype=dt))
		doc.flags.ignore_permissions = True
		doc.flags.ignore_links = True
		doc.flags.ignore_mandatory = True
		doc.insert(set_name=name)
	# keep the site's own date, so the next update still sees this as the site's change
	if saved.get("modified"):
		frappe.db.set_value(dt, name, "modified", saved["modified"], update_modified=False)


def restore():
	path = _path(SNAPSHOT_FILE)
	if not os.path.exists(path):
		return
	errors, kept_list, removed_list = [], [], []
	try:
		with open(path) as f:
			data = json.load(f) or {}

		for key, saved in (data.get("kept") or {}).items():
			try:
				_put_back(saved)
				frappe.db.commit()
				kept_list.append({"doctype": saved["doctype"], "name": saved["name"], "modified": saved.get("modified")})
			except Exception as e:
				frappe.db.rollback()
				errors.append(key + ": " + str(e)[:200])
				frappe.log_error(title="hiper_solar: could not put back " + key + " after migrate")

		for r in data.get("removed") or []:
			try:
				if frappe.db.exists(r["doctype"], r["name"]):
					frappe.delete_doc(r["doctype"], r["name"], force=1, ignore_permissions=True)
					frappe.db.commit()
				removed_list.append(r)
			except Exception as e:
				frappe.db.rollback()
				errors.append(key_of(r["doctype"], r["name"]) + " (delete): " + str(e)[:200])

		wf_doctypes = set()
		for key, value in (data.get("toggles") or {}).items():
			dt, name = key.split("|", 1)
			try:
				if not frappe.db.exists(dt, name):
					continue
				f = TOGGLE_FIELD[dt]
				if frappe.utils.cint(frappe.db.get_value(dt, name, f)) != frappe.utils.cint(value):
					frappe.db.set_value(dt, name, f, frappe.utils.cint(value), update_modified=False)
				if dt == "Workflow":
					wf_doctypes.add(frappe.db.get_value("Workflow", name, "document_type"))
			except Exception as e:
				errors.append(key + " (switch): " + str(e)[:200])

		for d in wf_doctypes:
			frappe.clear_cache(doctype=d)
		frappe.clear_cache()

		log = {
			"at": now(),
			"kept": kept_list,
			"removed": removed_list,
			"replaced": data.get("replaced") or [],
			"errors": errors,
		}
		if frappe.db.exists("DocType", "Solar Settings"):
			meta = frappe.get_meta("Solar Settings")
			if meta.has_field("custom_update_log"):
				frappe.db.set_single_value("Solar Settings", "custom_update_log", json.dumps(log, indent=1, default=str))
			if meta.has_field("custom_reset_to_app"):
				frappe.db.set_single_value("Solar Settings", "custom_reset_to_app", 0)
			if meta.has_field("custom_use_app_version"):
				frappe.db.set_single_value("Solar Settings", "custom_use_app_version", "[]")
		frappe.db.commit()
		os.remove(path)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="hiper_solar: could not put back this site's own changes after migrate")


# ---------------------------------------------------------------------------
# Solar Settings > App Updates
# ---------------------------------------------------------------------------


def _title(d):
	dt = d.get("doctype")
	if dt == "Property Setter":
		return " › ".join(x for x in [d.get("doc_type"), d.get("field_name"), d.get("property")] if x)
	if dt == "Custom Field":
		return (d.get("dt") or "") + " › " + (d.get("label") or d.get("fieldname") or "")
	return d.get("name")


@frappe.whitelist()
def preview():
	"""What the next app update keeps for this site, worked out from the site as it is now."""
	frappe.only_for("System Manager")
	use_app = _use_app_keys()
	items = []
	for key, app_doc in app_records().items():
		dt, name = app_doc["doctype"], app_doc["name"]
		if not frappe.db.exists("DocType", dt):
			continue
		site_doc = _site_dict(dt, name) if frappe.db.exists(dt, name) else None
		deleted_on = None if site_doc else _deleted_on(dt, name)
		what = classify(app_doc, site_doc, deleted_on, False)
		if what == "keep":
			items.append(
				{
					"key": key,
					"doctype": dt,
					"name": name,
					"title": _title(site_doc),
					"state": "changed",
					"when": site_doc.get("modified"),
					"fields": changed_fields(site_doc, app_doc),
					"use_app": key in use_app,
				}
			)
		elif what == "removed":
			items.append(
				{
					"key": key,
					"doctype": dt,
					"name": name,
					"title": _title(app_doc),
					"state": "removed",
					"when": str(deleted_on),
					"fields": [],
					"use_app": key in use_app,
				}
			)
	items.sort(key=lambda x: str(x["when"] or ""), reverse=True)
	try:
		log = json.loads(_settings_value("custom_update_log", "") or "{}") or {}
	except Exception:
		log = {}
	return {"items": items, "log": log}
