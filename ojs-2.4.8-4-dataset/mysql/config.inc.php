; <?php exit; ?>
; OJS 2.4.8-4 — SANITIZED config template for the dataset.
;
; This is NOT the runtime config. It carries no real credentials. On restore,
; the operator supplies their own lab database connection and base_url, and
; replaces the files_dir placeholder with their real private path.
;
; The dataset never ships the live config.inc.php verbatim (panduan 8.6).

[general]
installed = On
base_url = "http://localhost/ojs-248"

[database]
driver = mysql
host = __DATASET_DB_HOST__
username = __DATASET_DB_USER__
password = __DATASET_DB_PASSWORD__
name = __DATASET_DB_NAME__

[files]
; Must point OUTSIDE the web root on the lab host (panduan 6).
files_dir = "__DATASET_FILES_DIR__"
public_files_dir = "public"

[security]
; OJS 2.4.8-4 default is sha1; this dataset's generator uses bcrypt when PHP is
; available. Set to match your installed OJS encryption setting before login.
encryption = sha1
