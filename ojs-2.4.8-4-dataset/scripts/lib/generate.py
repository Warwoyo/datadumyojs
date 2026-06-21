#!/usr/bin/env python3
"""
Deterministic builder for the OJS 2.4.8-4 upload-directory SAST dataset
(baseline + clean/controller/compromised overlays).

Implements the contract in panduan_dataset_dummy_ojs_2_4_8_4_sast_upload.md.

It emits, all keyed to the same article/file IDs:
  - mysql/files/journals/1/articles/<aid>/<stage-dir>/<aid>-<fid>-<rev>-<CODE>.<ext>
  - mysql/files/journals/1/issues/1/public/<cover>           (issue cover)
  - mysql/public/journals/1/<logo>                           (public asset)
  - mysql/database.sql                                       data-only OJS 2.4 seed
  - ground-truth/{entity-inventory,file-inventory,upload-oracle}.csv
  - ground-truth/dataset-manifest.yaml + sha256sums*.txt
  - ground-truth/expected-findings-{clean,compromised}.json
  - scenarios/{clean,controller,compromised}/overlay-files/... (inert artifacts)

SAFETY: every "compromised" artifact is INERT — plain text/bytes with a risky
NAME/EXTENSION/LOCATION only. No PHP, no server-side tags, no executable code,
no payloads (panduan sections 1, 3.2, 10.6).

OJS 2.4 file layout/stage codes follow classes/file/ArticleFileManager.inc.php
(documented in the panduan section 2.3).
"""
import base64
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # ojs-2.4.8-4-dataset/
MYSQL = ROOT / "mysql"
FILES = MYSQL / "files"
PUBLIC = MYSQL / "public"
GT = ROOT / "ground-truth"
SCEN = ROOT / "scenarios"

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TS = "2026-06-21 09:00:00"
LAB_PASSWORD = os.environ.get("OJS_LAB_PASSWORD", "ojs248-lab-CHANGE-ME")
JOURNAL_ID = 1
JOURNAL_PATH = "jdis"
LOCALE = "en_US"

# file_stage int -> (relative dir under article, filename stage code)
STAGE = {
    1: ("submission/original", "SM"),
    2: ("submission/review", "RV"),
    3: ("submission/editor", "ED"),
    4: ("submission/copyedit", "CE"),
    5: ("submission/layout", "LE"),
    6: ("public", "PB"),
    7: ("supp", "SP"),
    8: ("note", "NT"),
    9: ("attachment", "AT"),
}
EXT_MIME = {
    "pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "odt": "application/vnd.oasis.opendocument.text", "csv": "text/csv",
    "txt": "text/plain", "png": "image/png", "jpg": "image/jpeg",
}
# OJS 2.x role constants
ROLE = {"admin": 0x00000001, "manager": 0x00000010, "editor": 0x00000100,
        "section_editor": 0x00000200, "reviewer": 0x00001000,
        "author": 0x00010000, "reader": 0x00100000}

ZIP_TIME = (1980, 1, 1, 0, 0, 0)
# minimal valid 1x1 JPEG
JPG_BYTES = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgK"
    "CgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/wAALCAABAAEBAREA/8QAFAAB"
    "AAAAAAAAAAAAAAAAAAAAAv/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AfwD/2Q==")


# --------------------------------------------------------------------------- #
# content builders (benign, non-empty, deterministic)                         #
# --------------------------------------------------------------------------- #
def _esc_pdf(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(title, lines):
    body = ["BT", "/F1 12 Tf", "72 760 Td", "16 TL", f"({_esc_pdf(title)}) Tj"]
    for ln in lines:
        body.append(f"T* ({_esc_pdf(ln)}) Tj")
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
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(out.tell())
        out.write(f"{i} 0 obj\n{o}\nendobj\n")
    xref = out.tell()
    n = len(objs) + 1
    out.write(f"xref\n0 {n}\n0000000000 65535 f \n")
    for o in offs:
        out.write(f"{o:010d} 00000 n \n")
    out.write(f"trailer\n<< /Size {n} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n")
    return out.getvalue().encode("latin-1")


def _zip(members, mimetype=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if mimetype is not None:  # ODT requires stored 'mimetype' first
            zi = zipfile.ZipInfo("mimetype", date_time=ZIP_TIME)
            zi.compress_type = zipfile.ZIP_STORED
            z.writestr(zi, mimetype)
        for name, data in members:
            zi = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)
    return buf.getvalue()


def build_docx(title, paras):
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
    def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = "".join(f'<w:p><w:r><w:t xml:space="preserve">{esc(p)}</w:t></w:r></w:p>'
                   for p in [title] + paras)
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           f'<w:body>{body}</w:body></w:document>')
    return _zip([("[Content_Types].xml", ct), ("_rels/.rels", rels),
                 ("word/document.xml", doc)])


def build_odt(title, paras):
    def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    content = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
               'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">'
               '<office:body><office:text>'
               + "".join(f"<text:p>{esc(p)}</text:p>" for p in [title] + paras)
               + '</office:text></office:body></office:document-content>')
    manifest = ('<?xml version="1.0" encoding="UTF-8"?>'
                '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
                '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>'
                '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
                '</manifest:manifest>')
    return _zip([("content.xml", content), ("META-INF/manifest.xml", manifest)],
                mimetype="application/vnd.oasis.opendocument.text")


def png_image(seed):
    import struct, zlib
    w = h = 16
    r, g, b = (53 * (seed + 1)) % 256, (101 * (seed + 1)) % 256, (197 * (seed + 1)) % 256
    raw = bytearray()
    for _ in range(h):
        raw.append(0)
        raw.extend(bytes((r, g, b)) * w)
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def make_content(ext, title, paras):
    if ext == "pdf":
        return build_pdf(title, paras)
    if ext == "docx":
        return build_docx(title, paras)
    if ext == "odt":
        return build_odt(title, paras)
    if ext == "csv":
        return ("section,metric,value\nintro,words,1200\nmethods,tables,3\n"
                f"meta,title,{title}\n").encode()
    if ext == "txt":
        return (title + "\n" + "\n".join(paras) + "\n").encode()
    if ext == "png":
        return png_image(len(title))
    if ext == "jpg":
        return JPG_BYTES
    raise ValueError(ext)


# --------------------------------------------------------------------------- #
# baseline data model (8 articles, per panduan section 5.3)                   #
# --------------------------------------------------------------------------- #
USERS = [
    # username, first, last, roles
    ("siteadmin", "Sam", "Admin", ["admin"]),
    ("manager01", "Mira", "Manager", ["manager"]),
    ("editor01", "Edi", "Editor", ["editor"]),
    ("editor02", "Sek", "Sectioneditor", ["section_editor"]),
    ("reviewer01", "Rev", "Onewer", ["reviewer"]),
    ("reviewer02", "Rini", "Twower", ["reviewer"]),
    ("author01", "Ari", "Authorone", ["author"]),
    ("author02", "Bayu", "Authortwo", ["author"]),
    ("author03", "Cinta", "Authorthree", ["author"]),
    ("author04", "Dito", "Authorfour", ["author"]),
    ("reader01", "Rian", "Reader", ["reader"]),
]
SECTIONS = [(1, "Artikel", "ART"), (2, "Tinjauan", "REV")]
# (article_id, section_id, submitter_user_id, status, progress, title, files)
# files: list of (stage_int, revision, ext) ; first file becomes submission_file_id
ARTICLES = [
    (1, 1, 7, 1, 0, "A Reproducible Pipeline for Dummy Information Systems",
     [(1, 1, "pdf")]),
    (2, 1, 8, 1, 0, "Peer Review Dynamics in Synthetic Journals",
     [(1, 1, "pdf"), (2, 1, "docx")]),
    (3, 2, 9, 1, 0, "Editorial Decision Modelling: A Review",
     [(1, 1, "pdf"), (3, 1, "docx")]),
    (4, 1, 10, 1, 0, "Copyediting Workflows for Lab Datasets",
     [(1, 1, "pdf"), (4, 1, "odt")]),
    (5, 1, 7, 1, 0, "Layout and Typesetting of Dummy Manuscripts",
     [(1, 1, "pdf"), (5, 1, "pdf")]),
    (6, 1, 8, 3, 0, "A Published Study on Upload Directory Structure",
     [(1, 1, "pdf"), (6, 1, "pdf")]),    # public file = galley
    (7, 2, 9, 1, 0, "Supplementary Data Handling in OJS 2.4",
     [(1, 1, "pdf"), (7, 1, "csv")]),    # supp file
    (8, 1, 10, 1, 0, "Revision Tracking Across Multiple File Versions",
     [(1, 1, "pdf"), (1, 2, "pdf")]),    # revised submission (revision 2)
]
ISSUE_PUBLISHED = dict(issue_id=1, volume=1, number="1", year=2025, published=1,
                       current=1, title="Inaugural Published Issue")
ISSUE_FUTURE = dict(issue_id=2, volume=1, number="2", year=2026, published=0,
                    current=0, title="Future Issue")


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
    cl = ", ".join(f"`{c}`" for c in cols)
    out = [f"-- {table}"]
    for r in rows:
        out.append(f"INSERT INTO `{table}` ({cl}) VALUES (" +
                   ", ".join(q(r.get(c)) for c in cols) + ");")
    return "\n".join(out) + "\n"


def bcrypt_hash(pw):
    p = subprocess.run(["php", "-r", "echo password_hash($argv[1], PASSWORD_BCRYPT);", pw],
                       capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.startswith("$2"):
        return p.stdout.strip()
    # OJS 2.4 default is sha1; provide a documented placeholder if php missing
    sys.stderr.write("WARN: php missing; using sha1 placeholder password hash\n")
    return hashlib.sha1(pw.encode()).hexdigest()


def write_bytes(relpath, data):
    p = FILES / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)


def main():
    pw = bcrypt_hash(LAB_PASSWORD)
    file_records = []        # baseline physical files (db-linked)
    file_id = 0
    article_files_rows = []
    galley_rows = []
    supp_rows = []
    pub_articles = []
    article_rows, article_settings = [], []

    for (aid, sec, submitter, status, progress, title, files) in ARTICLES:
        submission_file_id = None
        seen_fids = {}
        for (stage, rev, ext) in files:
            # same logical file across revisions keeps one file_id
            key = (stage, ext) if stage == 1 else (stage, ext, rev)
            if stage == 1 and ("S1") in seen_fids:
                fid = seen_fids["S1"]
            else:
                file_id += 1
                fid = file_id
                if stage == 1:
                    seen_fids["S1"] = fid
            stage_dir, code = STAGE[stage]
            fname = f"{aid}-{fid}-{rev}-{code}.{ext}"
            rel = f"journals/1/articles/{aid}/{stage_dir}/{fname}"
            paras = [f"Article {aid} ({code}) - synthetic lab content.",
                     "This file was produced for a non-production OJS 2.4.8-4 SAST dataset."]
            sha, size = write_bytes(rel, make_content(ext, title, paras))
            if stage == 1 and submission_file_id is None:
                submission_file_id = fid
            article_files_rows.append({
                "file_id": fid, "revision": rev, "article_id": aid,
                "file_name": fname, "file_type": EXT_MIME[ext], "file_size": size,
                "original_file_name": f"{code.lower()}-a{aid:03d}.{ext}",
                "file_stage": stage, "viewable": 1 if stage == 6 else 0,
                "date_uploaded": TS, "date_modified": TS, "round": 1,
            })
            file_records.append({
                "logical": f"F-{len(file_records)+1:03d}", "rel": rel, "article_id": aid,
                "issue_id": "", "file_id": fid, "revision": rev,
                "stage_name": {1: "submission", 2: "review", 3: "editor", 4: "copyedit",
                               5: "layout", 6: "public", 7: "supp", 8: "note",
                               9: "attachment"}[stage],
                "db_linked": "true", "orig": f"{code.lower()}-a{aid:03d}.{ext}",
                "mime": EXT_MIME[ext], "sha": sha, "size": size, "klass": "normal",
            })
            if stage == 6:   # public file used as galley for the published article
                galley_rows.append({"galley_id": len(galley_rows) + 1, "locale": LOCALE,
                                    "article_id": aid, "file_id": fid, "label": "PDF",
                                    "html_galley": 0, "seq": 1})
            if stage == 7:   # supplementary file link
                supp_rows.append({"supp_id": len(supp_rows) + 1, "file_id": fid,
                                  "article_id": aid, "type": "", "language": LOCALE,
                                  "date_created": TS.split()[0], "show_reviewers": 1,
                                  "date_submitted": TS, "seq": 1})

        article_rows.append({
            "article_id": aid, "locale": LOCALE, "user_id": submitter,
            "journal_id": JOURNAL_ID, "section_id": sec, "language": "en",
            "date_submitted": TS, "last_modified": TS, "date_status_modified": TS,
            "status": status, "submission_progress": progress, "current_round": 1,
            "submission_file_id": submission_file_id, "pages": f"{aid}-{aid+9}",
            "fast_tracked": 0, "hide_author": 0, "comments_status": 0,
        })
        article_settings.append({"article_id": aid, "locale": LOCALE,
                                 "setting_name": "title", "setting_value": title,
                                 "setting_type": "string"})
        article_settings.append({"article_id": aid, "locale": LOCALE,
                                 "setting_name": "abstract",
                                 "setting_value": f"<p>Synthetic abstract for article {aid}.</p>",
                                 "setting_type": "string"})
        if status == 3:
            pub_articles.append({"published_article_id": len(pub_articles) + 1,
                                 "article_id": aid, "issue_id": ISSUE_PUBLISHED["issue_id"],
                                 "date_published": TS, "seq": aid, "access_status": 1})

    # issue cover (issue_files) -> journals/1/issues/1/public/
    cover_rel = "journals/1/issues/1/public/1-1-PB.jpg"
    cp = FILES / cover_rel
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_bytes(JPG_BYTES)
    cover_sha = hashlib.sha256(JPG_BYTES).hexdigest()
    issue_files_rows = [{"file_id": 1, "issue_id": 1, "file_name": "1-1-PB.jpg",
                         "file_type": "image/jpeg", "file_size": len(JPG_BYTES),
                         "original_file_name": "cover-issue-1.jpg", "content_type": 1,
                         "date_uploaded": TS, "date_modified": TS}]
    file_records.append({"logical": f"F-{len(file_records)+1:03d}", "rel": cover_rel,
                         "article_id": "", "issue_id": 1, "file_id": 1, "revision": 1,
                         "stage_name": "issue_public", "db_linked": "true",
                         "orig": "cover-issue-1.jpg", "mime": "image/jpeg",
                         "sha": cover_sha, "size": len(JPG_BYTES), "klass": "normal"})

    # public journal asset (logo) -> mysql/public/journals/1/
    logo = png_image(7)
    lp = PUBLIC / "journals/1/logo_jdis.png"
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_bytes(logo)

    sql = build_sql(pw, article_rows, article_settings, article_files_rows,
                    galley_rows, supp_rows, pub_articles, issue_files_rows)
    (MYSQL / "database.sql").write_text(sql)

    write_overlays_and_oracle(file_records)
    write_entity_inventory()
    write_manifest()

    print("Built OJS 2.4.8-4 baseline:")
    print(f"  articles            : {len(ARTICLES)}")
    print(f"  baseline files (db) : {len(file_records)}")
    print(f"  galleys             : {len(galley_rows)}")
    print(f"  supplementary files : {len(supp_rows)}")
    print(f"  database_sql_sha256 : {hashlib.sha256(sql.encode()).hexdigest()}")


def build_sql(pw, article_rows, article_settings, af_rows, galley_rows,
              supp_rows, pub_articles, issue_files_rows):
    L = ["-- OJS 2.4.8-4 upload-directory SAST dataset — data-only baseline seed.",
         "-- Generated %s. Benign content only; INERT scenario artifacts live in" % NOW,
         "-- scenarios/*/overlay-files and are NOT part of this baseline.",
         "--",
         "-- Apply on a freshly-installed OJS 2.4.8-4 schema (or the reference schema",
         "-- in scripts/lib/schema_to_mysql.py). Does not create tables or touch source.",
         "SET NAMES utf8;", "SET FOREIGN_KEY_CHECKS=0;", "START TRANSACTION;", ""]
    A = L.append

    A(insert("journals", ["journal_id", "path", "seq", "primary_locale", "enabled"],
             [{"journal_id": JOURNAL_ID, "path": JOURNAL_PATH, "seq": 1,
               "primary_locale": LOCALE, "enabled": 1}]))
    A(insert("journal_settings", ["journal_id", "locale", "setting_name", "setting_value", "setting_type"], [
        {"journal_id": JOURNAL_ID, "locale": LOCALE, "setting_name": "title",
         "setting_value": "Journal of Dummy Information Systems", "setting_type": "string"},
        {"journal_id": JOURNAL_ID, "locale": LOCALE, "setting_name": "publisherInstitution",
         "setting_value": "Laboratory Publisher", "setting_type": "string"},
        {"journal_id": JOURNAL_ID, "locale": "", "setting_name": "onlineIssn",
         "setting_value": "2789-0000", "setting_type": "string"},
        {"journal_id": JOURNAL_ID, "locale": "", "setting_name": "supportedLocales",
         "setting_value": 'a:1:{i:0;s:5:"%s";}' % LOCALE, "setting_type": "object"},
    ]))

    # users + roles
    user_rows, user_settings, role_rows = [], [], []
    for i, (uname, first, last, roles) in enumerate(USERS, start=1):
        user_rows.append({"user_id": i, "username": uname, "password": pw,
                          "first_name": first, "last_name": last,
                          "email": f"{uname}@example.invalid",
                          "date_registered": TS, "date_last_login": TS,
                          "disabled": 0, "must_change_password": 1, "inline_help": 1})
        for r in roles:
            jid = 0 if r == "admin" else JOURNAL_ID
            role_rows.append({"journal_id": jid, "user_id": i, "role_id": ROLE[r]})
    A(insert("users", ["user_id", "username", "password", "first_name", "last_name",
                       "email", "date_registered", "date_last_login", "disabled",
                       "must_change_password", "inline_help"], user_rows))
    A(insert("roles", ["journal_id", "user_id", "role_id"], role_rows))

    # sections
    sec_rows, sec_settings = [], []
    for (sid, title, abbrev) in SECTIONS:
        sec_rows.append({"section_id": sid, "journal_id": JOURNAL_ID, "seq": sid,
                         "editor_restricted": 0, "meta_indexed": 1, "meta_reviewed": 1,
                         "abstracts_not_required": 0, "hide_title": 0, "hide_author": 0,
                         "hide_about": 0, "disable_comments": 0})
        sec_settings += [
            {"section_id": sid, "locale": LOCALE, "setting_name": "title",
             "setting_value": title, "setting_type": "string"},
            {"section_id": sid, "locale": LOCALE, "setting_name": "abbrev",
             "setting_value": abbrev, "setting_type": "string"}]
    A(insert("sections", ["section_id", "journal_id", "seq", "editor_restricted",
                          "meta_indexed", "meta_reviewed", "abstracts_not_required",
                          "hide_title", "hide_author", "hide_about", "disable_comments"], sec_rows))
    A(insert("section_settings", ["section_id", "locale", "setting_name", "setting_value", "setting_type"], sec_settings))

    # issues
    issue_rows, issue_settings = [], []
    for iss in (ISSUE_PUBLISHED, ISSUE_FUTURE):
        issue_rows.append({"issue_id": iss["issue_id"], "journal_id": JOURNAL_ID,
                           "volume": iss["volume"], "number": iss["number"],
                           "year": iss["year"], "published": iss["published"],
                           "current": iss["current"],
                           "date_published": TS if iss["published"] else None,
                           "access_status": 1, "show_volume": 1, "show_number": 1,
                           "show_year": 1, "show_title": 1})
        issue_settings.append({"issue_id": iss["issue_id"], "locale": LOCALE,
                               "setting_name": "title", "setting_value": iss["title"],
                               "setting_type": "string"})
    A(insert("issues", ["issue_id", "journal_id", "volume", "number", "year",
                        "published", "current", "date_published", "access_status",
                        "show_volume", "show_number", "show_year", "show_title"], issue_rows))
    A(insert("issue_settings", ["issue_id", "locale", "setting_name", "setting_value", "setting_type"], issue_settings))
    A(insert("issue_files", ["file_id", "issue_id", "file_name", "file_type", "file_size",
                            "original_file_name", "content_type", "date_uploaded", "date_modified"],
             issue_files_rows))

    A(insert("articles", ["article_id", "locale", "user_id", "journal_id", "section_id",
                         "language", "date_submitted", "last_modified", "date_status_modified",
                         "status", "submission_progress", "current_round", "submission_file_id",
                         "pages", "fast_tracked", "hide_author", "comments_status"], article_rows))
    A(insert("article_settings", ["article_id", "locale", "setting_name", "setting_value", "setting_type"], article_settings))
    A(insert("article_files", ["file_id", "revision", "article_id", "file_name", "file_type",
                              "file_size", "original_file_name", "file_stage", "viewable",
                              "date_uploaded", "date_modified", "round"], af_rows))
    A(insert("article_supplementary_files", ["supp_id", "file_id", "article_id", "type",
                                            "language", "date_created", "show_reviewers",
                                            "date_submitted", "seq"], supp_rows))
    A(insert("article_galleys", ["galley_id", "locale", "article_id", "file_id", "label",
                                "html_galley", "seq"], galley_rows))
    A(insert("published_articles", ["published_article_id", "article_id", "issue_id",
                                   "date_published", "seq", "access_status"], pub_articles))
    A("COMMIT;")
    A("SET FOREIGN_KEY_CHECKS=1;")
    A("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# scenario overlays + oracle                                                  #
# --------------------------------------------------------------------------- #
def _inert_marker(oracle_id, note):
    return (f"OJS-2.4.8-4-SAST-LAB-INERT-ARTIFACT:{oracle_id}\n"
            f"{note}\n"
            "This file is INERT: plain text only. No code, no server-side tags,\n"
            "no executable instructions. It exists so a scanner can be evaluated\n"
            "on NAME / EXTENSION / LOCATION signals at an OJS upload path.\n").encode()


# compromised positives: (oracle_id, relative_path, rule_family, severity, rationale)
POSITIVES = [
    ("OR-101", "journals/1/articles/6/public/6-901-1-PB.phtml",
     "dangerous_extension", "high",
     "Risky server-parsed extension (.phtml) placed in an article upload dir; inert."),
    ("OR-102", "journals/1/articles/1/submission/original/manuscript.pdf.exe",
     "dangerous_extension", "high",
     "Double extension ending in .exe in the submission dir; inert."),
    ("OR-103", "journals/1/articles/7/supp/dataset-helper.jsp",
     "dangerous_extension", "medium",
     "Orphan .jsp (no DB metadata) in supplementary dir; inert."),
    ("OR-104", "journals/1/articles/2/submission/review/notes.phar",
     "dangerous_extension", "medium",
     "PHP archive extension (.phar) in review dir; inert, not DB-linked."),
]
# controller (negative lookalikes): (oracle_id, relative_path, rationale)
CONTROLLERS = [
    ("OR-201", "journals/1/articles/3/submission/editor/php-coding-guidelines.txt",
     "Filename contains the token 'php' but extension is .txt; must NOT alert."),
    ("OR-202", "journals/1/articles/5/submission/layout/figure-final.pdf",
     "Adjacent benign PDF not in baseline DB; correct extension/content, must NOT alert."),
    ("OR-203", "journals/1/articles/7/supp/measurements-2.csv",
     "Extra benign CSV next to a real supplementary file; must NOT alert."),
]


def write_overlays_and_oracle(file_records):
    # write overlay artifacts
    pos_hashes, ctrl_hashes = {}, {}
    for (oid, rel, fam, sev, why) in POSITIVES:
        p = SCEN / "compromised" / "overlay-files" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = _inert_marker(oid, why)
        p.write_bytes(data)
        pos_hashes[oid] = (rel, hashlib.sha256(data).hexdigest(), len(data), fam, sev, why)
    for (oid, rel, why) in CONTROLLERS:
        p = SCEN / "controller" / "overlay-files" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        # controllers are benign real files (pdf/csv/txt) by extension
        ext = rel.rsplit(".", 1)[-1]
        data = make_content(ext, "Controller artifact", [why]) if ext in EXT_MIME \
            else _inert_marker(oid, why)
        p.write_bytes(data)
        ctrl_hashes[oid] = (rel, hashlib.sha256(data).hexdigest(), len(data), why)

    # clean overlay: intentionally empty (.gitkeep)
    (SCEN / "clean" / "overlay-files" / ".gitkeep").write_text("")

    # profile.yaml files
    (SCEN / "clean" / "profile.yaml").write_text(
        "profile: clean\nbase_profile: baseline\nexpected_positive_objects: 0\noverlay_action: none\n")
    (SCEN / "controller" / "profile.yaml").write_text(
        "profile: controller\nbase_profile: baseline\n"
        f"expected_positive_objects: 0\noverlay_root: overlay-files\n"
        f"control_objects: {len(CONTROLLERS)}\n")
    (SCEN / "compromised" / "profile.yaml").write_text(
        "profile: compromised\nbase_profile: baseline\n"
        f"expected_positive_objects: {len(POSITIVES)}\noverlay_root: overlay-files\n"
        "safety:\n  executable_content: false\n  web_root_placement: false\n"
        "  runtime_execution: prohibited\n")

    # file-inventory.csv (baseline db-linked files)
    GT.mkdir(parents=True, exist_ok=True)
    with open(GT / "file-inventory.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["profile", "logical_file_id", "relative_path", "article_id",
                    "issue_id", "file_id", "revision", "file_stage", "db_linked",
                    "original_filename", "mime_type", "sha256", "expected_class"])
        for r in file_records:
            w.writerow(["baseline", r["logical"], r["rel"], r["article_id"], r["issue_id"],
                        r["file_id"], r["revision"], r["stage_name"], r["db_linked"],
                        r["orig"], r["mime"], r["sha"], r["klass"]])

    # upload-oracle.csv
    with open(GT / "upload-oracle.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario_id", "profile", "oracle_id", "relative_path",
                    "artifact_origin", "db_linked", "expected_detection",
                    "expected_rule_family", "severity_expectation", "sha256", "rationale"])
        # baseline negatives (appear in clean, controller, compromised)
        neg_i = 0
        for r in file_records:
            neg_i += 1
            w.writerow([f"UPL-NEG-{neg_i:03d}", "clean", f"ORN-{neg_i:03d}", r["rel"],
                        "ojs_workflow", r["db_linked"], "no", "none", "none", r["sha"],
                        "Normal OJS workflow file"])
        for oid, (rel, sha, sz, why) in ctrl_hashes.items():
            w.writerow([f"UPL-CTRL-{oid[-3:]}", "controller", oid, rel, "test_control",
                        "false", "no", "none", "none", sha, why])
        for oid, (rel, sha, sz, fam, sev, why) in pos_hashes.items():
            w.writerow([f"UPL-POS-{oid[-3:]}", "compromised", oid, rel, "scenario_overlay",
                        "false", "yes", fam, sev, sha, why])

    # expected-findings JSONs
    (GT / "expected-findings-clean.json").write_text(json.dumps({
        "profile": "clean", "expected_positive_objects": 0,
        "expected_alert_oracle_ids": [], "note": "Negative corpus; measures false positives."
    }, indent=2) + "\n")
    (GT / "expected-findings-compromised.json").write_text(json.dumps({
        "profile": "compromised",
        "expected_positive_objects": len(POSITIVES),
        "expected_alert_oracle_ids": [oid for (oid, *_rest) in POSITIVES],
        "expected_rule_families": sorted({p[2] for p in POSITIVES}),
        "must_not_alert_oracle_ids": [c[0] for c in CONTROLLERS],
        "note": "Positives are inert; detection must rest on name/extension/location."
    }, indent=2) + "\n")

    # per-profile hash manifests
    _hash_tree(FILES, GT / "sha256sums-baseline.txt")
    _hash_tree(FILES, GT / "sha256sums.txt")
    _hash_tree(SCEN / "controller" / "overlay-files", GT / "sha256sums-controller.txt")
    _hash_tree(SCEN / "compromised" / "overlay-files", GT / "sha256sums-compromised.txt")
    (GT / "sha256sums-clean.txt").write_text("")


def _hash_tree(root, out):
    lines = []
    if root.exists():
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(root)
                lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel}")
    out.write_text("\n".join(lines) + ("\n" if lines else ""))


def write_entity_inventory():
    with open(GT / "entity-inventory.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["entity_type", "logical_id", "db_id", "parent_id", "status", "description"])
        w.writerow(["journal", "J-001", 1, "", "active", "Journal of Dummy Information Systems"])
        for (sid, title, _ab) in SECTIONS:
            w.writerow(["section", f"S-{sid:03d}", sid, 1, "active", title])
        w.writerow(["issue", "I-001", 1, 1, "published", ISSUE_PUBLISHED["title"]])
        w.writerow(["issue", "I-002", 2, 1, "future", ISSUE_FUTURE["title"]])
        status_name = {1: "queued", 3: "published"}
        for (aid, sec, sub, status, prog, title, files) in ARTICLES:
            w.writerow(["article", f"A-{aid:03d}", aid, 1, status_name.get(status, "queued"), title])


def write_manifest():
    db_sha = hashlib.sha256((MYSQL / "database.sql").read_bytes()).hexdigest()
    txt = f"""dataset:
  id: ojs-2.4.8-4-upload-lab-v1
  application: ojs
  application_version: "2.4.8-4"
  database_engine: mysql
  build_profile: baseline
  created_at: "{NOW}"

runtime_contract:
  files_dir_relative_root: mysql/files
  public_files_dir_relative_root: mysql/public
  source_code_included: false
  source_code_mutation_allowed: false

journal:
  journal_id: 1
  path: {JOURNAL_PATH}
  title: Journal of Dummy Information Systems

integrity:
  hash_algorithm: sha256
  file_inventory: ground-truth/file-inventory.csv
  hash_manifest: ground-truth/sha256sums.txt
  database_sql_sha256: {db_sha}

profiles:
  clean:
    base: baseline
    overlay: scenarios/clean/overlay-files
    expected_positive_objects: 0
  controller:
    base: baseline
    overlay: scenarios/controller/overlay-files
    expected_positive_objects: 0
  compromised:
    base: baseline
    overlay: scenarios/compromised/overlay-files
    expected_positive_objects: {len(POSITIVES)}
"""
    (GT / "dataset-manifest.yaml").write_text(txt)


if __name__ == "__main__":
    main()
