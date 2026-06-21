# Spesifikasi Dataset Lab OJS 3.3.0-13 untuk Skenario Pemindaian Direktori Unggahan

**Status:** rancangan implementasi  
**Target:** OJS 3.3.0-13 + MySQL/MariaDB pada lingkungan lab  
**Fokus evaluasi:** modul SAST *uploaded directory scan*  
**Sifat dataset:** data dummy, deterministik, dapat di-*reset*, dan aman untuk lab  
**Bukan tujuan dataset:** menguji eksekusi payload, memperoleh akses sistem, membangun web shell, melakukan persistensi, atau menguji eksploitasi terhadap jaringan lain.

---

## 1. Latar belakang dan tujuan

Dataset PKP untuk OJS 3.3.0-13 menggunakan pola *snapshot* instalasi: satu dump basis data, satu konfigurasi, direktori `files`, dan direktori `public`. Pada snapshot rujukan, berkas unggahan OJS disimpan di bawah hierarki `files/journals/1/articles/<id-submission>/`, sedangkan basis data memuat jurnal, issue, pengguna, submission, publication, serta relasi file submission.

Pola tersebut tepat dijadikan model karena pengujian SAST tidak hanya membutuhkan beberapa file acak di sebuah folder. Agar hasil pemindaian dapat dipertanggungjawabkan, objek yang dipindai harus:

1. berada pada lokasi yang secara nyata dibaca OJS sebagai `files_dir`;
2. memiliki hubungan yang dapat ditelusuri dengan entitas OJS seperti jurnal, submission, atau galley;
3. mempunyai status ground truth yang ditetapkan sebelum pemindaian;
4. dapat dibangun ulang secara identik setelah eksperimen selesai;
5. tidak bergantung pada temuan alat SAST untuk menetapkan labelnya.

Dataset yang dibangun dari spesifikasi ini menjadi **snapshot OJS lab khusus pengujian direktori unggahan**. Ketika diterapkan, snapshot boleh menimpa basis data dan isi `files_dir` target, tetapi **tidak boleh menimpa source code OJS** dan **tidak boleh menyalin mentah `config.inc.php` rujukan ke server target**.

Tujuan operasionalnya adalah menghasilkan tiga keadaan uji:

| Profil | Tujuan ilmiah | Isi |
|---|---|---|
| `clean-baseline` | Membuktikan bahwa kontrol negatif tidak memunculkan alert berisiko tinggi/medium. | File unggahan normal dan beberapa nama file yang tampak mencurigakan tetapi tidak dapat dieksekusi. |
| `mixed-primary` | Mengukur kemampuan deteksi primer terhadap artefak unggahan berakhiran ekstensi yang berbahaya. | Seluruh kontrol negatif + marker inert berakhiran `.php`, `.phtml`, `.php5`, dan double extension terminal. |
| `edge-secondary` | Mendokumentasikan batas aturan tanpa mencampurkannya ke metrik primer. | Kasus ekstensi majemuk, mismatch nama–konten, dan arsip yang membutuhkan kebijakan eksplisit. |

---

## 2. Keputusan desain yang harus dipatuhi agen

### 2.1 Batas lingkungan

Agen hanya boleh bekerja pada instalasi yang telah ditandai sebagai **lab**. Parameter minimum yang harus diterima agen:

```text
APP_DIR=/var/www/ojs-330
DB_NAME=<nama_database_OJS_33>
DB_HOST=<host_database>
DB_USER=<user_database>
FILES_DIR=<hasil_baca_dari_config_inc_php>
DATASET_DIR=<direktori_artefak_dataset>
TARGET_PROFILE=clean-baseline | mixed-primary | edge-secondary
```

Agen **wajib membaca** `config.inc.php` target untuk memperoleh `files_dir`, koneksi database, `base_url`, dan `public_files_dir`. Nilai konfigurasi deployment tidak boleh diasumsikan sama dengan snapshot PKP.

### 2.2 Larangan keamanan

Agen tidak boleh membuat atau memasukkan:

- web shell;
- fungsi eksekusi perintah, proses, atau shell;
- koneksi balik, *reverse shell*, pengunduh file, atau akses jaringan keluar;
- obfuscation, encoding payload, atau teknik *evasion*;
- kredensial nyata, token, alamat email personal, atau data pribadi;
- file berbahaya ke dalam `APP_DIR/public`, source code OJS, plugin, `cache`, atau direktori yang berada di bawah web root.

Artefak kompromi simulatif hanya boleh berupa **marker inert**. Contoh prinsip marker yang diizinkan adalah file dengan ekstensi berisiko yang isinya tidak melakukan tindakan apa pun, misalnya komentar identifikasi lab atau ekspresi inert. Tujuan marker adalah menguji pengenalan lokasi dan ekstensi oleh SAST, bukan eksekusi kode.

### 2.3 Kondisi aman yang tidak boleh dinegosiasikan

Sebelum dataset diterapkan, agen harus membuktikan:

```text
realpath(FILES_DIR) tidak berada di dalam realpath(APP_DIR)
FILES_DIR bukan symbolic link yang menunjuk ke web root
APP_DIR/public bukan lokasi penyimpanan fixture kompromi
web server tidak memetakan FILES_DIR sebagai static alias
```

Bila salah satu pemeriksaan gagal, agen harus menghentikan penerapan profil yang mengandung marker berakhiran executable. Kondisi ini adalah *fail closed*, bukan peringatan opsional.

### 2.4 Pemisahan sumber kebenaran

Terdapat tiga sumber data yang berbeda dan tidak boleh saling menggantikan:

| Artefak | Fungsi | Tidak boleh digunakan sebagai |
|---|---|---|
| `mysql/database.sql` | Memulihkan state basis data OJS. | Ground truth keamanan. |
| `files/` | Memulihkan file fisik yang dipindai. | Bukti bahwa relasi database sudah benar. |
| `oracle/upload-ground-truth.json` | Menetapkan label, skenario, dan ekspektasi evaluasi. | Hasil pemindaian alat. |
| `evidence/scan-result-*.json` | Menyimpan keluaran SAST aktual. | Dasar untuk mengubah label ground truth setelah pemindaian. |

---

## 3. Struktur paket dataset yang harus dihasilkan

Agen harus menghasilkan paket yang dapat disimpan dalam version control. Struktur minimum:

```text
ojs33-upload-sast-dataset/
├── README.md
├── dataset-manifest.yaml
├── CHANGELOG.md
├── mysql/
│   ├── database.sql
│   └── config.overlay.example.ini
├── files/
│   └── journals/
│       └── 1/
│           └── articles/
│               ├── 1/
│               ├── 2/
│               ├── ...
│               └── 12/
├── public/
│   └── index.html
├── oracle/
│   ├── upload-ground-truth.v1.json
│   ├── scenario-matrix.v1.csv
│   └── expected-scan-policy.v1.yaml
├── fixtures/
│   ├── benign/
│   ├── inert-executable-markers/
│   └── edge-cases/
├── profiles/
│   ├── clean-baseline.yaml
│   ├── mixed-primary.yaml
│   └── edge-secondary.yaml
├── scripts/
│   ├── build-dataset.sh
│   ├── apply-profile.sh
│   ├── verify-profile.sh
│   ├── collect-scan-evidence.sh
│   └── rollback.sh
└── evidence/
    └── .gitkeep
```

### 3.1 Aturan isi paket

1. `database.sql` adalah dump yang sudah memuat semua entity dummy dan relasi file yang digunakan oleh fixture.
2. `files/` hanya berisi file yang harus ada pada `files_dir`; tidak berisi dump, kredensial, script agen, atau hasil scan.
3. `public/` boleh memiliki `index.html` kosong sebagai placeholder, tetapi tidak boleh mengandung fixture berisiko.
4. `oracle/` harus dapat dipakai evaluator tanpa membaca hasil scan sebelumnya.
5. `fixtures/` adalah sumber build, bukan target runtime. Sesudah *build*, fixture disalin/di-*render* ke `files/` sesuai pemetaan manifest.
6. `evidence/` tidak boleh menjadi input pembuatan ground truth.

---

## 4. Model data OJS dummy yang wajib tersedia

Dataset tidak perlu meniru seluruh kompleksitas publikasi PKP. Namun, data harus cukup realistis agar file terlihat sebagai bagian dari sistem OJS, bukan file acak yang ditempelkan ke folder.

### 4.1 Jurnal

Buat tepat satu jurnal:

| Atribut | Nilai usulan |
|---|---|
| `journal_id` | `1` |
| `path` | `sastlab` |
| Nama tampilan | `Journal of OJS SAST Laboratory` |
| Locale utama | `en_US` atau `id_ID`, pilih satu dan konsisten |
| Status | aktif |
| Tujuan | menampung semua submission fixture |

URL publik yang dihasilkan boleh mengikuti basis URL target, misalnya `/index.php/sastlab`. Nilai `base_url` tidak disimpan secara statis di dump bila berbeda antar deployment.

### 4.2 Issue dan volume

OJS menyimpan nomor volume dan nomor issue pada entitas `issues`; tidak perlu membuat tabel volume tersendiri. Buat dua issue:

| `issue_id` | Volume | Nomor | Tahun | Status | Tujuan |
|---:|---:|---:|---:|---|---|
| 1 | 1 | 1 | 2026 | published/current | Menjadi konteks artikel kontrol. |
| 2 | 1 | 2 | 2026 | unpublished | Menjadi konteks artikel marker dan kasus tepi. |

Buat setidaknya dua section:

| `section_id` | Nama | Kegunaan |
|---:|---|---|
| 1 | Articles | Naskah utama dan galley. |
| 2 | Supplementary Files | Lampiran, dataset, gambar, dan fixture sekunder. |

### 4.3 Pengguna dummy

Gunakan akun dummy dengan domain non-produksi, misalnya `example.invalid`. Password tidak disimpan sebagai teks biasa dalam dokumentasi maupun repository. Agen harus menghasilkan hash bcrypt untuk password lab yang dipasok sebagai environment variable ketika build.

| Peran | Username usulan | Fungsi |
|---|---|---|
| Site Administrator | `lab_admin` | Pemeriksaan administratif OJS. |
| Journal Manager | `lab_manager` | Memastikan jurnal/issue dapat dikelola. |
| Editor | `lab_editor` | Pemilik proses editorial dummy. |
| Author | `lab_author` | Pengunggah logis file submission. |
| Reviewer | `lab_reviewer` | Melengkapi data editorial. |
| Reader | `lab_reader` | Akun biasa untuk pengecekan tampilan. |

Untuk setiap peran, agen harus membuat relasi yang sesuai melalui user group OJS dan `user_user_groups`. Jangan hanya membuat row `users` tanpa keanggotaan grup.

### 4.4 Submission dan publication

Buat 12 submission dummy, satu untuk setiap fixture utama. Setiap submission harus memiliki:

1. row pada `submissions`;
2. satu `publication` aktif yang menunjuk ke submission;
3. metadata judul sederhana;
4. relasi `submission_files`;
5. `files` record untuk file fisik;
6. `submission_file_settings` dengan nama tampilan asli;
7. bila fixture ditampilkan sebagai galley, relasi `publication_galleys`.

Tidak semua file wajib dipublikasikan sebagai galley. Untuk mengurangi risiko, marker inert berakhiran executable **wajib** berada pada submission internal/draft atau supplementary file, bukan galley publik yang dapat diunduh.

### 4.5 Relasi data yang harus konsisten

Agen harus mempertahankan rantai berikut:

```text
journals
  └── issues / sections
       └── submissions
            └── publications
                 └── publication_galleys (bila relevan)
            └── submission_files
                 └── files
                      └── file fisik pada FILES_DIR
```

Untuk file submission, database OJS 3.3 menggunakan `submission_files` yang mereferensikan tabel `files` melalui `file_id`. Nama tampilan file disimpan terpisah pada `submission_file_settings`. Agen tidak boleh menganggap nama fisik di disk identik dengan nama tampilan pengguna.

---

## 5. Desain fixture direktori unggahan

### 5.1 Prinsip penamaan dan isi

Setiap fixture harus memiliki empat identitas yang berbeda:

```text
fixture_id            : ID penelitian stabil, misalnya UPL-COMP-004
display_name          : nama yang terlihat pada UI OJS
physical_filename     : nama file fisik dalam FILES_DIR
relative_path          : lokasi relatif dari FILES_DIR
```

Contoh:

```text
fixture_id: UPL-COMP-004
display_name: manuscript-final.pdf.php
physical_filename: 0004-sast-marker.php
relative_path: journals/1/articles/4/0004-sast-marker.php
```

Dengan pemisahan ini, agen dapat menguji scanner yang membaca path fisik maupun metadata database tanpa membangun nama file fisik yang mudah ditebak.

### 5.2 Fixture primer yang masuk metrik utama

Tabel berikut adalah dataset minimal. Label `positive` berarti artefak berisiko secara kebijakan penelitian karena ekstensi terminal dapat diperlakukan sebagai executable pada sebagian stack PHP. Isi positif harus tetap marker inert.

| ID | Kelompok | Display name | Ekstensi terminal | Isi | Label primer | Ekspektasi |
|---|---|---|---|---|---|---|
| UPL-CTRL-001 | kontrol | `manuscript.pdf` | `.pdf` | PDF dummy valid | negatif | Tidak ada finding berisiko. |
| UPL-CTRL-002 | kontrol | `supplementary-data.csv` | `.csv` | CSV dummy | negatif | Tidak ada finding berisiko. |
| UPL-CTRL-003 | kontrol | `ethics-approval.docx` | `.docx` | DOCX dummy valid | negatif | Tidak ada finding berisiko. |
| UPL-CTRL-004 | kontrol | `figure-01.png` | `.png` | PNG dummy valid | negatif | Tidak ada finding berisiko. |
| UPL-CTRL-005 | kontrol | `server-note.php.txt` | `.txt` | teks biasa, bukan kode | negatif | Tidak ada finding executable; nama saja bukan bukti. |
| UPL-CTRL-006 | kontrol | `dataset.json` | `.json` | JSON dummy valid | negatif | Tidak ada finding berisiko. |
| UPL-COMP-001 | marker inert | `editorial-check.php` | `.php` | marker inert | positif | Minimal satu finding yang menunjuk path file. |
| UPL-COMP-002 | marker inert | `copyedit-note.phtml` | `.phtml` | marker inert | positif | Minimal satu finding yang menunjuk path file. |
| UPL-COMP-003 | marker inert | `revision.php5` | `.php5` | marker inert | positif | Minimal satu finding yang menunjuk path file. |
| UPL-COMP-004 | marker inert | `manuscript-final.pdf.php` | `.php` | marker inert | positif | Minimal satu finding yang menunjuk path file. |
| UPL-COMP-005 | marker inert | `figure-attachment.jpg.php` | `.php` | marker inert | positif | Minimal satu finding yang menunjuk path file. |
| UPL-COMP-006 | marker inert | `supplementary-form.phar` | `.phar` | marker inert | positif **hanya jika** kebijakan ruleset menetapkan `.phar` sebagai ekstensi berisiko. |

### 5.3 Kasus sekunder yang dikeluarkan dari metrik primer

Kasus berikut berguna untuk pembahasan keterbatasan ruleset, tetapi harus diberi `evaluation_scope: secondary_excluded`. Jangan menghitungnya sebagai TP, FN, FP, atau TN pada metrik primer.

| ID | Display name | Alasan dikeluarkan dari metrik primer |
|---|---|---|
| UPL-EDGE-001 | `archive.php.tar.gz` | Ekstensi terminal adalah arsip, bukan executable langsung; hasil bergantung kebijakan scanner. |
| UPL-EDGE-002 | `report.php.txt` | Nama memuat `.php`, tetapi ekstensi terminal `.txt`; tidak boleh otomatis dianggap file executable. |
| UPL-EDGE-003 | `supplement.pdf` dengan marker teks inert | Menguji mismatch nama–konten; hanya relevan bila ruleset memeriksa signature/konten. |
| UPL-EDGE-004 | `attachment.inc` | Perlakuan `.inc` tergantung konfigurasi interpreter dan kebijakan rule. |
| UPL-EDGE-005 | arsip ZIP berisi teks dummy bernama `.php` | Memerlukan keputusan eksplisit apakah scanner melakukan inspeksi isi arsip. |

### 5.4 Bentuk marker inert

Agen harus menggunakan marker yang tidak menghasilkan aksi. Aturan konseptualnya:

```text
- Tidak ada fungsi pemanggilan sistem.
- Tidak ada pembacaan/penulisan file.
- Tidak ada HTTP request atau socket.
- Tidak ada command execution.
- Tidak ada loop, kondisi, redirect, output sensitif, atau payload tersembunyi.
- Hanya header atau komentar identifikasi fixture lab.
```

Setiap marker harus memuat string stabil, contohnya:

```text
OJS-SAST-LAB-INERT-MARKER:<fixture_id>
```

String tersebut berguna untuk verifikasi hash dan audit dataset, bukan sebagai pola wajib rule SAST. Ruleset seharusnya mendeteksi karena konteks path/ekstensi, bukan karena mengetahui marker penelitian.

### 5.5 Tata letak disk

Gunakan struktur yang konsisten dengan pola OJS:

```text
${FILES_DIR}/journals/1/articles/
├── 1/  # UPL-CTRL-001
├── 2/  # UPL-CTRL-002
├── 3/  # UPL-CTRL-003
├── 4/  # UPL-CTRL-004
├── 5/  # UPL-CTRL-005
├── 6/  # UPL-CTRL-006
├── 7/  # UPL-COMP-001
├── 8/  # UPL-COMP-002
├── 9/  # UPL-COMP-003
├── 10/ # UPL-COMP-004
├── 11/ # UPL-COMP-005
└── 12/ # UPL-COMP-006
```

Agen harus menentukan format nama fisik yang kompatibel dengan instalasi OJS 3.3 target. Bila ingin meniru snapshot PKP, nama fisik dapat berupa nama generated yang tidak sama dengan display name. Namun, manifest harus selalu menyimpan pemetaan `fixture_id → relative_path → file_id → submission_file_id`.

---

## 6. Skema ground truth yang wajib dihasilkan

### 6.1 Prinsip label

Ground truth harus menyatakan **keadaan objek sebelum pemindaian**, bukan hasil yang diharapkan dari alat tertentu. Oleh karena itu:

- `security_label` menjelaskan klasifikasi menurut kebijakan eksperimen;
- `evaluation_scope` menentukan apakah item masuk metrik primer;
- `expected_detection` adalah ekspektasi terhadap kelas capability, bukan pengganti hasil;
- `actual_result` tidak boleh ada dalam file oracle awal.

### 6.2 Struktur JSON

Buat file `oracle/upload-ground-truth.v1.json` dengan struktur berikut:

```json
{
  "schema_version": "1.0",
  "dataset_id": "ojs33-upload-sast-lab-v1",
  "ojs_version": "3.3.0-13",
  "module": "uploaded_directory_scan",
  "created_at_utc": "<ISO-8601>",
  "label_policy": {
    "positive_definition": "File marker inert dengan ekstensi terminal yang diklasifikasikan berisiko oleh kebijakan eksperimen dan berada di FILES_DIR OJS.",
    "negative_definition": "File unggahan normal atau file teks yang tidak memiliki ekstensi terminal executable.",
    "excluded_definition": "Kasus bergantung kebijakan, seperti arsip atau mismatch nama-konten, yang dibahas secara sekunder."
  },
  "fixtures": [
    {
      "fixture_id": "UPL-COMP-001",
      "profile_membership": ["mixed-primary", "edge-secondary"],
      "security_label": "positive",
      "evaluation_scope": "primary",
      "artifact_class": "inert_executable_extension",
      "display_name": "editorial-check.php",
      "relative_path": "journals/1/articles/7/0007-sast-marker.php",
      "sha256": "<sha256_aktual>",
      "size_bytes": 0,
      "journal_id": 1,
      "submission_id": 7,
      "publication_id": 7,
      "submission_file_id": 7,
      "file_id": 7,
      "file_stage": "<nilai_stage_aktual>",
      "web_access_expected": false,
      "expected_detection": {
        "should_alert": true,
        "acceptable_rule_categories": [
          "dangerous_executable_extension",
          "executable_in_upload_directory"
        ],
        "minimum_severity": "medium"
      },
      "rationale": "Marker inert berekstensi .php berada pada FILES_DIR OJS dan melambangkan artefak kompromi yang harus diidentifikasi tanpa dieksekusi."
    }
  ]
}
```

### 6.3 Field wajib per fixture

| Field | Makna |
|---|---|
| `fixture_id` | ID stabil yang tidak berubah jika nama fisik berubah. |
| `security_label` | `positive`, `negative`, atau `excluded`. |
| `evaluation_scope` | `primary` atau `secondary_excluded`. |
| `profile_membership` | Daftar profil yang memuat fixture. |
| `relative_path` | Path relatif terhadap `FILES_DIR`; tidak menyimpan path host absolut. |
| `sha256` | Bukti integritas file aktual. |
| `journal_id`, `submission_id`, `publication_id` | Jejak ke entitas OJS. |
| `submission_file_id`, `file_id` | Jejak ke relasi file OJS. |
| `web_access_expected` | Selalu `false` untuk fixture marker inert. |
| `expected_detection.should_alert` | Ekspektasi kebijakan; tidak boleh diisi dari hasil SAST. |
| `rationale` | Alasan klasifikasi yang dapat dibaca pembaca skripsi. |

---

## 7. Kebijakan evaluasi dan pencocokan hasil SAST

### 7.1 Unit evaluasi

Unit evaluasi adalah **satu fixture file ground truth**, bukan jumlah total finding yang dikeluarkan alat. Satu file boleh menghasilkan beberapa finding, tetapi pada metrik primer hanya dihitung sekali.

Aturan pencocokan:

```text
Satu fixture positif = terdeteksi
jika terdapat minimal satu finding SAST yang:
  (a) path-nya sama atau dapat dinormalisasi ke relative_path fixture; dan
  (b) kategorinya relevan dengan file executable/berbahaya di FILES_DIR; dan
  (c) severity memenuhi ambang eksperimen.

Satu fixture negatif = false positive
jika terdapat finding berisiko yang dipetakan ke relative_path fixture.
```

### 7.2 Metrik primer

Gunakan hanya fixture dengan `evaluation_scope = primary`.

| Kondisi | Klasifikasi |
|---|---|
| Fixture positif dan terdeteksi | TP |
| Fixture positif tetapi tidak terdeteksi | FN |
| Fixture negatif dan tidak ada alert berisiko | TN |
| Fixture negatif tetapi diberi alert berisiko | FP |

Laporkan sekurang-kurangnya:

```text
Detection Coverage = TP / (TP + FN)
Miss Rate          = FN / (TP + FN)
False Positive Rate pada kontrol = FP / (FP + TN)
Precision          = TP / (TP + FP), bila FP + TP > 0
```

Untuk skripsi, **Detection Coverage** dan **Miss Rate** adalah metrik utama modul ini. Precision/False Positive Rate berfungsi sebagai pelengkap untuk menunjukkan apakah kontrol bersih ikut teralert.

### 7.3 Kasus sekunder

Fixture `secondary_excluded` tidak masuk pembilang/penyebut metrik primer. Hasilnya dilaporkan dalam tabel naratif:

| Fixture | Hasil SAST | Status terhadap kebijakan | Interpretasi |
|---|---|---|---|
| UPL-EDGE-001 | alert / tidak alert | tidak dihitung | Menunjukkan apakah ruleset memandang ekstensi menengah `.php` dalam arsip sebagai indikasi risiko. |

Dengan cara ini, eksperimen tetap adil: aturan tidak “dihukum” karena kasus yang definisi ground truth-nya belum tegas.

---

## 8. Prosedur build dataset

### 8.1 Tahap A — inventaris instalasi target

Agen harus menghasilkan `evidence/preflight.json` berisi:

```text
- versi OJS yang terdeteksi;
- APP_DIR canonical path;
- FILES_DIR canonical path;
- PUBLIC_DIR canonical path;
- nama database target;
- engine dan versi database;
- user/group owner file;
- status apakah FILES_DIR di luar APP_DIR;
- status apakah terdapat symbolic link pada jalur file;
- jumlah file awal dalam FILES_DIR;
- checksum config target tanpa mencatat password.
```

Kriteria lulus:

```text
OJS version == 3.3.0-13
database driver == mysqli
FILES_DIR berada di luar APP_DIR
target dapat dibackup
akun database memiliki hak untuk restore database target
```

### 8.2 Tahap B — buat data sumber secara terkendali

Agen harus membuat dataset dari instalasi OJS 3.3.0-13 yang bersih atau dari snapshot kerja khusus, bukan dari instalasi penelitian yang sudah tidak diketahui state-nya.

Urutan logis:

1. membuat jurnal `sastlab`;
2. membuat section;
3. membuat akun dummy dan role;
4. membuat dua issue;
5. membuat 12 submission;
6. membuat publication dan metadata minimal;
7. membuat row `files`, `submission_files`, dan `submission_file_settings`;
8. menempatkan file fisik pada path OJS;
9. membuat galley hanya untuk fixture kontrol yang aman;
10. memverifikasi melalui query database dan filesystem;
11. melakukan dump database;
12. menyalin pohon `FILES_DIR` yang telah tervalidasi ke `files/`;
13. menghitung SHA-256 seluruh fixture;
14. menghasilkan oracle dan manifest.

Agen boleh memakai SQL yang spesifik untuk skema OJS 3.3.0-13, tetapi harus menguji foreign key dan memastikan ID hasil build identik dengan ID pada oracle. Agen tidak boleh mengedit source code OJS untuk memaksa file diterima.

### 8.3 Tahap C — buat database dump yang portabel

`mysql/database.sql` harus:

- memakai `utf8`/charset yang kompatibel dengan OJS 3.3 target;
- berisi struktur dan data yang dibutuhkan snapshot;
- tidak menyimpan password deployment;
- tidak bergantung pada nama host target;
- dapat diimpor berulang untuk menghasilkan state yang sama;
- memiliki catatan versi pembuatan dan checksum di `dataset-manifest.yaml`.

Dump boleh memuat seluruh database OJS snapshot agar proses reset sederhana. Bila ingin mengurangi ukuran paket, agen boleh membuat dump hanya database OJS lab yang minimal, tetapi wajib tetap lengkap untuk booting OJS.

### 8.4 Tahap D — buat manifest integritas

`dataset-manifest.yaml` minimum:

```yaml
dataset_id: ojs33-upload-sast-lab-v1
ojs_version: 3.3.0-13
database_engine: mysql
journal:
  journal_id: 1
  path: sastlab
profiles:
  clean-baseline:
    fixture_count: 6
  mixed-primary:
    fixture_count: 12
  edge-secondary:
    fixture_count: 17
integrity:
  oracle_sha256: <hash>
  database_sql_sha256: <hash>
  files_tree_sha256: <hash>
build:
  created_at_utc: <ISO-8601>
  builder_version: <git_commit_atau_release>
security:
  executable_fixtures_are_inert: true
  expected_web_access: false
  files_dir_must_be_outside_app_dir: true
```

---

## 9. Prosedur penerapan yang menimpa state OJS lab

### 9.1 Prinsip umum

Penerapan bersifat destruktif terhadap **database target** dan **isi FILES_DIR target**. Karena itu, agen harus selalu membuat backup lebih dahulu dan hanya melanjutkan setelah preflight lulus.

Agen tidak boleh menggunakan `rm -rf` dengan path yang belum dinormalisasi. Semua path harus diperiksa dengan `realpath`, dan operasi delete harus dibatasi pada:

```text
DATABASE target yang telah diverifikasi
FILES_DIR target yang telah diverifikasi
APP_DIR/public bila dan hanya bila public snapshot memang diperlukan
```

### 9.2 Urutan apply profile

1. Kunci atau hentikan akses aplikasi secara sementara untuk mencegah perubahan saat restore.
2. Buat backup basis data dan pohon file saat ini.
3. Simpan metadata backup di `evidence/backup-manifest-<timestamp>.json`.
4. Bersihkan isi `FILES_DIR` target secara aman.
5. Pulihkan `mysql/database.sql` ke database target.
6. Salin `files/` ke `FILES_DIR` dengan mode preservasi metadata yang sesuai.
7. Jangan mengganti `config.inc.php` target. Bila diperlukan, terapkan hanya overlay yang aman seperti `base_url` atau `allowed_hosts`, dan buat backup konfigurasi terlebih dahulu.
8. Atur owner dan permission sesuai user PHP-FPM/OJS pada target.
9. Bersihkan cache OJS yang boleh dibangun ulang.
10. Jalankan verifikasi database–filesystem.
11. Jalankan pemeriksaan OJS dasar melalui HTTP lokal atau CLI yang aman.
12. Jalankan scanner SAST terhadap `FILES_DIR` atau root OJS sesuai desain modul.
13. Simpan hasil scan sebagai evidence tanpa mengubah oracle.

### 9.3 Kontrak idempotensi

Menjalankan:

```text
apply-profile.sh mixed-primary
```

dua kali berturut-turut harus menghasilkan:

```text
- jumlah fixture sama;
- hash setiap fixture sama;
- ID database yang dipetakan di oracle sama;
- tidak ada file sisa dari profil sebelumnya;
- tidak ada duplikasi submission atau user;
- tidak ada perubahan pada source code OJS.
```

### 9.4 Kontrak rollback

`rollback.sh <backup_id>` harus:

1. memulihkan database backup;
2. mengembalikan isi `FILES_DIR` backup;
3. mengembalikan konfigurasi target bila sebelumnya dibuat overlay;
4. memeriksa checksum hasil pemulihan;
5. mencatat berhasil/gagalnya rollback.

---

## 10. Verifikasi wajib sebelum pemindaian

Agen harus menjalankan verifikasi berikut dan menyimpan hasilnya.

### 10.1 Verifikasi filesystem

```text
- Semua relative_path dalam oracle ada tepat satu kali.
- Semua hash fixture sama dengan SHA-256 pada oracle.
- Tidak ada symlink pada fixture maupun direktori induknya.
- Tidak ada fixture marker inert di APP_DIR atau APP_DIR/public.
- Tidak ada file di FILES_DIR yang tidak tercatat pada manifest, kecuali file OJS yang secara eksplisit diizinkan.
- Owner dan mode permission memungkinkan OJS membaca file, tetapi tidak menambah hak executable yang tidak diperlukan.
```

### 10.2 Verifikasi database

```text
- Tepat satu journal dengan path sastlab.
- Dua issue tersedia dengan volume/nomor yang benar.
- Semua user dummy tersedia dan terhubung ke user group.
- Setiap fixture memiliki row files, submission_files, dan submission_file_settings.
- Setiap submission_file_id/file_id pada oracle cocok dengan database.
- Fixture marker tidak memiliki galley publik atau tautan unduh publik.
```

### 10.3 Verifikasi aplikasi

```text
- Halaman indeks OJS merespons normal.
- Jurnal sastlab dapat dibuka.
- Issue dan submission kontrol dapat dilihat sesuai status.
- Tidak ada error fatal pada log aplikasi akibat relasi database yang tidak lengkap.
- FILES_DIR tidak dapat diakses sebagai URL langsung.
```

### 10.4 Verifikasi non-eksekusi

Agen tidak perlu dan tidak boleh meminta atau mencoba browser untuk menjalankan fixture marker. Pembuktian keamanan cukup dilakukan dengan:

```text
- pemeriksaan containment FILES_DIR di luar APP_DIR;
- pemeriksaan konfigurasi web server;
- bukti bahwa marker tidak diletakkan pada galley publik;
- pemeriksaan bahwa marker tidak mengandung aksi.
```

---

## 11. Format evidence hasil scan

Setelah scanner dijalankan, agen harus membuat file normalisasi, misalnya:

```text
evidence/normalized-scan-result-<profile>-<timestamp>.json
```

Format minimum:

```json
{
  "dataset_id": "ojs33-upload-sast-lab-v1",
  "profile": "mixed-primary",
  "scan_id": "<id_scan>",
  "scanner_version": "<versi>",
  "scan_target": "<FILES_DIR_atau_root_yang_dinormalisasi>",
  "started_at_utc": "<ISO-8601>",
  "finished_at_utc": "<ISO-8601>",
  "finding_count": 0,
  "fixture_mapping": [
    {
      "fixture_id": "UPL-COMP-001",
      "relative_path": "journals/1/articles/7/0007-sast-marker.php",
      "matched_findings": [
        {
          "rule_id": "<rule>",
          "severity": "<severity>",
          "reported_path": "<path_dari_scanner>",
          "path_match": true
        }
      ],
      "classification": "TP"
    }
  ]
}
```

Klasifikasi TP/TN/FP/FN pada evidence adalah hasil pascapemindaian. Oracle tetap tidak diubah.

---

## 12. Kriteria penerimaan implementasi agen

Implementasi dianggap selesai hanya bila seluruh kondisi berikut terpenuhi:

1. Dataset dapat dipasang pada OJS 3.3.0-13 lab tanpa mengubah source code OJS.
2. Instalasi target dapat dikembalikan dari backup apabila penerapan gagal.
3. `clean-baseline` memuat hanya fixture negatif primer.
4. `mixed-primary` memuat tepat 6 fixture negatif primer dan fixture positif primer yang didefinisikan.
5. `edge-secondary` memuat kasus ambigu tetapi kasus tersebut tidak ikut metrik primer.
6. Semua file fisik memiliki hash dalam oracle.
7. Semua marker positif terbukti inert dari isi statisnya.
8. Semua marker positif berada di `FILES_DIR` yang berada di luar web root.
9. Tidak ada fixture marker yang tersedia sebagai galley publik.
10. Scan menghasilkan evidence yang dapat dipetakan ke `fixture_id`.
11. Penerapan profil yang sama dua kali tidak menghasilkan perubahan state tambahan.
12. Rollback berhasil pada state backup yang dibuat sebelum apply.

---

## 13. Daftar tugas implementasi untuk agen AI

Agen harus menjalankan pekerjaan dalam urutan berikut, tidak melompati verifikasi:

### Fase 0 — Preflight dan backup
- Baca konfigurasi target.
- Validasi versi OJS dan lokasi `FILES_DIR`.
- Validasi containment dan web exposure.
- Buat backup database, files, dan config.
- Hentikan pekerjaan apabila pemeriksaan aman gagal.

### Fase 1 — Bangun snapshot sumber
- Siapkan OJS 3.3.0-13 bersih untuk membentuk state kanonik.
- Buat jurnal, user, issue, section, submission, dan file mapping.
- Buat fixture kontrol, marker inert, dan edge case.
- Pastikan marker tidak dieksekusi atau ditautkan publik.
- Buat dump database dan pohon `files`.

### Fase 2 — Buat oracle
- Hitung checksum seluruh fixture.
- Buat `upload-ground-truth.v1.json`.
- Buat `scenario-matrix.v1.csv`.
- Tandai setiap item sebagai primary atau secondary excluded.
- Review bahwa label dibuat sebelum scan.

### Fase 3 — Terapkan profile
- Pulihkan database snapshot.
- Sinkronkan file snapshot ke `FILES_DIR`.
- Terapkan profile dengan daftar fixture yang jelas.
- Bersihkan state profil sebelumnya.
- Jalankan verifikasi database, filesystem, dan aplikasi.

### Fase 4 — Scan dan bukti
- Jalankan SAST.
- Simpan keluaran mentah scan.
- Normalisasi path.
- Cocokkan finding ke oracle.
- Hasilkan tabel TP/TN/FP/FN, Detection Coverage, Miss Rate, dan false-positive rate kontrol.
- Pisahkan pelaporan kasus primer dan sekunder.

### Fase 5 — Reproducibility
- Terapkan ulang profile yang sama.
- Bandingkan hash dan jumlah row database.
- Uji rollback.
- Catat versi agen, versi scanner, waktu build, dan checksum artefak.

---

## 14. Catatan metodologis untuk skripsi

Dataset ini tidak mengklaim bahwa marker inert adalah malware nyata. Terminologi yang tepat dalam naskah adalah:

> **file kompromi simulatif** atau **artefak berisiko simulatif**, yaitu file inert yang memiliki karakteristik statis relevan terhadap kebijakan deteksi, terutama ekstensi executable pada direktori unggahan OJS.

Keuntungan desain ini:

1. pengujian tetap mengukur kemampuan scanner menemukan artefak yang semestinya dicurigai;
2. tidak perlu mengaktifkan atau mengeksekusi kode pada server;
3. kontrol negatif memungkinkan pengukuran false positive;
4. relasi database–filesystem menjadikan skenario lebih representatif daripada sekadar menyalin file ke folder kosong;
5. manifest dan hash memungkinkan eksperimen diulang;
6. edge case dapat dibahas sebagai batas ruleset tanpa merusak metrik utama.

Pernyataan metodologis yang dapat digunakan:

> Evaluasi modul pemindaian direktori unggahan dilakukan pada snapshot OJS 3.3.0-13 yang dapat direproduksi. Snapshot memuat jurnal, pengguna dummy, issue, submission, serta file unggahan yang dipetakan ke ground truth independen. Artefak positif merupakan marker inert dengan karakteristik ekstensi berisiko dan ditempatkan pada `files_dir` OJS di luar web root. Pengukuran utama menggunakan detection coverage dan miss rate pada fixture positif primer serta tingkat false positive pada file kontrol. Kasus yang bergantung pada kebijakan, seperti arsip dan mismatch nama–konten, dilaporkan terpisah sebagai evaluasi sekunder.

---

## 15. Hasil akhir yang harus diserahkan agen

Agen dianggap menyerahkan pekerjaan lengkap bila tersedia:

```text
1. Paket dataset versioned sesuai struktur pada Bagian 3.
2. database.sql yang dapat memulihkan snapshot OJS lab.
3. files/ yang sesuai dengan database.sql.
4. Oracle ground truth ber-hash.
5. Tiga profile scenario.
6. Skrip build, apply, verify, collect evidence, dan rollback.
7. Preflight evidence dan backup manifest.
8. Laporan verifikasi profile.
9. Hasil scan mentah dan hasil normalisasi.
10. Tabel evaluasi primer dan tabel kasus sekunder.
```

---

## 16. Ringkasan keputusan final

- Gunakan struktur snapshot PKP sebagai **referensi organisasi**, bukan sebagai dataset keamanan yang langsung dipakai.
- Buat satu jurnal dummy, dua issue, beberapa role user, dan 12 submission agar file benar-benar menjadi bagian dari state OJS.
- Simpan fixture di `FILES_DIR` OJS; jangan di source tree atau `public/`.
- Gunakan marker kompromi simulatif yang inert.
- Pisahkan file primer, kontrol, dan edge case.
- Kunci ground truth sebelum scan.
- Jadikan dataset idempoten, dapat dibackup, dapat dipulihkan, dan dapat diaudit dengan hash.
- Ukur performa berdasarkan fixture, bukan berdasarkan jumlah finding mentah.
