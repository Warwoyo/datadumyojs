#!/usr/bin/env python3
"""
Deterministic generator for a REALISTIC, normally-operating OJS 3.4.0-7 seed.

This package injects dummy-but-realistic data into an OJS 3.4.0-7 install: a
journal that looks like it is running normally -- multiple issues, sections, a
pool of editors/authors/reviewers, and submissions that each carry SEVERAL
uploaded files (manuscript, revised manuscript, figures, supplementary data,
cover letters, datasets, ...). Every uploaded file is a benign, non-empty,
real-looking document. There are NO executable uploads (.php/.phtml/.phar/...),
no web shells, no "compromise" markers, and nothing that simulates a hacked
instance.

Reads fixtures/fixture-spec.json (single source of truth) and emits, all keyed
to the same submission/file IDs:

  - files/journals/<jid>/articles/<sid>/<file>   physical uploads (FILES_DIR layout)
  - files/CHECKSUMS.sha256                         per-file integrity list
  - oracle/upload-ground-truth.v1.json            benign file inventory (no scan data)
  - oracle/scenario-matrix.v1.csv                 flat per-file inventory
  - mysql/database.sql                            OJS data-only seed (FK-consistent)
  - dataset-manifest.yaml  (integrity block only) hashes + counts

Determinism: same spec + same OJS_LAB_PASSWORD => identical files/ hashes (the
bcrypt password hash in database.sql is salted, so it varies and is excluded
from files_tree_sha256).
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # ojs34-upload-sast-dataset/
SPEC = ROOT / "fixtures" / "fixture-spec.json"
FILES = ROOT / "files"
ORACLE = ROOT / "oracle"
MYSQL = ROOT / "mysql"
FIX = ROOT / "fixtures"

NOW_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
LAB_PASSWORD = os.environ.get("OJS_LAB_PASSWORD", "ojs-lab-CHANGE-ME")
ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # fixed => byte-reproducible archives

EXT_MIME = {
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".json": "application/json",
    ".bib": "application/x-bibtex",
    ".ris": "application/x-research-info-systems",
    ".tex": "application/x-tex",
    ".png": "image/png",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# --------------------------------------------------------------------------- #
# physical content builders (all benign, all non-empty)                       #
# --------------------------------------------------------------------------- #
def _wrap(text, width=92):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out or [""]


def _pdf_escape(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(lines):
    """A valid, deterministic multi-line PDF (Helvetica, single page)."""
    body = ["BT", "/F1 11 Tf", "72 760 Td", "15 TL"]
    first = True
    for ln in lines:
        if first:
            body.append(f"({_pdf_escape(ln)}) Tj")
            first = False
        else:
            body.append(f"T* ({_pdf_escape(ln)}) Tj")
    body.append("ET")
    stream = "\n".join(body)
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.StringIO()
    out.write("%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n{o}\nendobj\n")
    xref_pos = out.tell()
    n = len(objs) + 1
    out.write(f"xref\n0 {n}\n0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n")
    out.write(f"trailer\n<< /Size {n} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n")
    return out.getvalue().encode("latin-1")


def manuscript_pdf(sub, label):
    authors = "; ".join(f"{a['given']} {a['family']}" for a in sub["authors"])
    affil = " / ".join(sorted({a["affiliation"] for a in sub["authors"]}))
    lines = [
        sub["title"],
        "",
        f"Authors: {authors}",
        f"Affiliations: {affil}",
        f"Correspondence: {sub['authors'][0]['email']}",
        f"Document: {label}",
        "",
        "Abstract",
    ]
    for para in sub["abstract"].split("\n"):
        lines += _wrap(para)
    lines += ["", "Keywords: " + ", ".join(sub["keywords"]), ""]
    lines.append("1. Introduction")
    lines += _wrap(
        "This manuscript is part of a realistic but synthetic Open Journal "
        "Systems instance used for non-production testing. The content is "
        "fictional; any resemblance to real studies is coincidental.")
    lines += ["", "2. Methods"]
    lines += _wrap(
        "The study design, materials, and analysis described here are "
        "illustrative placeholders that mirror the structure of a genuine "
        "research article so that downstream tooling sees plausible inputs.")
    lines += ["", "References"]
    for i, a in enumerate(sub["authors"], 1):
        lines.append(f"[{i}] {a['family']}, {a['given'][:1]}. ({sub['year']}). "
                     f"Working notes. {a['affiliation']}.")
    return build_pdf(lines)


def png_image(seed):
    """Small deterministic solid-colour PNG (16x16), colour varies by seed."""
    import struct
    import zlib
    w = h = 16
    r = (37 * (seed + 1)) % 256
    g = (91 * (seed + 1)) % 256
    b = (151 * (seed + 1)) % 256
    raw = bytearray()
    for _ in range(h):
        raw.append(0)                      # filter byte: none
        raw.extend(bytes((r, g, b)) * w)   # RGB row

    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8-bit RGB
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _zip_bytes(members):
    """Deterministic zip from a list of (name, bytes)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members:
            zi = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)
    return buf.getvalue()


def docx_document(title, paragraphs):
    """Smallest valid OOXML wordprocessing document (deterministic zip)."""
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')

    def esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    paras = [f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{esc(title)}</w:t></w:r></w:p>']
    for p in paragraphs:
        paras.append(f'<w:p><w:r><w:t xml:space="preserve">{esc(p)}</w:t></w:r></w:p>')
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           '<w:body>' + "".join(paras) + '</w:body></w:document>')
    return _zip_bytes([
        ("[Content_Types].xml", ct),
        ("_rels/.rels", rels),
        ("word/document.xml", doc),
    ])


def xlsx_workbook(sheet_name, rows):
    """Minimal valid .xlsx using inline strings (deterministic zip)."""
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
          '</Types>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                 '</Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          f'<sheets><sheet name="{sheet_name}" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wb_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
               '</Relationships>')

    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def col_ref(idx):
        s = ""
        idx += 1
        while idx:
            idx, rem = divmod(idx - 1, 26)
            s = chr(65 + rem) + s
        return s

    xml_rows = []
    for ri, row in enumerate(rows, start=1):
        cells = []
        for ci, val in enumerate(row):
            ref = f"{col_ref(ci)}{ri}"
            if isinstance(val, (int, float)):
                cells.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{esc(val)}</t></is></c>')
        xml_rows.append(f'<row r="{ri}">' + "".join(cells) + "</row>")
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetData>' + "".join(xml_rows) + '</sheetData></worksheet>')
    return _zip_bytes([
        ("[Content_Types].xml", ct),
        ("_rels/.rels", root_rels),
        ("xl/workbook.xml", wb),
        ("xl/_rels/workbook.xml.rels", wb_rels),
        ("xl/worksheets/sheet1.xml", sheet),
    ])


def build_content(fx, sub, seq):
    kind = fx["content_kind"]
    if kind == "text":
        return fx["content"].encode("utf-8")
    if kind == "manuscript_pdf":
        return manuscript_pdf(sub, fx.get("label", "Manuscript"))
    if kind == "png":
        return png_image(seq)
    if kind == "docx":
        return docx_document(fx["doc_title"], fx["paragraphs"])
    if kind == "xlsx":
        return xlsx_workbook(fx.get("sheet_name", "Sheet1"), fx["rows"])
    raise ValueError(f"unknown content_kind for {sub['submission_id']}: {kind}")


# --------------------------------------------------------------------------- #
# SQL helpers                                                                 #
# --------------------------------------------------------------------------- #
def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def insert(table, cols, rows):
    if not rows:
        return f"-- {table}: (none)\n"
    out = [f"-- {table}"]
    collist = ", ".join("`%s`" % c for c in cols)
    for r in rows:
        vals = ", ".join(q(r.get(c)) for c in cols)
        out.append(f"INSERT INTO `{table}` ({collist}) VALUES ({vals});")
    out.append("")
    return "\n".join(out)


def loc_array(locale):
    # OJS 3.4 stores list/array settings (supportedLocales, users.locales, ...)
    # as JSON, not PHP serialize() as in 3.3.
    return json.dumps([locale])


def bcrypt_hash(password):
    php = subprocess.run(
        ["php", "-r", "echo password_hash($argv[1], PASSWORD_BCRYPT);", password],
        capture_output=True, text=True)
    if php.returncode == 0 and php.stdout.startswith("$2"):
        return php.stdout.strip()
    sys.stderr.write("WARN: php bcrypt unavailable; emitting placeholder hash.\n")
    return "$2y$10$PLACEHOLDERPLACEHOLDERPLACEHOLDERPLACEHOLDERPLACEHOLD"


# --------------------------------------------------------------------------- #
# main                                                                        #
# --------------------------------------------------------------------------- #
def main():
    spec = json.loads(SPEC.read_text())
    jrn = spec["journal"]
    jid = jrn["journal_id"]

    # ---- render physical files, assign global file IDs ---------------------
    file_id = 0
    sf_id = 0
    checksum_lines = []
    file_records = []          # flat per-file records for SQL + oracle

    for sub in spec["submissions"]:
        sid = sub["submission_id"]
        for seq, fx in enumerate(sub["files"], start=1):
            file_id += 1
            sf_id += 1
            data = build_content(fx, sub, seq)
            physical = f"{file_id:04d}-{fx['physical_basename']}{fx['ext']}"
            rel = f"journals/{jid}/articles/{sid}/{physical}"
            target = FILES / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            sha = hashlib.sha256(data).hexdigest()
            checksum_lines.append(f"{sha}  {rel}")
            file_records.append({
                "file_id": file_id, "submission_file_id": sf_id,
                "submission_id": sid, "publication_id": sub["publication_id"],
                "seq": seq, "rel": rel, "physical": physical, "sha256": sha,
                "size": len(data), "ext": fx["ext"],
                "mimetype": EXT_MIME[fx["ext"]],
                "display_name": fx["display_name"],
                "genre_id": fx.get("genre_id", 1),
                "file_stage": fx["file_stage"],
                "is_galley": fx.get("is_galley", False),
                "galley_label": fx.get("galley_label"),
                "status": sub["status"],
            })

    (FILES / "CHECKSUMS.sha256").write_text("\n".join(checksum_lines) + "\n")
    files_tree_sha = hashlib.sha256(
        ("\n".join(sorted(checksum_lines)) + "\n").encode()).hexdigest()

    write_inventory(spec, file_records)
    write_inventory_csv(file_records)
    sql = write_sql(spec, file_records)
    db_sha = hashlib.sha256(sql.encode()).hexdigest()
    oracle_sha = hashlib.sha256(
        (ORACLE / "upload-ground-truth.v1.json").read_bytes()).hexdigest()

    write_manifest_integrity(oracle_sha, db_sha, files_tree_sha)

    print("Built realistic OJS seed:")
    print(f"  submissions       : {len(spec['submissions'])}")
    print(f"  uploaded files    : {len(file_records)}")
    print(f"  files_tree_sha256 : {files_tree_sha}")
    print(f"  database_sql_sha  : {db_sha}")
    print(f"  oracle_sha256     : {oracle_sha}")


def write_inventory(spec, file_records):
    out = {
        "schema_version": "2.0",
        "dataset_id": spec["dataset_id"],
        "ojs_version": spec["ojs_version"],
        "module": spec["module"],
        "created_at_utc": NOW_UTC,
        "description": ("Inventory of benign uploaded files in a realistic, "
                        "normally-operating OJS instance. No risky/executable "
                        "uploads and no compromise markers are present."),
        "journal_id": spec["journal"]["journal_id"],
        "files": [],
    }
    by_sub = {}
    for r in file_records:
        by_sub.setdefault(r["submission_id"], []).append(r)
    for sub in spec["submissions"]:
        for r in by_sub.get(sub["submission_id"], []):
            out["files"].append({
                "submission_id": r["submission_id"],
                "publication_id": r["publication_id"],
                "submission_file_id": r["submission_file_id"],
                "file_id": r["file_id"],
                "display_name": r["display_name"],
                "relative_path": r["rel"],
                "physical_filename": r["physical"],
                "mimetype": r["mimetype"],
                "sha256": r["sha256"],
                "size_bytes": r["size"],
                "genre_id": r["genre_id"],
                "file_stage": r["file_stage"],
                "is_galley": r["is_galley"],
                "submission_status": r["status"],
                "security_label": "benign",
                "profile_membership": (["core-published", "full-instance"]
                                       if r["status"] == "published"
                                       else ["full-instance"]),
            })
    ORACLE.mkdir(parents=True, exist_ok=True)
    (ORACLE / "upload-ground-truth.v1.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")


def write_inventory_csv(file_records):
    cols = ["submission_id", "submission_file_id", "file_id", "display_name",
            "relative_path", "mimetype", "genre_id", "file_stage", "is_galley",
            "submission_status", "sha256", "size_bytes"]
    lines = [",".join(cols)]
    for r in file_records:
        lines.append(",".join([
            str(r["submission_id"]), str(r["submission_file_id"]),
            str(r["file_id"]), r["display_name"], r["rel"], r["mimetype"],
            str(r["genre_id"]), str(r["file_stage"]),
            str(r["is_galley"]).lower(), r["status"], r["sha256"], str(r["size"]),
        ]))
    (ORACLE / "scenario-matrix.v1.csv").write_text("\n".join(lines) + "\n")


def write_sql(spec, file_records):
    jrn = spec["journal"]
    jid = jrn["journal_id"]
    locale = jrn["primary_locale"]
    pw = bcrypt_hash(LAB_PASSWORD)
    L = []
    A = L.append
    A("-- OJS 3.4.0-7 realistic instance seed (data-only).")
    A("-- dataset_id: %s" % spec["dataset_id"])
    A("-- Generated %s. Benign content only; no executable uploads." % NOW_UTC)
    A("--")
    A("-- SCOPE: data-only seed. Apply on top of a FRESH OJS 3.4.0-7 schema")
    A("--        (default site row) created by the OJS installer. It does NOT")
    A("--        create tables and does NOT modify OJS source. This seed DOES")
    A("--        insert the default submission-file genres for the journal,")
    A("--        because inserting the journal row directly (instead of via the")
    A("--        OJS UI) does not auto-create them. See README.md.")
    A("--")
    A("-- 3.4 schema notes vs 3.3: short locale codes (en), JSON array settings,")
    A("--   journals.current_issue_id (no issues.current), submissions.status +")
    A("--   varchar submission_progress, publications.date_published is DATE.")
    A("SET NAMES utf8mb4;")
    A("SET FOREIGN_KEY_CHECKS=0;")
    A("START TRANSACTION;")
    A("")

    # ---- journal + settings ------------------------------------------------
    # 3.4: the "current issue" lives on journals.current_issue_id (issues table
    # no longer has a `current` column).
    current_issue_id = next((i["issue_id"] for i in spec["issues"]
                             if i.get("current")), None)
    A(insert("journals",
             ["journal_id", "path", "seq", "primary_locale", "enabled",
              "current_issue_id"],
             [{"journal_id": jid, "path": jrn["path"], "seq": 1,
               "primary_locale": locale, "enabled": 1,
               "current_issue_id": current_issue_id}]))
    js = [
        {"setting_name": "name", "locale": locale, "setting_value": jrn["name"]},
        {"setting_name": "acronym", "locale": locale, "setting_value": jrn["acronym"]},
        {"setting_name": "abbreviation", "locale": locale, "setting_value": jrn["acronym"]},
        {"setting_name": "description", "locale": locale, "setting_value": jrn["description"]},
        {"setting_name": "onlineIssn", "locale": "", "setting_value": jrn["online_issn"]},
        {"setting_name": "publisherInstitution", "locale": locale, "setting_value": jrn["publisher"]},
        {"setting_name": "contactEmail", "locale": "", "setting_value": jrn["contact_email"]},
        {"setting_name": "contactName", "locale": "", "setting_value": jrn["contact_name"]},
        {"setting_name": "supportEmail", "locale": "", "setting_value": jrn["contact_email"]},
        {"setting_name": "supportName", "locale": "", "setting_value": jrn["contact_name"]},
        {"setting_name": "supportedLocales", "locale": "", "setting_value": loc_array(locale)},
        {"setting_name": "supportedFormLocales", "locale": "", "setting_value": loc_array(locale)},
        {"setting_name": "supportedSubmissionLocales", "locale": "", "setting_value": loc_array(locale)},
        {"setting_name": "enableOai", "locale": "", "setting_value": "1"},
        {"setting_name": "itemsPerPage", "locale": "", "setting_value": "25"},
        {"setting_name": "numPageLinks", "locale": "", "setting_value": "10"},
        {"setting_name": "publishingMode", "locale": "", "setting_value": "0"},
    ]
    for r in js:
        r["journal_id"] = jid
    A(insert("journal_settings",
             ["journal_id", "locale", "setting_name", "setting_value"], js))

    # ---- default submission-file genres for this context -------------------
    # OJS auto-creates these per journal through the UI; we insert the journal
    # directly, so we seed the 3.4 default genre set here (FK target for
    # submission_files.genre_id). Tuple = (genre_id, seq, category, dependent,
    # supplementary, required, entry_key).
    genre_defs = [
        (1, 0, 1, 0, 0, 1, "SUBMISSION"),
        (2, 1, 3, 0, 1, 0, "RESEARCHINSTRUMENT"),
        (3, 2, 3, 0, 1, 0, "RESEARCHMATERIALS"),
        (4, 3, 3, 0, 1, 0, "RESEARCHRESULTS"),
        (5, 4, 3, 0, 1, 0, "TRANSCRIPTS"),
        (6, 5, 3, 0, 1, 0, "DATAANALYSIS"),
        (7, 6, 3, 0, 1, 0, "DATASET"),
        (8, 7, 3, 0, 1, 0, "SOURCETEXTS"),
        (9, 8, 1, 1, 1, 0, "MULTIMEDIA"),
        (10, 9, 2, 1, 0, 0, "IMAGE"),
        (11, 10, 1, 1, 0, 0, "STYLE"),
        (12, 11, 3, 0, 1, 0, "OTHER"),
    ]
    genre_rows = [{"genre_id": g[0], "context_id": jid, "seq": g[1], "enabled": 1,
                   "category": g[2], "dependent": g[3], "supplementary": g[4],
                   "required": g[5], "entry_key": g[6]} for g in genre_defs]
    A(insert("genres",
             ["genre_id", "context_id", "seq", "enabled", "category",
              "dependent", "supplementary", "required", "entry_key"], genre_rows))

    # ---- issues ------------------------------------------------------------
    issue_rows, issue_settings = [], []
    for iss in spec["issues"]:
        issue_rows.append({
            "issue_id": iss["issue_id"], "journal_id": jid,
            "volume": iss["volume"], "number": iss["number"], "year": iss["year"],
            "published": iss["published"],
            "date_published": iss.get("date_published") if iss["published"] else None,
            "access_status": 1, "show_volume": 1, "show_number": 1,
            "show_year": 1, "show_title": 1,
        })
        issue_settings.append({"issue_id": iss["issue_id"], "locale": locale,
                               "setting_name": "title", "setting_value": iss["title"]})
    A(insert("issues",
             ["issue_id", "journal_id", "volume", "number", "year", "published",
              "date_published", "access_status", "show_volume",
              "show_number", "show_year", "show_title"], issue_rows))
    A(insert("issue_settings",
             ["issue_id", "locale", "setting_name", "setting_value"], issue_settings))

    # ---- sections ----------------------------------------------------------
    sec_rows, sec_settings = [], []
    for s in spec["sections"]:
        sec_rows.append({"section_id": s["section_id"], "journal_id": jid,
                         "seq": s["section_id"], "editor_restricted": 0,
                         "meta_indexed": 1, "meta_reviewed": 1,
                         "abstracts_not_required": 0, "hide_title": 0,
                         "hide_author": 0, "is_inactive": 0})
        sec_settings.append({"section_id": s["section_id"], "locale": locale,
                             "setting_name": "title", "setting_value": s["title"]})
        sec_settings.append({"section_id": s["section_id"], "locale": locale,
                             "setting_name": "abbrev", "setting_value": s["abbrev"]})
    A(insert("sections",
             ["section_id", "journal_id", "seq", "editor_restricted", "meta_indexed",
              "meta_reviewed", "abstracts_not_required", "hide_title", "hide_author",
              "is_inactive"], sec_rows))
    A(insert("section_settings",
             ["section_id", "locale", "setting_name", "setting_value"], sec_settings))

    # ---- users + groups ----------------------------------------------------
    user_rows, user_settings = [], []
    for u in spec["users"]:
        user_rows.append({
            "user_id": u["user_id"], "username": u["username"], "password": pw,
            "email": u["email"], "locales": loc_array(locale),
            "date_registered": u["date_registered"],
            "date_last_login": u.get("date_last_login", u["date_registered"]),
            "must_change_password": 0, "disabled": 0, "inline_help": 1,
        })
        user_settings += [
            {"user_id": u["user_id"], "locale": locale, "setting_name": "givenName", "setting_value": u["given"]},
            {"user_id": u["user_id"], "locale": locale, "setting_name": "familyName", "setting_value": u["family"]},
            {"user_id": u["user_id"], "locale": locale, "setting_name": "affiliation", "setting_value": u["affiliation"]},
            {"user_id": u["user_id"], "locale": locale, "setting_name": "country", "setting_value": u["country"]},
        ]
    A(insert("users",
             ["user_id", "username", "password", "email", "locales",
              "date_registered", "date_last_login", "must_change_password",
              "disabled", "inline_help"], user_rows))
    A(insert("user_settings",
             ["user_id", "locale", "setting_name", "setting_value"], user_settings))

    # one user_group per distinct (role_id, group name) in spec
    groups = spec["user_groups"]
    ug_rows, ugs_rows = [], []
    for g in groups:
        ctx = 0 if g["role_id"] == 1 else jid
        ug_rows.append({"user_group_id": g["user_group_id"], "context_id": ctx,
                        "role_id": g["role_id"], "is_default": 1, "show_title": 1,
                        "permit_self_registration": 0, "permit_metadata_edit": 1})
        ugs_rows.append({"user_group_id": g["user_group_id"], "locale": locale,
                         "setting_name": "name", "setting_value": g["name"]})
        ugs_rows.append({"user_group_id": g["user_group_id"], "locale": locale,
                         "setting_name": "abbrev", "setting_value": g["abbrev"]})
    A(insert("user_groups",
             ["user_group_id", "context_id", "role_id", "is_default", "show_title",
              "permit_self_registration", "permit_metadata_edit"], ug_rows))
    A(insert("user_group_settings",
             ["user_group_id", "locale", "setting_name", "setting_value"], ugs_rows))

    uug_rows = [{"user_group_id": m["user_group_id"], "user_id": m["user_id"]}
                for m in spec["user_group_memberships"]]
    A(insert("user_user_groups", ["user_group_id", "user_id"], uug_rows))

    author_ug_id = next(g["user_group_id"] for g in groups if g["name"] == "Author")

    # ---- submissions / publications / authors ------------------------------
    files_by_sub = {}
    for r in file_records:
        files_by_sub.setdefault(r["submission_id"], []).append(r)

    sub_rows, pub_rows, pub_settings = [], [], []
    author_rows, author_settings = [], []
    files_rows, sf_rows, sf_settings = [], [], []
    galley_rows = []
    author_id = 0
    galley_id = 0

    for sub in spec["submissions"]:
        sid = sub["submission_id"]
        pid = sub["publication_id"]
        published = sub["status"] == "published"
        stage_map = {"published": 5, "review": 3, "copyediting": 4, "draft": 1}
        stage_id = stage_map.get(sub["status"], 1)
        sub_rows.append({
            "submission_id": sid, "context_id": jid,
            "current_publication_id": pid,
            "date_last_activity": sub["date_last_activity"],
            "date_submitted": sub["date_submitted"],
            "last_modified": sub["date_last_activity"],
            "stage_id": stage_id, "locale": locale,
            # 3.4: submissions has its own status, and submission_progress is a
            # varchar workflow step ('' = completed wizard, not an int).
            "status": 3 if published else 1,
            "submission_progress": "",
            "work_type": 0,
        })

        first_author_id = author_id + 1
        # 3.4: publications.date_published is a DATE (YYYY-MM-DD), not datetime.
        pub_date = sub.get("date_published") if published else None
        if pub_date:
            pub_date = str(pub_date)[:10]
        pub_rows.append({
            "publication_id": pid, "access_status": 0,
            "date_published": pub_date,
            "last_modified": sub["date_last_activity"],
            "primary_contact_id": first_author_id,
            "section_id": sub["section_id"], "seq": sid,
            "submission_id": sid,
            "status": 3 if published else 1,
            "url_path": None, "version": 1,
        })
        pub_settings.append({"publication_id": pid, "locale": locale,
                             "setting_name": "title", "setting_value": sub["title"]})
        pub_settings.append({"publication_id": pid, "locale": locale,
                             "setting_name": "abstract",
                             "setting_value": "<p>" + sub["abstract"].replace("\n", "</p><p>") + "</p>"})
        if published:
            pub_settings.append({"publication_id": pid, "locale": "",
                                 "setting_name": "issueId", "setting_value": sub["issue_id"]})
            if sub.get("pages"):
                pub_settings.append({"publication_id": pid, "locale": "",
                                     "setting_name": "pages", "setting_value": sub["pages"]})

        for a in sub["authors"]:
            author_id += 1
            author_rows.append({"author_id": author_id, "email": a["email"],
                                "include_in_browse": 1, "publication_id": pid,
                                "seq": a["seq"], "user_group_id": author_ug_id})
            author_settings += [
                {"author_id": author_id, "locale": locale, "setting_name": "givenName", "setting_value": a["given"]},
                {"author_id": author_id, "locale": locale, "setting_name": "familyName", "setting_value": a["family"]},
                {"author_id": author_id, "locale": locale, "setting_name": "affiliation", "setting_value": a["affiliation"]},
                {"author_id": author_id, "locale": locale, "setting_name": "country", "setting_value": a["country"]},
            ]

        for r in files_by_sub.get(sid, []):
            files_rows.append({"file_id": r["file_id"], "path": r["rel"],
                               "mimetype": r["mimetype"]})
            sf_rows.append({
                "submission_file_id": r["submission_file_id"], "submission_id": sid,
                "file_id": r["file_id"], "genre_id": r["genre_id"],
                "file_stage": r["file_stage"],
                "viewable": 1 if (published and r["is_galley"]) else 0,
                "created_at": sub["date_submitted"], "updated_at": sub["date_last_activity"],
                "uploader_user_id": sub["submitter_user_id"],
                "assoc_type": None, "assoc_id": None,
            })
            sf_settings.append({"submission_file_id": r["submission_file_id"], "locale": locale,
                                "setting_name": "name", "setting_value": r["display_name"]})
            if r["is_galley"] and published:
                galley_id += 1
                galley_rows.append({
                    "galley_id": galley_id, "publication_id": pid, "locale": locale,
                    "label": r["galley_label"] or r["ext"].lstrip(".").upper(),
                    "seq": 0, "is_approved": 1,
                    "submission_file_id": r["submission_file_id"], "url_path": None,
                })

    A(insert("submissions",
             ["submission_id", "context_id", "current_publication_id",
              "date_last_activity", "date_submitted", "last_modified",
              "stage_id", "locale", "status", "submission_progress",
              "work_type"], sub_rows))
    A(insert("publications",
             ["publication_id", "access_status", "date_published", "last_modified",
              "primary_contact_id", "section_id", "seq", "submission_id",
              "status", "url_path", "version"], pub_rows))
    A(insert("publication_settings",
             ["publication_id", "locale", "setting_name", "setting_value"], pub_settings))
    A(insert("authors",
             ["author_id", "email", "include_in_browse", "publication_id", "seq",
              "user_group_id"], author_rows))
    A(insert("author_settings",
             ["author_id", "locale", "setting_name", "setting_value"], author_settings))
    A(insert("files", ["file_id", "path", "mimetype"], files_rows))
    A(insert("submission_files",
             ["submission_file_id", "submission_id", "file_id", "genre_id",
              "file_stage", "viewable", "created_at", "updated_at",
              "uploader_user_id", "assoc_type", "assoc_id"], sf_rows))
    A(insert("submission_file_settings",
             ["submission_file_id", "locale", "setting_name", "setting_value"], sf_settings))
    A(insert("publication_galleys",
             ["galley_id", "publication_id", "locale", "label", "seq",
              "is_approved", "submission_file_id", "url_path"], galley_rows))

    A("COMMIT;")
    A("SET FOREIGN_KEY_CHECKS=1;")
    A("")
    sql = "\n".join(L)
    MYSQL.mkdir(parents=True, exist_ok=True)
    (MYSQL / "database.sql").write_text(sql)
    return sql


def write_manifest_integrity(oracle_sha, db_sha, files_tree_sha):
    block = (
        "# AUTO-GENERATED integrity block. Do not edit by hand; rebuild instead.\n"
        "integrity:\n"
        f"  oracle_sha256: {oracle_sha}\n"
        f"  database_sql_sha256: {db_sha}\n"
        f"  files_tree_sha256: {files_tree_sha}\n"
        "build:\n"
        f"  created_at_utc: {NOW_UTC}\n"
        "  builder_version: generate.py-2.0\n"
    )
    (ROOT / "scripts" / "lib" / "_integrity.generated.yaml").write_text(block)


if __name__ == "__main__":
    main()
