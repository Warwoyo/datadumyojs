# Panduan Teknis Pembuatan Dataset Dummy OJS 2.4.8-4 untuk Pengujian SAST

> **Status:** Blueprint implementasi  
> **Target aplikasi:** Open Journal Systems (OJS) `2.4.8-4`  
> **DBMS target:** MySQL/MariaDB  
> **Fokus eksperimen:** snapshot data dummy yang dapat dipulihkan ulang, dengan skenario evaluasi **pemindaian direktori unggahan** (*upload directory scanning*)  
> **Prinsip:** seluruh data bersifat dummy, tidak mengubah source code OJS, dan tidak memasukkan payload yang dapat dieksekusi.

---

## 1. Tujuan

Dokumen ini menjelaskan cara membangun **dataset dummy OJS 2.4.8-4** yang memiliki pola seperti repositori `pkp/datasets`, tetapi diperluas agar layak dipakai sebagai korpus eksperimen SAST.

Dataset hasil akhir harus memungkinkan peneliti untuk:

1. memulihkan (*restore*) OJS 2.4.8-4 ke kondisi data yang konsisten;
2. menyediakan jurnal, pengguna, issue, artikel, alur editorial, dan file upload yang realistis;
3. memisahkan file OJS yang sah dari artefak pengujian SAST;
4. menjalankan profil `clean` dan `compromised` secara berulang tanpa mengubah baseline;
5. membuktikan setiap status file melalui manifest dan hash;
6. mengevaluasi scanner pada direktori unggahan yang sesuai dengan struktur asli OJS 2.4.

Dokumen ini tidak bertujuan membuat eksploit aktif, shell, backdoor, atau file yang dapat dijalankan. Artefak skenario keamanan harus bersifat **inert**: tidak memiliki instruksi executable, tidak memiliki tag kode server-side, dan tidak digunakan untuk memperoleh akses ke sistem.

---

## 2. Dasar arsitektur yang menentukan desain dataset

### 2.1. Konvensi dataset PKP

Repositori `pkp/datasets` menata setiap dataset berdasarkan aplikasi, tag/branch, dan DBMS. Isi inti sebuah dataset biasanya terdiri dari:

```text
database.sql
config.inc.php
public/
files/
```

Untuk OJS 2.4.8-4, format ini tetap dipakai agar struktur dataset mudah dipahami dan dipulihkan.

### 2.2. Karakteristik penting OJS 2.4.8-4

OJS 2.4 menggunakan istilah dan struktur internal yang berbeda dari OJS 3.x.

| Aspek | OJS 2.4.8-4 | Implikasi untuk dataset |
|---|---|---|
| Objek submission | `articles` | Satu submission direpresentasikan sebagai artikel dengan `article_id`. |
| Lokasi file artikel | `files_dir/journals/<journal_id>/articles/<article_id>/...` | Direktori upload harus dibangun mengikuti `article_id`, bukan struktur OJS 3.x. |
| Tahap file editorial | submission, review, editor, copyedit, layout, supplementary, public, note, attachment | Dataset perlu memiliki file normal pada beberapa tahap agar representatif. |
| File issue | `files_dir/journals/<journal_id>/issues/<issue_id>/public/` | Cover atau file issue tidak dicampur dengan file artikel. |
| Aset publik jurnal | `public_files_dir/journals/<journal_id>/` | Logo jurnal dan aset web-visible dipisahkan dari private `files_dir`. |
| Metadata file | database `article_files` dan file fisik | File dan database harus selalu konsisten. |
| Publikasi artikel | tabel `published_articles` | Artikel yang sudah terbit perlu memiliki relasi ke issue, bukan hanya status artikel. |

### 2.3. Struktur file aktual yang harus dipatuhi

OJS 2.4 membangun root file artikel sebagai berikut:

```text
<files_dir>/
└── journals/
    └── <journal_id>/
        └── articles/
            └── <article_id>/
```

Di bawah root artikel tersebut, lokasi file ditentukan oleh tahap file:

```text
articles/<article_id>/
├── submission/
│   ├── original/
│   ├── review/
│   ├── editor/
│   ├── copyedit/
│   └── layout/
├── public/
├── supp/
├── note/
└── attachment/
```

Nama file fisik dibentuk OJS dari identitas artikel, file, revisi, dan singkatan tahap:

```text
<article_id>-<file_id>-<revision>-<stage>.<extension>
```

Contoh format:

```text
12-45-1-SM.pdf
12-46-1-RV.docx
12-47-1-ED.docx
12-48-1-CE.odt
12-49-1-LE.pdf
12-50-1-SP.csv
```

Kode tahap file:

| Tahap | Direktori relatif | Kode nama file |
|---|---|---|
| Submission original | `submission/original` | `SM` |
| Review | `submission/review` | `RV` |
| Editor decision | `submission/editor` | `ED` |
| Copyedit | `submission/copyedit` | `CE` |
| Layout | `submission/layout` | `LE` |
| Public | `public` | `PB` |
| Supplementary | `supp` | `SP` |
| Note | `note` | `NT` |
| Attachment | `attachment` | `AT` |

> **Aturan utama:** jangan membuat sendiri nama file, `file_id`, atau metadata `article_files` secara manual sebelum baseline terbentuk. Buat submission dan upload melalui workflow OJS sehingga aplikasi menghasilkan struktur dan relasi yang benar; setelah itu baru ekspor snapshot.

---

## 3. Batasan, asumsi, dan guardrail

### 3.1. Batasan lingkungan

- Dataset dibuat untuk **OJS 2.4.8-4**, bukan 2.4.8 generik dan bukan OJS 3.x.
- Instalasi legacy harus ditempatkan pada jaringan lab terisolasi.
- Jangan mengekspos instalasi OJS 2.4.8-4 ke internet publik.
- Gunakan pengguna, surel, nama organisasi, artikel, dan berkas yang seluruhnya dummy.
- Jangan menyimpan kredensial produksi, token, private key, data mahasiswa, atau dokumen nyata.

### 3.2. Larangan implementasi

Agen atau operator **tidak boleh**:

- mengubah source code OJS agar dataset dapat dibuat;
- membangun file skenario dengan isi executable atau instruksi server-side;
- menaruh file skenario ke web root;
- menjalankan artefak skenario melalui browser atau PHP-FPM;
- menyisipkan file positif ke baseline;
- mengedit `database.sql` untuk mengakali relasi OJS tanpa verifikasi pada aplikasi;
- menggunakan data riil dari jurnal atau pengguna nyata.

### 3.3. Definisi profil

| Profil | Tujuan | Isi |
|---|---|---|
| `baseline` | Snapshot kanonik yang dapat dipulihkan | OJS dummy yang konsisten, hanya file normal dan kontrol negatif. |
| `clean` | Kondisi pengujian tanpa indikator kompromi | Salinan `baseline`; tidak memiliki artefak positif. |
| `compromised` | Kondisi pengujian detector | Salinan `baseline` + overlay artefak inert yang telah didefinisikan oracle. |
| `controller` | Pembanding/negative control | File yang mirip secara nama atau lokasi tetapi secara oracle tidak perlu memicu rule tertentu. |

---

## 4. Kontrak artefak dataset

Dataset dianggap selesai hanya apabila seluruh artefak berikut ada dan lolos verifikasi.

```text
ojs-2.4.8-4-dataset/
├── README.md
├── VERSION
├── mysql/
│   ├── database.sql
│   ├── config.inc.php
│   ├── public/
│   │   └── journals/
│   │       └── 1/
│   └── files/
│       └── journals/
│           └── 1/
│               ├── articles/
│               └── issues/
│
├── ground-truth/
│   ├── dataset-manifest.yaml
│   ├── entity-inventory.csv
│   ├── upload-oracle.csv
│   ├── file-inventory.csv
│   ├── expected-findings-clean.json
│   ├── expected-findings-compromised.json
│   └── sha256sums.txt
│
├── scenarios/
│   ├── clean/
│   │   ├── overlay-files/
│   │   └── profile.yaml
│   ├── compromised/
│   │   ├── overlay-files/
│   │   └── profile.yaml
│   └── controller/
│       ├── overlay-files/
│       └── profile.yaml
│
├── scripts/
│   ├── export-snapshot.sh
│   ├── restore-baseline.sh
│   ├── apply-profile.sh
│   ├── verify-dataset.sh
│   ├── generate-manifest.py
│   └── collect-evidence.sh
│
├── evidence/
│   └── README.md
│
└── docs/
    ├── architecture-ojs-2.4.8-4.md
    ├── build-log-template.md
    └── scenario-catalog.md
```

### 4.1. Kompatibilitas dengan pola PKP

Bagian yang bersifat kompatibel dengan pola dataset PKP berada di:

```text
mysql/database.sql
mysql/config.inc.php
mysql/public/
mysql/files/
```

Bagian tambahan penelitian berada di:

```text
ground-truth/
scenarios/
scripts/
evidence/
docs/
```

Dengan pemisahan ini, snapshot OJS tetap dapat dipulihkan seperti dataset aplikasi biasa, sedangkan data evaluasi SAST tetap terorganisasi dan tidak mengotori snapshot dasar.

---

## 5. Model entitas dummy

### 5.1. Objek yang wajib ada

Dataset minimum yang layak untuk eksperimen harus memiliki:

| Kelompok | Minimal | Alasan |
|---|---:|---|
| Site administrator | 1 | Memastikan konteks tingkat situs ada. |
| Journal manager | 1 | Mengelola jurnal, section, dan issue. |
| Editor / section editor | 2 | Mewakili alur keputusan editorial. |
| Reviewer | 2 | Mewakili tahap peer review. |
| Author | 4 | Memungkinkan beberapa submission. |
| Reader | 1 | Akun dummy tingkat pembaca. |
| Journal | 1 | Target utama dataset. |
| Section | 2 | Misalnya `Artikel` dan `Tinjauan`. |
| Issue terbit | 1 | Menguji artikel published dan galley publik. |
| Issue belum terbit | 1 | Menguji keadaan draft/future issue. |
| Submission/article | 8 | Mewakili tahapan editorial dan variasi file. |
| File normal | ≥ 15 | Korpus kontrol negatif dan workflow file. |

### 5.2. Identitas dummy yang disarankan

Gunakan informasi yang jelas dummy dan tidak menyerupai orang nyata.

```text
Journal title : Journal of Dummy Information Systems
Journal path  : jdis
Publisher     : Laboratory Publisher
Email domain  : example.invalid
```

Contoh akun:

| Username | Role utama | Surel dummy |
|---|---|---|
| `siteadmin` | Site administrator | `siteadmin@example.invalid` |
| `manager01` | Journal manager | `manager01@example.invalid` |
| `editor01` | Editor | `editor01@example.invalid` |
| `editor02` | Section editor | `editor02@example.invalid` |
| `reviewer01` | Reviewer | `reviewer01@example.invalid` |
| `reviewer02` | Reviewer | `reviewer02@example.invalid` |
| `author01`–`author04` | Author | `authorNN@example.invalid` |
| `reader01` | Reader | `reader01@example.invalid` |

Kredensial dapat dibuat dummy, namun jangan menyimpan kata sandi plaintext di repositori. Simpan hanya prosedur pembuatan akun atau gunakan password sementara yang diganti setelah restore lokal.

### 5.3. Matriks submission

Buat data melalui UI OJS agar tabel seperti `articles`, `article_settings`, `authors`, `article_files`, `editing_assignments`, serta relasi workflow diisi oleh aplikasi.

| ID logis | Status target | Tahap yang harus tampak | File utama |
|---|---|---|---|
| `A-001` | submission awal | original submission | PDF |
| `A-002` | dalam review | original + review | DOCX/PDF |
| `A-003` | keputusan editor | editor decision | DOCX |
| `A-004` | copyedit | copyedit | ODT/DOCX |
| `A-005` | layout | layout + galley | PDF |
| `A-006` | published | issue + galley publik | PDF/HTML metadata |
| `A-007` | memiliki supplementary file | supplementary | CSV/TXT |
| `A-008` | revisi | revisi file lebih dari satu | PDF/DOCX |

### 5.4. Jenis file normal

Gunakan file kecil buatan sendiri, bukan karya berhak cipta atau dokumen sungguhan.

| Kategori | Contoh ekstensi | Peran |
|---|---|---|
| Manuskrip | `.pdf`, `.docx`, `.odt` | File submission dan layout. |
| Data pendukung | `.csv`, `.txt` | Supplementary file. |
| Gambar | `.png`, `.jpg` | Cover issue atau aset publik. |
| Metadata | `.xml` yang valid dan non-eksekusi | Hanya bila workflow atau plugin lab membutuhkannya. |
| Aset desain | `.css`, `.svg` statis | Hanya pada `public/` jika diperlukan. |

> Jangan menganggap file normal hanya PDF. Korpus harus mencakup beberapa ekstensi yang sah agar scanner diuji terhadap variasi nyata.

---

## 6. Arsitektur penyimpanan: database, `files_dir`, dan `public`

### 6.1. Tiga komponen yang tidak boleh dipisahkan

```text
                         Snapshot OJS 2.4.8-4
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  1. MySQL/MariaDB                  2. private files_dir          │
│  ┌────────────────────┐           ┌───────────────────────────┐ │
│  │ users              │           │ journals/1/articles/...   │ │
│  │ roles              │           │ journals/1/issues/...     │ │
│  │ journals           │           └───────────────────────────┘ │
│  │ sections           │                                          │
│  │ issues             │           3. public_files_dir            │
│  │ articles           │           ┌───────────────────────────┐ │
│  │ article_files      │           │ public/journals/1/...     │ │
│  │ published_articles │           └───────────────────────────┘ │
│  └────────────────────┘                                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

Dataset tidak valid apabila salah satu komponen berikut hilang:

1. database memiliki metadata file tetapi file fisik tidak ada;
2. file fisik ada tetapi tidak dapat dipetakan ke metadata file yang sah;
3. `config.inc.php` menunjuk ke lokasi yang berbeda dari file snapshot;
4. artikel published tidak memiliki relasi publication/issue yang konsisten;
5. file `public` tercampur ke dalam private `files_dir` tanpa alasan workflow.

### 6.2. Struktur root yang direkomendasikan di host lab

Contoh pada host laboratorium:

```text
/var/www/ojs-248/                  # source aplikasi OJS, tidak disalin sebagai dataset
/var/lib/ojs-248-files/            # private files_dir, di luar web root
/var/www/ojs-248/public/           # public_files_dir relatif terhadap aplikasi
/opt/ojs-datasets/ojs-2.4.8-4/     # repositori/snapshot dataset
```

Pada konfigurasi runtime:

```ini
[files]
files_dir = "/var/lib/ojs-248-files"
public_files_dir = "public"
```

Pada konfigurasi yang disimpan sebagai artefak dataset, gunakan placeholder yang harus diganti saat restore:

```ini
[files]
files_dir = "__DATASET_FILES_DIR__"
public_files_dir = "public"
```

---

## 7. Tahap pembuatan baseline yang benar

## 7.1. Fase 0 — Kunci versi dan lingkungan

Sebelum memasukkan data apa pun, catat metadata lingkungan.

Buat `docs/build-log-template.md` dengan isian berikut:

```markdown
# Build Log Dataset OJS 2.4.8-4

- Build ID:
- Tanggal build:
- OJS source tag:
- OJS source commit:
- PHP version:
- Web server:
- DBMS dan versinya:
- OS:
- Application root:
- files_dir runtime:
- public_files_dir runtime:
- Database name:
- Database charset/collation:
- Operator:
- Catatan kompatibilitas:
```

Buat file `VERSION`:

```text
dataset_format=1
application=ojs
ojs_version=2.4.8-4
dbms=mysql
profile_model=baseline+overlay
```

### 7.2. Fase 1 — Instalasi OJS kosong

1. Siapkan OJS 2.4.8-4 dari source/tag yang tepat.
2. Pastikan aplikasi berjalan pada lingkungan legacy yang memang kompatibel.
3. Buat database kosong untuk dataset, misalnya `ojs248_dataset`.
4. Atur `files_dir` di luar web root.
5. Jalankan installer OJS melalui prosedur normal.
6. Verifikasi halaman utama, login, pembuatan jurnal, dan unggah file normal.

**Jangan** membuat `database.sql` pada tahap ini. Snapshot belum representatif.

### 7.3. Fase 2 — Buat jurnal dan struktur editorial

Melalui UI OJS:

1. buat jurnal dummy dengan path `jdis`;
2. buat section `Artikel`;
3. buat section `Tinjauan`;
4. buat issue terbit;
5. buat issue future/draft;
6. buat pengguna dan role dummy;
7. isi nama jurnal, ISSN dummy, kebijakan dummy, serta informasi penerbit dummy;
8. unggah logo atau cover dummy jika memang diperlukan.

Catat setiap tindakan dalam build log agar struktur snapshot dapat direproduksi.

### 7.4. Fase 3 — Buat submission melalui workflow OJS

Buat submission satu per satu, bukan dengan penyisipan SQL manual.

Urutan yang disarankan:

1. `A-001`: author submit file PDF normal, berhenti di tahap awal.
2. `A-002`: assign editor dan reviewer; buat file review.
3. `A-003`: buat keputusan editor dan file editor.
4. `A-004`: pindahkan ke copyedit dan buat file copyedit.
5. `A-005`: pindahkan ke layout dan buat galley/layout PDF.
6. `A-006`: publish ke issue terbit dan verifikasi halaman publik artikel.
7. `A-007`: tambahkan supplementary file, misalnya CSV.
8. `A-008`: lakukan penggantian/revisi file untuk menghasilkan nomor revisi > 1.

Setelah tiap tahap, catat:

- `article_id`;
- username author;
- section;
- status workflow;
- `file_id`;
- revision;
- file stage;
- jalur fisik di `files_dir`;
- hash SHA-256 file;
- apakah file terhubung ke database.

### 7.5. Fase 4 — Freeze baseline

Baseline dibekukan hanya setelah seluruh kondisi berikut benar:

- halaman jurnal dapat dibuka;
- artikel published dapat dibuka;
- issue terbit dan future issue terlihat sesuai status;
- file yang seharusnya dapat diunduh berhasil;
- tidak ada link file yang rusak;
- direktori file memuat struktur artikel dan issue;
- metadata database cocok dengan file fisik;
- belum ada artefak scenario `compromised`.

---

## 8. Ekspor snapshot

### 8.1. Variabel build

Gunakan variabel eksplisit agar perintah tidak bergantung pada path pribadi operator.

```bash
export APP_ROOT="/var/www/ojs-248"
export DATASET_ROOT="/opt/ojs-datasets/ojs-2.4.8-4"
export FILES_DIR="/var/lib/ojs-248-files"
export DB_NAME="ojs248_dataset"
export DB_USER="ojs_dataset"
```

### 8.2. Buat struktur keluaran

```bash
mkdir -p "$DATASET_ROOT"/mysql/{files,public}
mkdir -p "$DATASET_ROOT"/{ground-truth,scenarios/{clean,compromised,controller}/overlay-files,scripts,evidence,docs}
```

### 8.3. Dump database

Gunakan dump yang konsisten dan tidak memasukkan kredensial ke command history bila memungkinkan.

```bash
mysqldump \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --default-character-set=utf8 \
  "$DB_NAME" > "$DATASET_ROOT/mysql/database.sql"
```

Sebelum menganggap dump valid:

```bash
test -s "$DATASET_ROOT/mysql/database.sql"
grep -q "CREATE TABLE" "$DATASET_ROOT/mysql/database.sql"
```

### 8.4. Salin private `files_dir`

```bash
rsync -aHAX --delete \
  "$FILES_DIR/" \
  "$DATASET_ROOT/mysql/files/"
```

### 8.5. Salin aset publik

```bash
rsync -aHAX --delete \
  "$APP_ROOT/public/" \
  "$DATASET_ROOT/mysql/public/"
```

### 8.6. Simpan konfigurasi yang dapat dipulihkan

Jangan menyalin `config.inc.php` runtime apa adanya apabila mengandung kredensial produksi atau path personal. Buat salinan yang telah disanitasi:

```bash
cp "$APP_ROOT/config.inc.php" "$DATASET_ROOT/mysql/config.inc.php"
```

Kemudian ganti hanya path `files_dir` menjadi placeholder:

```text
__DATASET_FILES_DIR__
```

Catat pula bahwa pengguna yang melakukan restore harus memasukkan kredensial database dan URL lab miliknya sendiri.

---

## 9. Manifest ground truth

## 9.1. Mengapa manifest wajib ada

Database dan file tidak cukup untuk evaluasi SAST. Evaluasi membutuhkan **oracle** yang mendefinisikan kondisi yang benar sebelum scanner dijalankan.

Oracle tidak boleh diturunkan dari hasil scanner. Oracle harus dibuat dari kondisi dataset dan skenario yang disengaja.

### 9.2. `dataset-manifest.yaml`

Contoh:

```yaml
dataset:
  id: ojs-2.4.8-4-upload-lab-v1
  application: ojs
  application_version: "2.4.8-4"
  database_engine: mysql
  build_profile: baseline
  created_at: "YYYY-MM-DDTHH:MM:SSZ"

runtime_contract:
  files_dir_relative_root: mysql/files
  public_files_dir_relative_root: mysql/public
  source_code_included: false
  source_code_mutation_allowed: false

journal:
  journal_id: 1
  path: jdis
  title: Journal of Dummy Information Systems

integrity:
  hash_algorithm: sha256
  file_inventory: ground-truth/file-inventory.csv
  hash_manifest: ground-truth/sha256sums.txt

profiles:
  clean:
    base: baseline
    overlay: scenarios/clean/overlay-files
  compromised:
    base: baseline
    overlay: scenarios/compromised/overlay-files
  controller:
    base: baseline
    overlay: scenarios/controller/overlay-files
```

### 9.3. `entity-inventory.csv`

Satu baris untuk setiap entitas penting yang harus muncul setelah restore.

```csv
entity_type,logical_id,db_id,parent_id,status,description
journal,J-001,1,,active,Journal of Dummy Information Systems
section,S-001,1,1,active,Artikel
section,S-002,2,1,active,Tinjauan
issue,I-001,1,1,published,Issue published
issue,I-002,2,1,future,Issue future
article,A-001,<article_id>,1,submitted,Initial submission
article,A-002,<article_id>,1,in_review,Review scenario
article,A-003,<article_id>,1,editor_decision,Editor scenario
article,A-004,<article_id>,1,copyedit,Copyedit scenario
article,A-005,<article_id>,1,layout,Layout scenario
article,A-006,<article_id>,1,published,Published article
article,A-007,<article_id>,1,supplementary,Supplementary-file scenario
article,A-008,<article_id>,1,revision,Revision scenario
```

Ganti nilai placeholder `<article_id>` dengan ID nyata yang dibentuk OJS pada saat build.

### 9.4. `file-inventory.csv`

Inventaris ini memetakan kondisi fisik dan kondisi database.

```csv
profile,logical_file_id,relative_path,article_id,issue_id,file_id,revision,file_stage,db_linked,original_filename,mime_type,sha256,expected_class
baseline,F-001,journals/1/articles/11/submission/original/11-21-1-SM.pdf,11,,21,1,submission,true,manuscript-a001.pdf,application/pdf,<sha256>,normal
baseline,F-002,journals/1/articles/12/submission/review/12-22-1-RV.docx,12,,22,1,review,true,review-a002.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,<sha256>,normal
baseline,F-003,journals/1/articles/17/supp/17-30-1-SP.csv,17,,30,1,supp,true,appendix-a007.csv,text/csv,<sha256>,normal
baseline,F-004,journals/1/issues/1/public/1-2-PB.jpg,,1,2,1,issue_public,true,cover-issue-1.jpg,image/jpeg,<sha256>,normal
```

### 9.5. `upload-oracle.csv`

Ini adalah oracle evaluasi bagi scanner upload directory.

```csv
scenario_id,profile,oracle_id,relative_path,artifact_origin,db_linked,expected_detection,expected_rule_family,severity_expectation,rationale
UPL-NEG-001,clean,OR-001,journals/1/articles/11/submission/original/11-21-1-SM.pdf,ojs_workflow,true,no,none,none,Normal submission PDF created through OJS workflow
UPL-NEG-002,clean,OR-002,journals/1/articles/17/supp/17-30-1-SP.csv,ojs_workflow,true,no,none,none,Normal supplementary CSV
UPL-CTRL-001,controller,OR-003,<relative-control-path>,test_control,false,no,none,none,Adjacent control artifact that should not meet any positive rule condition
UPL-POS-001,compromised,OR-101,<relative-positive-path>,scenario_overlay,false,yes,dangerous_extension_or_signature,medium_or_high,Inert test artifact deliberately matching the documented rule condition
```

Aturan penulisan oracle:

- satu baris mewakili satu objek evaluasi atomik;
- `relative_path` selalu relatif terhadap `files_dir`;
- `db_linked=true` hanya bila file memiliki metadata OJS yang konsisten;
- artefak scenario selalu diberi `artifact_origin=scenario_overlay`;
- file normal tidak boleh diberi label positif hanya karena kebetulan ekstensi mirip;
- nilai `expected_rule_family` harus sesuai dengan desain ruleset, bukan nama finding hasil scanner;
- jangan tulis isi artefak positif di oracle; cukup identitas, lokasi, label, hash, dan rasionalenya.

---

## 10. Desain skenario upload directory

## 10.1. Tujuan ilmiah

Skenario pemindaian upload directory harus menjawab pertanyaan:

> Apakah scanner dapat membedakan file OJS yang normal dari artefak yang secara aturan harus dianggap mencurigakan pada lokasi upload OJS 2.4.8-4?

Dengan demikian, unit evaluasi bukan “satu scan”, melainkan **satu artefak yang memiliki oracle**.

### 10.2. Struktur scenario overlay

```text
scenarios/
├── clean/
│   ├── overlay-files/
│   └── profile.yaml
├── compromised/
│   ├── overlay-files/
│   │   └── journals/
│   │       └── 1/
│   │           └── articles/
│   │               └── <article_id>/
│   │                   └── submission/original/
│   └── profile.yaml
└── controller/
    ├── overlay-files/
    └── profile.yaml
```

### 10.3. Profil `clean`

Profil clean:

- dimulai dari baseline;
- tidak menambahkan artefak positif;
- hanya berisi file OJS normal;
- digunakan untuk mengukur false positive pada corpus normal.

Contoh `profile.yaml`:

```yaml
profile: clean
base_profile: baseline
expected_positive_objects: 0
overlay_action: none
```

### 10.4. Profil `controller`

Profil controller berisi file pembanding yang dekat secara bentuk tetapi tidak memenuhi kriteria rule positif.

Contoh tujuan controller:

- membedakan ekstensi normal dari ekstensi berisiko;
- membedakan file pada lokasi normal dari lokasi yang harus dipantau;
- membedakan artefak yang memiliki marker benign dari yang tidak;
- memastikan scanner tidak sekadar memicu karena nama folder atau nama artikel.

Controller tidak boleh menjadi file executable atau payload.

### 10.5. Profil `compromised`

Profil compromised:

- dimulai dari baseline;
- menambahkan artefak inert ke lokasi upload valid;
- artefak tidak dimasukkan ke database kecuali desain rule secara eksplisit ingin menguji ketidaksesuaian metadata;
- setiap artefak harus memiliki hash dan satu record oracle;
- artefak tidak boleh dapat dijalankan atau diakses dari web root.

Contoh `profile.yaml`:

```yaml
profile: compromised
base_profile: baseline
expected_positive_objects: <jumlah_oracle_positif>
overlay_root: overlay-files
safety:
  executable_content: false
  web_root_placement: false
  runtime_execution: prohibited
```

### 10.6. Jenis artefak skenario yang aman

Gunakan hanya indikator non-eksekusi sesuai kebutuhan rule Anda, misalnya:

- ekstensi yang seharusnya tidak muncul di private upload directory;
- nama ganda yang perlu diuji normalisasi;
- ketidaksesuaian MIME/ekstensi berdasarkan file uji yang tidak dapat dieksekusi;
- file orphan: berada di `files_dir` tetapi tidak memiliki metadata database;
- file linked/unlinked sebagai pengujian konsistensi;
- permission yang tidak sesuai kebijakan lab, bila rule memang memeriksa permission.

Jangan menggunakan:

- kode PHP;
- web shell;
- command execution;
- payload reverse shell;
- obfuscation;
- script yang meminta koneksi jaringan;
- artefak yang dapat memodifikasi OJS atau host.

---

## 11. Prosedur penerapan profil

### 11.1. Prinsip reset

Setiap eksperimen harus dimulai dari kondisi baseline baru. Jangan “membersihkan manual” hasil run sebelumnya karena itu menghasilkan keadaan yang sulit dibuktikan.

Alur:

```text
restore baseline
→ verify baseline
→ apply profile
→ verify profile + hashes
→ jalankan scanner
→ simpan hasil
→ hapus runtime
→ ulang dari baseline
```

### 11.2. `scripts/restore-baseline.sh`

Template:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${DATASET_ROOT:?Set DATASET_ROOT}"
: "${TARGET_FILES_DIR:?Set TARGET_FILES_DIR}"
: "${TARGET_PUBLIC_DIR:?Set TARGET_PUBLIC_DIR}"
: "${DB_NAME:?Set DB_NAME}"
: "${MYSQL_CMD:=mysql}"

BASE="$DATASET_ROOT/mysql"

test -f "$BASE/database.sql"
test -d "$BASE/files"
test -d "$BASE/public"

printf 'Restoring database...\n'
"$MYSQL_CMD" -e "DROP DATABASE IF EXISTS \`$DB_NAME\`; CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8 COLLATE utf8_general_ci;"
"$MYSQL_CMD" "$DB_NAME" < "$BASE/database.sql"

printf 'Restoring private files_dir...\n'
mkdir -p "$TARGET_FILES_DIR"
rsync -aHAX --delete "$BASE/files/" "$TARGET_FILES_DIR/"

printf 'Restoring public files...\n'
mkdir -p "$TARGET_PUBLIC_DIR"
rsync -aHAX --delete "$BASE/public/" "$TARGET_PUBLIC_DIR/"

printf 'Baseline restore complete.\n'
```

Sebelum menjalankan script ini, operator harus memastikan `TARGET_FILES_DIR` benar. Kesalahan path pada `rsync --delete` dapat menghapus data yang bukan bagian lab.

### 11.3. `scripts/apply-profile.sh`

Template:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${DATASET_ROOT:?Set DATASET_ROOT}"
: "${TARGET_FILES_DIR:?Set TARGET_FILES_DIR}"
: "${1:?Usage: apply-profile.sh <clean|controller|compromised>}"

PROFILE="$1"
OVERLAY="$DATASET_ROOT/scenarios/$PROFILE/overlay-files"
PROFILE_META="$DATASET_ROOT/scenarios/$PROFILE/profile.yaml"

test -f "$PROFILE_META"

if [ -d "$OVERLAY" ]; then
  rsync -aHAX "$OVERLAY/" "$TARGET_FILES_DIR/"
fi

printf 'Profile applied: %s\n' "$PROFILE"
```

`apply-profile.sh` hanya boleh dipanggil setelah `restore-baseline.sh` berhasil.

---

## 12. Verifikasi konsistensi

## 12.1. Verifikasi struktur file

Minimal:

```bash
find "$TARGET_FILES_DIR/journals" -type d | sort
find "$TARGET_FILES_DIR/journals" -type f | sort
```

Pastikan terdapat:

```text
journals/<journal_id>/articles/<article_id>/submission/original/
journals/<journal_id>/articles/<article_id>/submission/review/
journals/<journal_id>/articles/<article_id>/submission/editor/
journals/<journal_id>/articles/<article_id>/submission/copyedit/
journals/<journal_id>/articles/<article_id>/submission/layout/
journals/<journal_id>/articles/<article_id>/supp/
journals/<journal_id>/issues/<issue_id>/public/
```

Tidak semua artikel harus memiliki seluruh directory. Yang penting, directory muncul sesuai workflow yang benar-benar dibuat.

## 12.2. Verifikasi database

Sebelum memakai query spesifik, lihat dulu schema aktual yang terinstall:

```sql
SHOW TABLES;
DESCRIBE articles;
DESCRIBE article_files;
DESCRIBE issues;
DESCRIBE published_articles;
DESCRIBE roles;
```

Query pemeriksaan dasar:

```sql
SELECT COUNT(*) AS users_count FROM users;
SELECT COUNT(*) AS journals_count FROM journals;
SELECT COUNT(*) AS sections_count FROM sections;
SELECT COUNT(*) AS issues_count FROM issues;
SELECT COUNT(*) AS articles_count FROM articles;
SELECT COUNT(*) AS article_files_count FROM article_files;
SELECT COUNT(*) AS published_articles_count FROM published_articles;
```

Contoh query metadata file:

```sql
SELECT
  article_id,
  file_id,
  revision,
  file_stage,
  file_name,
  original_file_name,
  file_type,
  file_size
FROM article_files
ORDER BY article_id, file_id, revision;
```

Gunakan hasil query ini untuk mengisi `file-inventory.csv`. Jangan menebak ID.

## 12.3. Verifikasi file-vs-database

Untuk setiap record `article_files`:

1. ambil `article_id`, `file_id`, `revision`, `file_stage`, dan `file_name`;
2. petakan `file_stage` ke direktori sesuai tabel stage;
3. bentuk jalur absolut di bawah `files_dir`;
4. pastikan file ada;
5. hitung hash SHA-256;
6. bandingkan dengan `file-inventory.csv`.

Untuk file issue:

1. ambil data `issue_files`;
2. pastikan file berada di `journals/<journal_id>/issues/<issue_id>/public/`;
3. pastikan nama file sesuai metadata;
4. catat hash pada manifest.

## 12.4. Verifikasi aplikasi

Setelah database dan file dipulihkan:

- halaman home jurnal dapat dibuka;
- login akun dummy berhasil;
- issue published muncul;
- artikel published muncul;
- file normal yang memang harus dapat diunduh dapat diunduh;
- tidak ada error 500 pada rute utama;
- file private tidak dapat diakses secara langsung sebagai aset web;
- scanner diberi scope ke `files_dir` yang benar, bukan hanya ke application root.

---

## 13. Pembuatan hash dan bukti integritas

### 13.1. Hash baseline

Jalankan dari root `mysql/files`:

```bash
(
  cd "$DATASET_ROOT/mysql/files"
  find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$DATASET_ROOT/ground-truth/sha256sums.txt"
```

### 13.2. Hash overlay

Buat manifest hash terpisah per profil:

```text
ground-truth/sha256sums-baseline.txt
ground-truth/sha256sums-clean.txt
ground-truth/sha256sums-controller.txt
ground-truth/sha256sums-compromised.txt
```

### 13.3. Evidence run

Setiap scan harus menghasilkan direktori bukti terpisah:

```text
evidence/
└── 2026-06-21T120000Z-compromised-run-01/
    ├── environment.txt
    ├── profile.txt
    ├── hash-before.txt
    ├── scanner-command.txt
    ├── scanner-result.json
    ├── scanner-stdout.log
    ├── scanner-stderr.log
    ├── oracle-snapshot.csv
    └── comparison-result.csv
```

Simpan hasil scanner apa adanya. Jangan mengedit hasil untuk menyesuaikan oracle.

---

## 14. Aturan evaluasi ground truth upload directory

### 14.1. Unit evaluasi

Unit evaluasi yang dianjurkan:

```text
satu artefak berlabel dalam upload-oracle.csv
```

Bukan:

```text
satu folder
satu scan keseluruhan
satu artikel
```

Satu artefak dapat berupa:

- file normal OJS;
- file controller;
- file overlay inert yang seharusnya dideteksi;
- file orphan;
- file yang database-linked;
- file dengan kondisi permission tertentu, jika kebijakan pemeriksaan mencakup permission.

### 14.2. Aturan pencocokan finding

Sebelum evaluasi, tetapkan aturan pencocokan:

| Kondisi | Kriteria |
|---|---|
| `TP` | Scanner menghasilkan finding yang cocok dengan artefak oracle positif dan rule family yang relevan. |
| `FN` | Artefak oracle positif tidak menghasilkan finding relevan. |
| `FP` | Scanner menandai artefak oracle negatif/controller sebagai positif. |
| `TN` | Artefak oracle negatif tidak ditandai. |

Aturan matching yang harus dikunci:

1. matching utama menggunakan `relative_path`;
2. bila scanner melaporkan path absolut, normalisasi menjadi relatif terhadap `files_dir`;
3. bila scanner memberikan beberapa finding pada satu file, pilih rule family paling relevan atau hitung per-rule jika rancangan evaluasi memang per-rule;
4. file yang tidak terdaftar di oracle tidak boleh langsung dihitung; catat sebagai `unlabeled finding` dan investigasi;
5. jangan mengubah oracle setelah melihat hasil scanner tanpa membuat versi oracle baru dan mencatat alasan revisi.

### 14.3. Hasil yang perlu dilaporkan

Untuk setiap profil dan setiap run, laporkan minimal:

- jumlah objek oracle positif;
- jumlah objek oracle negatif;
- TP, FN, FP, TN;
- detection coverage / recall terhadap artefak positif;
- miss rate;
- false-positive rate terhadap kontrol negatif;
- daftar path yang terlewat;
- daftar finding tanpa label;
- hash manifest yang dipakai;
- versi scanner dan ruleset.

---

## 15. Checklist penerimaan dataset

Dataset dinyatakan **siap** hanya bila semua kotak berikut terpenuhi.

### 15.1. Struktur dan versi

- [ ] Source OJS dikunci pada `2.4.8-4`.
- [ ] Versi PHP, DBMS, web server, dan OS dicatat.
- [ ] `database.sql`, `config.inc.php`, `mysql/files`, dan `mysql/public` tersedia.
- [ ] `files_dir` berada di luar web root pada runtime lab.
- [ ] Source code aplikasi tidak dimasukkan sebagai bagian snapshot data.

### 15.2. Data aplikasi

- [ ] Satu jurnal dummy tersedia dan dapat diakses.
- [ ] Role dummy tersedia.
- [ ] Minimal dua section tersedia.
- [ ] Issue published dan future tersedia.
- [ ] Delapan submission mewakili tahapan yang ditentukan.
- [ ] Artikel published dapat dibuka pada halaman publik.
- [ ] File normal dapat diunduh melalui workflow OJS.

### 15.3. File dan database

- [ ] Setiap file `db_linked=true` di inventaris benar-benar ada secara fisik.
- [ ] Setiap file database-linked memiliki record metadata yang cocok.
- [ ] File issue berada pada tree issue.
- [ ] Aset publik berada pada `public/`, bukan tercampur dengan private files.
- [ ] Hash seluruh file baseline tercatat.
- [ ] Baseline tidak memiliki artefak skenario positif.

### 15.4. Skenario dan evaluasi

- [ ] `clean`, `controller`, dan `compromised` tersedia.
- [ ] Semua artefak skenario bersifat inert dan tidak executable.
- [ ] Tiap artefak scenario memiliki oracle ID dan hash.
- [ ] Restore baseline dapat dilakukan lebih dari sekali dengan hasil konsisten.
- [ ] Profil diterapkan dari baseline, bukan dari kondisi run sebelumnya.
- [ ] Hasil scan, environment, dan oracle disimpan sebagai evidence.

---

## 16. Kesalahan umum yang harus dihindari

| Kesalahan | Dampak | Pencegahan |
|---|---|---|
| Mengimpor dump OJS 3.x ke OJS 2.4 | Schema dan workflow tidak cocok | Bangun baseline khusus OJS 2.4.8-4. |
| Menyalin file tanpa dump database | File tidak terhubung metadata | Ekspor database dan `files_dir` sebagai satu snapshot. |
| Mengedit ID file manual | Jalur dan metadata tidak sinkron | Buat file melalui UI OJS, lalu snapshot. |
| Menaruh `files_dir` di web root | Mengubah makna eksperimen dan meningkatkan risiko | Gunakan lokasi private di luar application root. |
| Menyimpan file positif di baseline | Clean test tidak lagi bersih | Simpan hanya di overlay `compromised`. |
| Menghapus artefak setelah scan secara manual | State tidak reproducible | Selalu restore baseline dengan script. |
| Membuat oracle dari hasil scanner | Bias evaluasi | Bangun oracle dari rancangan scenario sebelum scan. |
| Tidak mencatat hash | Tidak dapat membuktikan file yang dipindai | Buat manifest SHA-256 per profile. |
| Menilai satu scan sebagai satu unit | Tidak menunjukkan miss per artefak | Gunakan satu record oracle sebagai unit evaluasi. |
| Menjalankan file test | Berisiko dan bukan kebutuhan evaluasi | Artefak harus inert; tidak pernah dieksekusi. |

---

## 17. Instruksi operasional untuk agen AI pembuat dataset

Agen AI yang menjalankan panduan ini harus mengikuti prioritas berikut.

```text
1. Keselamatan lab dan data dummy
2. Konsistensi OJS 2.4.8-4
3. Reproducibility baseline + overlay
4. Oracle yang independen dari hasil scanner
5. Kelengkapan bukti dan hash
6. Otomasi
```

### 17.1. Perilaku wajib

Agen harus:

1. memeriksa versi OJS yang terinstal sebelum mulai;
2. memeriksa `files_dir` aktual dari `config.inc.php`;
3. mencatat versi lingkungan;
4. membuat data melalui UI atau workflow OJS, bukan mengarang tabel manual;
5. mengambil ID aktual dari database setelah workflow selesai;
6. membangun file inventory dari metadata aktual;
7. memastikan private file berada di luar web root;
8. membuat baseline bersih sebelum scenario;
9. membuat scenario sebagai overlay;
10. menghentikan proses apabila ada mismatch database–file atau path target tidak aman.

### 17.2. Kondisi berhenti (*stop conditions*)

Agen harus berhenti dan melaporkan masalah bila:

- source OJS bukan `2.4.8-4`;
- `files_dir` kosong atau tidak dapat dibaca;
- `files_dir` menunjuk ke lokasi yang tidak dapat dipastikan sebagai lab;
- database dump gagal;
- ada file `db_linked=true` yang tidak ada;
- path overlay berada di luar `files_dir`;
- artefak scenario berisi material executable;
- baseline telah tercemar artefak positive scenario;
- aplikasi gagal membuka jurnal setelah restore;
- hash baseline berubah tanpa perubahan build yang didokumentasikan.

---

## 18. Urutan implementasi singkat

```text
A. Siapkan OJS 2.4.8-4 pada lab terisolasi
B. Konfigurasi private files_dir dan public_files_dir
C. Buat journal, user, section, issue, dan submission melalui UI
D. Verifikasi workflow, artikel published, dan file download
E. Catat ID aktual dan inventaris file
F. Dump database + copy files_dir + copy public
G. Sanitasi config menjadi portable
H. Buat hash manifest dan oracle baseline
I. Buat overlay clean/controller/compromised yang inert
J. Uji restore → apply profile → scan → collect evidence
K. Bekukan dataset versi v1
```

---

## 19. Referensi implementasi

Rujukan source yang perlu dipakai saat implementasi:

1. Tag source OJS: `ojs-2_4_8-4`.
2. `classes/file/ArticleFileManager.inc.php` untuk root file artikel, path stage, kode stage, dan pola nama file.
3. `classes/file/IssueFileManager.inc.php` untuk root file issue dan nama file public issue.
4. `config.TEMPLATE.inc.php` untuk konfigurasi `files_dir` dan `public_files_dir`.
5. README repositori `pkp/datasets` untuk layout `database.sql`, `config.inc.php`, `public`, dan `files`.

> Bila terdapat perbedaan antara dokumen ini dan schema/instalasi OJS yang benar-benar berjalan di lab, **schema dan perilaku instalasi target yang telah diverifikasi harus menjadi sumber kebenaran**, lalu dokumentasikan perbedaannya pada build log.
