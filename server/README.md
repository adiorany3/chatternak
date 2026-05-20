# AI Pakar Ternak

Aplikasi Streamlit berbasis AI untuk membantu peternak rakyat dan pengelola farm modern dalam konsultasi peternakan dari hulu sampai hilir: nutrisi-pakan, produksi, sosial-ekonomi/agribisnis, teknologi hasil ternak, pemuliaan-reproduksi, kesehatan, recording performa, SOP, biosecurity, prediksi usaha, insight AI, backup XLSX, dan laporan PDF.

Footer aplikasi: **Developed by Galuh Adi Insani (Fakultas Peternakan UGM)**.

## Fitur Utama

### Chat dan AI
- Persona kuat sebagai **AI Pakar Ternak** dengan format jawaban pakar, aturan kesehatan, template komoditas, dan katalog bangsa/ras/strain ternak.
- Integrasi API OpenAI-compatible via `https://api.slashai.my.id/v1/chat/completions`.
- API key aman lewat **Streamlit Secrets**, bukan `config.toml`.
- Default model murah, dengan fallback model otomatis.
- Chat history, profil farm, catatan performa, kalender, kasus kesehatan, insight, skor risiko, dan preferensi pengguna dikirim sebagai konteks AI.
- Validator jawaban AI akan meminta perbaikan otomatis jika jawaban terlalu umum, kurang tindakan, atau berisiko pada kasus kesehatan.
- AI dapat bertanya balik maksimal 5 pertanyaan penting jika data kasus belum cukup.
- Tombol ubah jawaban: **Lebih sederhana**, **Langkah lapangan**, **Versi teknis**, dan **Buat SOP**.
- Log keputusan AI tersimpan agar rekomendasi dapat ditindaklanjuti dan dievaluasi.
- Mode pengguna:
  - **Peternak Rakyat**: bahasa sederhana dan bertahap.
  - **Industri Modern**: KPI, SOP, audit trail, FCR, ADG, mortalitas, biaya, dan risiko operasional.


### Komoditas Ternak dan Bangsa/Ras/Strain
- Profil farm sekarang menyimpan **komoditas ternak** dan **bangsa/ras/strain**.
- Katalog mencakup sapi, kerbau, kambing, domba, ayam, bebek/itik, puyuh, kelinci, babi, lele, nila, gurame, patin, dan ikan mas.
- Contoh bangsa/strain: Sapi Bali, Madura, PO, Brahman Cross, Simmental, Limousin, FH; Kambing Kacang, PE, Boer, Saanen, Sapera; Domba Garut, Ekor Tipis, Dorper; Broiler, Layer, KUB, Joper; Itik Mojosari, Alabio, Peking; Lele Sangkuriang, Nila Nirwana, Gurame Soang, Patin Siam, dan lainnya.
- Informasi bangsa/strain ikut dikirim ke AI, ditulis ke XLSX, dan muncul dalam laporan PDF.

### Tujuan Pemeliharaan
- Profil farm sekarang menyimpan **tujuan pemeliharaan**: **pedaging**, **petelur**, **perah**, dan **dwiguna**.
- Tujuan ini dipakai AI untuk menyesuaikan rekomendasi pakan, fase produksi, recording, teknologi hasil, target panen/produksi, dan analisis usaha.
- Backup XLSX memiliki sheet **Tujuan_Pemeliharaan** agar peternak dapat membaca definisi/fokus tiap tujuan tanpa membuka aplikasi.

### Kerangka Hulu-Hilir 5 Departemen
- Sistem sekarang memakai kerangka 5 departemen Fakultas Peternakan UGM sebagai peta keilmuan:
  - Nutrisi dan Makanan Ternak
  - Produksi Ternak
  - Sosial Ekonomi Peternakan
  - Teknologi Hasil Ternak
  - Pemuliaan dan Reproduksi Ternak
- Tersedia tab **5 Departemen** pada menu Konsultasi AI untuk konsultasi berdasarkan lensa keilmuan tertentu.
- Tersedia modul **Teknologi Hasil** untuk daging, susu, telur, ikan konsumsi, pupuk/kompos/limbah, olahan, mutu, penyimpanan, dan nilai tambah.
- Dashboard dan laporan menampilkan cek cakupan data 5 departemen agar terlihat bagian hulu-hilir mana yang masih kurang.

### Manajemen Farm
- Dashboard Farm.
- Profil Peternakan.
- Konsultasi Bertahap.
- Konsultasi Kesehatan / Triase.
- Formulasi Pakan berbasis katalog bahan pakan Indonesia yang lebih lengkap: hijauan, leguminosa, silase/fermentasi, sumber energi, protein nabati, protein hewani, konsentrat/pakan komersial, mineral, vitamin, dan aditif umum.
- Benchmark KPI.
- SOP & Biosecurity.
- Prediksi Usaha, Panen, dan Stok Pakan.
- Library Pengetahuan Lokal Indonesia.
- Edukasi Peternak.
- Laporan Manajemen.
- Catatan Performa.
- Kalender Manajemen.
- Kalkulator Pakan, Prediksi Pertumbuhan, dan BEP.

### Backup XLSX
- Setiap sesi otomatis bisa diekspor ke `.xlsx`.
- Peternak dapat membuka file XLSX tanpa sistem.
- File XLSX dapat diunggah ulang untuk memulihkan sesi.
- Sheet yang tersedia antara lain:
  - Ringkasan
  - Profil
  - Tujuan_Pemeliharaan
  - Komoditas_Bangsa
  - Catatan_Performa
  - Kalender
  - Chat
  - Kesehatan
  - Insight_AI
  - Pakan
  - Pengaturan
  - SOP_Terakhir
  - Prediksi_Usaha
  - Pemakaian_AI
  - Log_Keputusan_AI
  - Kerangka_5_Departemen
  - RAW_JSON tersembunyi untuk restore data


## Alur Aplikasi Sederhana

Sidebar sekarang memakai 2 tingkat pilihan agar dropdown **Pilih alur kerja** lebih tertata dan tidak terlalu panjang. Pertama pilih **Kelompok alur kerja**, lalu pilih menu kerja di dalam kelompok tersebut.

**1. Mulai & Data Farm**
- **Beranda** — ringkasan farm, risiko, insight cepat, dan alur kerja.
- **Input Data** — profil farm, catatan performa, dan kalender.

**2. Konsultasi & Keputusan**
- **Konsultasi AI** — konsultasi bertahap, konsultasi 5 departemen, chat pakar, dan triase kesehatan.
- **Insight & Keputusan** — AI insight, formulasi pakan, KPI, prediksi usaha, SOP, biosecurity, dan teknologi hasil ternak.

**3. Operasional Enterprise**
- **Manajemen Enterprise** — multi-farm, role, KPI, early warning, keuangan, knowledge base, dan audit trail.
- **Database Supabase** — tes koneksi, simpan sesi, dan pulihkan data permanen dari Supabase.

**4. Alat, Edukasi & Laporan**
- **Alat Hitung** — kalkulator pakan, prediksi pertumbuhan, dan BEP.
- **Edukasi & Laporan** — library lokal, materi edukasi, laporan manajemen, PDF, dan XLSX.

Algoritma kerja utama:

```text
Isi Profil Farm
   ↓
Catat Data Lapangan
   ↓
Konsultasi / Triase / Chat AI
   ↓
Baca Insight, KPI, SOP, Prediksi, dan Rekomendasi
   ↓
Pantau Dashboard Enterprise / Early Warning bila diperlukan
   ↓
Download Backup XLSX
```

## Struktur File

```text
app.py
openai_integration.py
chat_router.py
persona.py
domain_data.py
commodity_breeds.py
calculators.py
farm_profile.py
farm_records.py
farm_calendar.py
health_triage.py
feed_formulation.py
ai_insights.py
decision_support.py
expert_rules.py
ugm_departments.py
session_storage.py
model_catalog.py
models.toml
config.toml
requirements.txt
.streamlit/secrets.toml.example
```

## Setup Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```


## Memory Ahli

Sistem sekarang memakai empat lapisan memory:

1. **Default expert memory** di kode aplikasi: selalu aktif setelah deploy/restart dan membentuk AI sebagai ahli peternakan hulu-hilir.
2. **Streamlit Secrets memory**: memory permanen yang bisa disalin admin ke `App settings → Secrets`, cocok untuk konteks perusahaan, standar direksi, atau aturan strategis yang harus selalu ada.
3. **AI Core Memory Supabase**: persona, skill, role, strategi, policy, dan pembelajaran kasus disimpan pada tabel `ai_pakar_ternak_core_memory` agar tetap aktif setelah Streamlit restart.
4. **Memory berkembang lokal/XLSX**: memory yang ditambahkan admin dari panel aplikasi atau dari saran data sesi. Memory ini ikut tersimpan di Backup XLSX dan dapat disinkronkan ke Supabase.

Contoh Secrets tambahan:

```toml
[expert_memory]
organization_context = "AI Pakar Ternak digunakan untuk mendukung keputusan peternakan hulu-hilir berstandar akademik dan industri."
strategic_role = "Jawaban harus sesuai kebutuhan pimpinan/direktur utama: ringkas, berbasis risiko, KPI, biaya, prioritas, dan rencana eksekusi."
notes = [
  "Selalu bedakan rekomendasi untuk peternak rakyat dan industri modern.",
  "Gunakan kerangka 5 departemen Fakultas Peternakan UGM untuk membaca masalah hulu-hilir."
]

[[expert_memory.items]]
category = "Strategi Perusahaan"
priority = "Tinggi"
memory = "Setiap insight manajemen harus menyebut dampak biaya, risiko operasional, prioritas, dan target 7/30 hari."
```

Catatan: data baru tidak melakukan fine-tuning/model training otomatis. Sistem menyimpan ringkasan pembelajaran sebagai **retrieval memory** di Supabase, lalu memory tersebut dimasukkan kembali ke prompt AI sehingga jawaban berikutnya makin konsisten.

Di panel admin **Memory Ahli**, gunakan tombol:
- **Tes AI Core Memory**
- **Simpan Persona/Skill/Role Default**
- **Muat Memory dari Supabase**
- **Simpan Memory Berkembang ke Supabase**


## Streamlit Online Secrets

Masukkan di **App settings → Secrets**:

```toml
[openai]
api_key = "ISI_API_KEY_ANDA"

[admin]
password = "ISI_KUNCI_ADMIN_ANDA"
```

Opsional:

```toml
[openai]
api_key = "ISI_API_KEY_ANDA"
model = "slashai/gpt-5-mini"
```

## Admin Mode

Panel teknis/API disembunyikan dari pengguna biasa dan hanya terbuka dengan password admin dari Secrets. Admin dapat melihat status API, model, fallback, token, biaya, batas sesi, dan tes koneksi.

## Catatan Penting Streamlit Online

Filesystem Streamlit Online dapat hilang ketika app restart/redeploy. Karena itu backup utama adalah file XLSX yang diunduh peternak. Gunakan menu **Backup XLSX → Download Backup XLSX** setelah input data penting.

## Batasan Kesehatan Hewan

Aplikasi ini memberi triase dan tindakan awal aman, bukan pengganti dokter hewan. Untuk kematian mendadak, banyak ternak sakit bersamaan, sesak napas, kejang, kembung parah, diare berdarah, atau kondisi darurat lain, segera hubungi dokter hewan/paramedik setempat.


## Tampilan Light Paksa

Aplikasi dipaksa memakai tema **Light** melalui `.streamlit/config.toml`. Styling tambahan di `ui_theme.py` menjaga keterbacaan kartu, chat, metric, tombol, tab, expander, form input, sidebar, tabel, dan footer.

Footer tetap: `Developed by Galuh Adi Insani (Fakultas Peternakan UGM)`.

## Catatan versi hotfix TypeError

Versi ini menambahkan pelindung kompatibilitas pada jalur `run_ai_consultation -> answer_message`, sehingga tombol rekomendasi AI pada Konsultasi Bertahap tidak berhenti jika ada mismatch parameter saat deployment Streamlit Cloud melakukan partial reload/cache.

## Tampilan Light dan Pengamanan Hapus Data

Aplikasi dipaksa memakai tema **Light** melalui `.streamlit/config.toml` dan styling `ui_theme.py` agar semua kartu, tabel, tombol, form, dan sidebar tetap mudah terbaca di Streamlit Cloud.

Sebelum melakukan **Reset Chat** atau **Reset Data Farm**, aplikasi akan menanyakan:

> Apakah database sudah Anda download?

Tombol reset akan terkunci sampai pengguna mencentang konfirmasi bahwa Backup XLSX sudah diunduh. Ini mencegah data hilang ketika session Streamlit habis, app restart, atau data belum sempat dibackup.

## Laporan PDF Profesional

Aplikasi menyediakan laporan peternakan dalam format PDF siap cetak melalui menu **Edukasi & Laporan → Laporan** atau panel **Backup XLSX**. Laporan PDF memuat:

- ringkasan eksekutif farm;
- profil peternakan;
- peta cakupan 5 departemen/hulu-hilir;
- skor kesiapan dan risiko;
- KPI performa seperti ADG, FCR, mortalitas, pakan, dan biaya;
- ringkasan biosecurity dan agenda manajemen;
- insight AI terakhir dan log keputusan;
- footer **Developed by Galuh Adi Insani (Fakultas Peternakan UGM)**.

PDF bersifat laporan baca/cetak. Untuk backup dan restore data, tetap gunakan file XLSX.



## Hardening Streamlit Cloud

Versi ini ditambahkan pengaman agar lebih stabil di Streamlit Online:

- `streamlit>=1.57.0` agar parameter widget `width="stretch"` tersedia dan tidak lagi memakai `use_container_width` yang sudah deprecated.
- Setiap menu utama dirender melalui safe wrapper, sehingga error di satu modul tidak langsung mematikan seluruh aplikasi.
- Jika bagian tertentu error, aplikasi menampilkan tombol **Download Backup XLSX Darurat**.
- Reset Chat, Reset Data Farm, dan Kosongkan Log Keputusan memakai nonce key agar tidak memicu error `st.session_state` setelah widget dibuat.
- Generator XLSX dan PDF dibungkus dengan error handler.
- Autosave menggunakan folder temp dan tidak dijadikan satu-satunya penyimpanan permanen. Backup utama tetap file XLSX yang diunduh pengguna.

## Manajemen Enterprise / Platform Perusahaan

Versi ini menambahkan lapisan **Manajemen Enterprise** untuk kebutuhan peternak rakyat yang berkembang, koperasi, perusahaan peternakan, hingga keputusan level direktur utama.

Fitur tambahan:

- **Role akses operasional**: Owner/Direktur Utama, Direktur Operasional, Manager Farm, Dokter Hewan/Konsultan, Admin Data, Petugas Kandang, dan Peternak Rakyat.
- **Multi-farm dan multi-batch**: menyimpan daftar farm/unit, kandang/kolam, batch/siklus produksi, target panen, dan target pasar.
- **Input harian cepat**: petugas cukup mengisi populasi, sakit, mati, pakan, bobot, biaya, telur/susu, dan catatan lapangan.
- **Dashboard Direktur Utama**: skor enterprise, margin kasar, jumlah farm, batch, peringatan merah/kuning, dan prioritas keputusan.
- **Early warning system**: membaca mortalitas, ADG, FCR, stok pakan, biosecurity, kasus kesehatan, dan kelengkapan recording.
- **KPI standar per komoditas**: broiler, layer, ruminansia potong/perah, ikan, kelinci, babi, dan komoditas lain.
- **Validasi data otomatis**: mencegah input tidak masuk akal seperti mortalitas melebihi populasi, bobot tidak realistis, atau pakan negatif.
- **Keuangan enterprise**: transaksi pendapatan/biaya, total biaya, margin kasar, HPP per ekor/unit, HPP per kg gain, dan ROI estimasi.
- **Knowledge Base / RAG ringan**: admin dapat menambahkan SOP, standar perusahaan, atau catatan teknis yang ikut masuk Memory Ahli dan Backup XLSX.
- **Hilirisasi / Teknologi Hasil**: checklist mutu daging, susu, telur, dan ikan konsumsi sesuai tujuan pemeliharaan.
- **Database permanen opsional**: mendukung local temp save, Supabase PostgreSQL via `DATABASE_URL`/host, dan Supabase REST legacy jika dikonfigurasi melalui Secrets.
- **Aksi notifikasi langsung**: tombol Email (`mailto:`) dan WhatsApp (`wa.me`) membuka aplikasi yang tersedia di perangkat pengguna dengan pesan early warning yang sudah terisi otomatis.
- **Audit trail**: mencatat perubahan data penting, input harian, transaksi, knowledge base, dan sinkronisasi database.

Menu baru di sidebar:

```text
Manajemen Enterprise
├── Dashboard Direksi
├── Multi-Farm
├── Input Cepat
├── KPI & Warning
├── Keuangan
├── Knowledge Base
├── Hilirisasi
├── Database
├── Notifikasi
└── Audit Trail
```

### Opsional: Supabase Database PostgreSQL

Untuk Streamlit Online, jangan gunakan file `.env`. Masukkan konfigurasi database lewat **App settings → Secrets**.

Aplikasi dapat membuat tabel otomatis jika user database memiliki izin `CREATE TABLE`. Jika ingin membuat manual, jalankan SQL berikut di Supabase SQL Editor:

```sql
-- Skema baru yang dipakai aplikasi.
CREATE TABLE IF NOT EXISTS ai_pakar_ternak_sessions (
    session_id TEXT PRIMARY KEY,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ai_pakar_ternak_sessions_updated_at
ON ai_pakar_ternak_sessions (updated_at DESC);

-- Jika Anda sudah pernah membuat tabel versi lama, jalankan migrasi ini sekali:
ALTER TABLE ai_pakar_ternak_sessions ADD COLUMN IF NOT EXISTS session_id TEXT;
ALTER TABLE ai_pakar_ternak_sessions ADD COLUMN IF NOT EXISTS payload JSONB;
UPDATE ai_pakar_ternak_sessions SET session_id = session_key WHERE session_id IS NULL AND session_key IS NOT NULL;
UPDATE ai_pakar_ternak_sessions SET payload = data WHERE payload IS NULL AND data IS NOT NULL;

-- Tabel AI Core Memory untuk persona, skill, role, strategi, policy, dan pembelajaran kasus.
CREATE TABLE IF NOT EXISTS ai_pakar_ternak_core_memory (
    memory_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL DEFAULT 'learning',
    category TEXT NOT NULL DEFAULT 'Catatan Lapangan',
    priority TEXT NOT NULL DEFAULT 'Sedang',
    memory TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'app',
    usage_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_pakar_ternak_core_memory_kind
ON ai_pakar_ternak_core_memory (kind);

CREATE INDEX IF NOT EXISTS idx_ai_pakar_ternak_core_memory_updated_at
ON ai_pakar_ternak_core_memory (updated_at DESC);
```

Gunakan konfigurasi Secrets berikut:

```toml
[database]
provider = "postgres"
host = "db.huhezxjjnypthgbafmdv.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "ISI_PASSWORD_DATABASE_SUPABASE"
sslmode = "require"
table = "ai_pakar_ternak_sessions"
core_memory_table = "ai_pakar_ternak_core_memory"
```

Atau gunakan satu baris koneksi:

```toml
[database]
provider = "postgres"
database_url = "postgresql://postgres:ISI_PASSWORD_DATABASE_SUPABASE@db.huhezxjjnypthgbafmdv.supabase.co:5432/postgres?sslmode=require"
table = "ai_pakar_ternak_sessions"
core_memory_table = "ai_pakar_ternak_core_memory"
```

Untuk local development saja, boleh memakai `.env` berdasarkan `.env.example`:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Catatan keamanan:

- Jangan commit `.env` atau password Supabase ke GitHub.
- Gunakan **Streamlit Secrets** untuk deployment online.
- Backup XLSX tetap disarankan sebelum reset/hapus data.

Jika Supabase belum dikonfigurasi, aplikasi tetap berjalan memakai local temp save dan Backup XLSX.

### Tes koneksi database di aplikasi

Setelah Secrets disimpan dan aplikasi di-reboot:

1. Buka aplikasi **AI Pakar Ternak**.
2. Pilih menu utama **Database Supabase**.
3. Masukkan **Kunci admin** jika belum login Admin Mode.
4. Klik **Tes Koneksi Database**.
5. Jika berhasil, gunakan **Simpan ke Database** untuk menyimpan sesi aktif atau **Muat dari Database** untuk memulihkan data berdasarkan Session ID.

Menu **Database Supabase** sengaja dibuat sebagai menu utama agar tidak tersembunyi di tab Enterprise.

## Optimasi Responsivitas Dropdown/Menu

Versi ini mengurangi proses berat saat pengguna hanya berpindah dropdown/menu dan merapikan pilihan alur kerja:

- Sidebar memakai 2 tingkat dropdown: **Kelompok alur kerja** dan **Pilih alur kerja**.
- Setiap menu diberi label ikon dan deskripsi singkat agar pengguna memahami tujuan menu sebelum membuka halaman.

- File XLSX/PDF tidak lagi dibuat otomatis pada setiap rerun Streamlit.
- Backup dan laporan dibuat secara lazy melalui tombol **Siapkan / Perbarui File Backup**.
- Hasil XLSX/PDF yang sudah dibuat disimpan sementara di `st.session_state` agar tombol download tetap cepat.
- `st.cache_data` dipakai untuk cache generator XLSX/PDF berdasarkan fingerprint payload.
- Autosave XLSX hanya berjalan ketika data benar-benar berubah, bukan setiap rerun yang sama.
- Jika data berubah setelah file disiapkan, aplikasi meminta pengguna menyiapkan ulang backup agar isi file tetap terbaru.

## Update dropdown komoditas dan bangsa/ras/strain
- Pilihan **Bangsa / ras / strain** pada Profil Peternakan, Konsultasi Kesehatan, dan Katalog Komoditas otomatis mengikuti **Komoditas ternak** yang dipilih.
- Saat komoditas diganti, pilihan bangsa/ras/strain yang tidak sesuai tidak dibawa ke komoditas baru.

## Katalog Bahan Pakan Indonesia

Modul Formulasi Pakan menyediakan katalog bahan yang umum digunakan di Indonesia, antara lain:

- Hijauan: rumput odot, rumput gajah, pakchong, setaria, rumput raja, tebon jagung, jerami padi, jerami jagung, pucuk tebu.
- Leguminosa/daun protein: indigofera, kaliandra, lamtoro, gamal, turi, daun singkong, azolla.
- Silase/fermentasi: silase jagung, silase rumput, complete feed fermentasi, jerami amoniasi, dedak fermentasi, ampas tahu fermentasi.
- Energi/karbohidrat: jagung giling, dedak padi, bekatul, pollard, onggok, gaplek, menir, nasi aking, molases, minyak sawit/CPO.
- Protein nabati: bungkil kedelai, bungkil kelapa, bungkil inti sawit, bungkil kacang tanah, ampas tahu, ampas tempe, ampas kecap, DDGS, corn gluten meal.
- Protein hewani: tepung ikan, tepung kepala udang, tepung darah, MBM, maggot BSF, cacing sutra, keong mas olahan, limbah ikan olahan.
- Pakan komersial: konsentrat sapi/kambing/domba, pakan broiler, layer, itik, puyuh, kelinci, ikan, dan babi.
- Mineral/aditif: mineral mix, premix, garam, kapur, DCP/MCP, grit, lisin, metionin, probiotik, yeast, toxin binder.

Dropdown bahan pakan dapat difilter berdasarkan kategori dan kesesuaian komoditas agar peternak tidak bingung memilih bahan. Angka nutrisi bersifat estimasi edukatif; formula presisi tetap memerlukan uji bahan dan evaluasi performa aktual.
