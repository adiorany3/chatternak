# Pakar Ternak Nusantara

Aplikasi Streamlit berbasis AI untuk membantu peternak rakyat dan pengelola farm modern dalam konsultasi peternakan, pakan, kesehatan, reproduksi, recording performa, SOP, biosecurity, prediksi usaha, insight AI, dan backup data XLSX.

Footer aplikasi: **Developed by Galuh Adi Insani**.

## Fitur Utama

### Chat dan AI
- Persona kuat sebagai **Pakar Ternak Nusantara** dengan format jawaban pakar, aturan kesehatan, dan template komoditas.
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
  - RAW_JSON tersembunyi untuk restore data


## Alur Aplikasi Sederhana

Sidebar hanya memakai 6 menu utama agar tidak membingungkan:

1. **Beranda** — ringkasan farm, risiko, insight cepat, dan alur kerja.
2. **Input Data** — profil farm, catatan performa, dan kalender.
3. **Konsultasi AI** — konsultasi bertahap, chat pakar, dan triase kesehatan.
4. **Insight & Keputusan** — AI insight, formulasi pakan, KPI, prediksi usaha, SOP, dan biosecurity.
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
calculators.py
farm_profile.py
farm_records.py
farm_calendar.py
health_triage.py
feed_formulation.py
ai_insights.py
decision_support.py
expert_rules.py
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


## Tampilan Light/Dark

Aplikasi memakai `ui_theme.py` untuk menjaga keterbacaan pada tema Light maupun Dark Streamlit. Styling menggunakan variabel tema bawaan Streamlit (`--background-color`, `--secondary-background-color`, `--text-color`, dan `--primary-color`) sehingga kartu, tab, tombol, chat, metric, input, sidebar, dan footer mengikuti tema yang dipilih pengguna.

Komponen penting yang sudah dioptimalkan:
- kartu alur kerja;
- chat message;
- metric/scorecard;
- tombol dan download button;
- tab dan expander;
- form input;
- sidebar;
- footer `Developed by Galuh Adi Insani`.


## Catatan versi hotfix TypeError

Versi ini menambahkan pelindung kompatibilitas pada jalur `run_ai_consultation -> answer_message`, sehingga tombol rekomendasi AI pada Konsultasi Bertahap tidak berhenti jika ada mismatch parameter saat deployment Streamlit Cloud melakukan partial reload/cache.
