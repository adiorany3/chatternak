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
- Formulasi Pakan berbasis bahan lokal.
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

Sidebar hanya memakai 6 menu utama agar tidak membingungkan:

1. **Beranda** — ringkasan farm, risiko, insight cepat, dan alur kerja.
2. **Input Data** — profil farm, catatan performa, dan kalender.
3. **Konsultasi AI** — konsultasi bertahap, konsultasi 5 departemen, chat pakar, dan triase kesehatan.
4. **Insight & Keputusan** — AI insight, formulasi pakan, KPI, prediksi usaha, SOP, biosecurity, dan teknologi hasil ternak.
5. **Alat Hitung** — kalkulator pakan, prediksi pertumbuhan, dan BEP.
6. **Edukasi & Laporan** — library lokal, materi edukasi, dan laporan manajemen.

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
