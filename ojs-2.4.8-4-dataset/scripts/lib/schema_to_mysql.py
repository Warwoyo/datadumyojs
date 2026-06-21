#!/usr/bin/env python3
"""
Convert the OJS 2.4.8-4 ADODB XMLSchema definitions into MySQL CREATE TABLE
DDL, for the subset of tables the baseline seed populates.

This produces a *reference* schema used to import/verify the seed in a lab
MariaDB. It is NOT a replacement for the real OJS installer; on a live lab box
the operator installs OJS 2.4.8-4 normally (per the panduan) and the seed data
lands in the installer-created tables. The column definitions here are taken
verbatim from the source tag `ojs-2_4_8-4`:
  - dbscripts/xml/ojs_schema.xml         (OJS tables)
  - lib/pkp/xml/schema/common.xml        (shared tables: users, site, ...)
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ADODB type -> MySQL type. size applied for C/C2.
TYPEMAP = {
    "I1": "TINYINT", "I2": "SMALLINT", "I4": "INT", "I8": "BIGINT",
    "F": "FLOAT", "D": "DATE", "T": "DATETIME", "X": "TEXT",
}


def col_sql(field):
    name = field.get("name")
    typ = field.get("type")
    size = field.get("size")
    if typ in ("C", "C2"):
        mysql = f"VARCHAR({size or 255})"
    else:
        mysql = TYPEMAP.get(typ)
        if mysql is None:
            raise ValueError(f"unmapped type {typ} for {name}")
    notnull = field.find("NOTNULL") is not None
    autoinc = field.find("AUTOINCREMENT") is not None
    is_key = field.find("KEY") is not None
    default = field.find("DEFAULT")
    parts = [f"`{name}`", mysql]
    # text columns can't carry a literal default in older MySQL; skip if TEXT
    if notnull:
        parts.append("NOT NULL")
    if default is not None and mysql != "TEXT":
        val = default.get("VALUE")
        parts.append(f"DEFAULT '{val}'")
    if autoinc:
        parts.append("AUTO_INCREMENT")
    return " ".join(parts), is_key, autoinc


def table_sql(table):
    name = table.get("name")
    cols, keys = [], []
    for field in table.findall("field"):
        sql, is_key, _ = col_sql(field)
        cols.append("  " + sql)
        if is_key:
            keys.append(field.get("name"))
    if keys:
        cols.append("  PRIMARY KEY (" + ", ".join(f"`{k}`" for k in keys) + ")")
    body = ",\n".join(cols)
    return (f"DROP TABLE IF EXISTS `{name}`;\n"
            f"CREATE TABLE `{name}` (\n{body}\n) "
            f"ENGINE=InnoDB DEFAULT CHARSET=utf8;\n")


def load_tables(xml_path):
    root = ET.parse(xml_path).getroot()
    return {t.get("name"): t for t in root.iter("table")}


def main():
    wanted = sys.argv[1:]
    tables = {}
    tables.update(load_tables(HERE / "pkp_common_schema.xml"))
    tables.update(load_tables(HERE / "ojs_schema.xml"))
    out = ["-- OJS 2.4.8-4 reference schema (subset), generated from ADODB XMLSchema.",
           "-- Source tag: ojs-2_4_8-4. For lab import/verify of the dataset seed.",
           "SET NAMES utf8;", "SET FOREIGN_KEY_CHECKS=0;", ""]
    for name in wanted:
        if name not in tables:
            sys.stderr.write(f"WARN: table {name} not found in schema XML\n")
            continue
        out.append(table_sql(tables[name]))
    out.append("SET FOREIGN_KEY_CHECKS=1;")
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()
