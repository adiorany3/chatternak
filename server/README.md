# Pakar Ternak Nusantara

Aplikasi Streamlit asisten manajemen peternakan dengan integrasi OpenAI-compatible Chat Completions via SlashAI endpoint:

```text
https://api.slashai.my.id/v1/chat/completions
```

Persona utama aplikasi adalah **Pakar Ternak Nusantara**: konsultan peternakan praktis untuk pakan, kandang/kolam, kesehatan, reproduksi, produksi, pupuk organik, biogas, biaya, recording, dan manajemen farm Indonesia.

## Fitur utama

- Integrasi API via **Streamlit Secrets**, bukan hardcode di repo.
- Default model murah: `slashai/gpt-5-nano`.
- Fallback bertingkat jika respons kosong, error, kepotong, atau tidak layak.
- Panel teknis/API disembunyikan dalam **Admin Mode** dengan kunci dari Streamlit Secrets.
- Chat history, profil farm, catatan performa, kasus kesehatan, kalender manajemen, dan insight lokal dikirim sebagai konteks ke AI.
- Persona pakar peternakan kuat melalui `persona.py`.
- Profil peternakan pengguna: komoditas, fase, populasi, bobot, pakan, kandang, masalah utama, biaya, target pasar.
- Dashboard farm: ringkasan profil, checklist, jadwal terdekat, ADG, FCR, mortalitas, total pakan, level risiko, dan insight cepat.
- AI Insight Farm: scorecard risiko, prioritas aksi, anomali performa, efisiensi pakan/biaya, tindak lanjut kesehatan, agenda kalender, dan rekomendasi 24 jam/7 hari/30 hari.
- Konsultasi kesehatan/triase: gejala, durasi, jumlah sakit, kematian, kondisi pakan-air, kandang/kolam, tanda bahaya, dan rekomendasi aman.
- Formulasi pakan sederhana: bahan lokal, estimasi protein, indeks energi, biaya campuran, dan ransum awal ruminansia.
- Catatan performa: bobot, pakan, biaya, mortalitas, telur, susu, catatan lapangan, ADG, FCR, ekspor JSON.
- Kalender manajemen: sanitasi, evaluasi pakan, recording, kontrol kesehatan, reproduksi, sampling bobot, dan prediksi kelahiran.
- Kalkulator pakan, prediksi pertumbuhan, dan analisis BEP.
- Estimasi token dan biaya berdasarkan `usage` dari API.
- Limit sederhana per sesi untuk menahan biaya.
- Tombol reset chat, reset data farm khusus admin, ekspor data JSON, ekspor insight JSON, dan footer **Developed by Galuh Adi Insani**.

## Struktur file

```text
app.py                    # UI Streamlit utama
openai_integration.py     # Client OpenAI-compatible + parser respons fleksibel
chat_router.py            # Routing chat: lokal, tools, AI, fallback
persona.py                # System prompt/persona ahli peternakan
calculators.py            # Kalkulator pakan, pertumbuhan, BEP
domain_data.py            # Basis pengetahuan lokal dan intent sederhana
farm_profile.py           # Profil farm, fase ternak, checklist, prediksi kebuntingan
health_triage.py          # Triase kesehatan dan tanda bahaya
feed_formulation.py       # Formula pakan, bahan lokal, target protein sederhana
farm_records.py           # Recording performa, ADG, FCR, mortalitas, produksi, biaya
farm_calendar.py          # Kalender manajemen otomatis
ai_insights.py            # Scorecard risiko, insight lokal, konteks AI insight engine
model_catalog.py          # Daftar model, harga, estimasi biaya
models.toml               # Katalog model dan harga per 1 juta token
config.toml               # Konfigurasi umum tanpa API key
.streamlit/secrets.toml.example
requirements.txt
```


## AI Insight Farm

Mode **AI Insight** membaca seluruh data aplikasi yang tersedia:

- profil peternakan,
- catatan performa,
- ADG dan FCR,
- mortalitas,
- konsumsi pakan,
- biaya,
- produksi telur/susu,
- kasus kesehatan terakhir,
- kalender manajemen,
- jadwal terlewat dan jadwal 14 hari ke depan.

Output insight dibagi menjadi dua lapis:

1. **Insight lokal otomatis**: dibuat tanpa biaya API dari aturan deterministik.
2. **Insight AI lengkap**: memakai model AI untuk menyusun kesimpulan eksekutif, temuan data, risiko prioritas, rekomendasi 24 jam, 7 hari, 30 hari, dan data yang perlu dicatat.

AI tidak mengarang data yang belum ada; sistem membedakan fakta, asumsi, risiko, dan rekomendasi.

## Cara menjalankan lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

Untuk lokal, buat file `.streamlit/secrets.toml`:

```toml
[openai]
api_key = "ISI_API_KEY_ANDA"

[admin]
password = "ISI_KUNCI_ADMIN_ANDA"
```

`[admin].password` dipakai untuk membuka panel admin di sidebar. Panel ini menyimpan status API, sumber API key, pilihan model, fallback model, temperature, token, estimasi biaya, batas sesi, tes koneksi, dan debug konfigurasi. Pengguna biasa tidak melihat panel teknis/API.

## Cara deploy Streamlit Online

1. Upload semua file ke GitHub.
2. Buka Streamlit Community Cloud.
3. Pilih repository aplikasi.
4. Masuk ke **App settings → Secrets**.
5. Isi:

```toml
[openai]
api_key = "ISI_API_KEY_ANDA"

[admin]
password = "ISI_KUNCI_ADMIN_ANDA"
```

Jangan masukkan API key atau kunci admin ke `config.toml` atau file repository.

## Admin Mode

Panel admin berada di sidebar dan terkunci dengan kunci dari Streamlit Secrets. Tambahkan bagian berikut di **App settings → Secrets**:

```toml
[admin]
password = "ISI_KUNCI_ADMIN_ANDA"
```

Setelah login admin, panel akan menampilkan:

- Status API dan sumber API key.
- Pilihan model awal dan fallback model.
- Temperature dan batas riwayat chat.
- Pemakaian sesi, token, estimasi biaya, dan batas biaya.
- Tombol tes koneksi API.
- Debug konfigurasi jika `show_debug = true` di `config.toml`.
- Tombol reset data farm.

Tekan **Kunci kembali panel admin** untuk menutup panel.

## Konfigurasi model

Di `config.toml`:

```toml
[openai]
model = "slashai/gpt-5-nano"
fallback_models = [
  "slashai/gpt-5-mini",
  "slashai/claude-haiku-4.5",
  "slashai/gemini-3-flash",
  "slashai/deepseek-v3.2",
  "slashai/claude-sonnet-4.5"
]
```

Setiap pertanyaan selalu mulai dari model awal. Jika gagal, sistem mencoba fallback, lalu request berikutnya tetap kembali ke model awal.

## Konfigurasi limit sesi

```toml
[limits]
enabled = true
max_requests_per_session = 60
max_estimated_cost_rp_per_session = 2500
max_history_messages = 16
```

Limit ini berbasis session Streamlit, bukan database global. Untuk produksi serius, tambahkan database/identity user bila ingin membatasi semua pengguna secara global.

## Catatan teknis API

Parser respons API mendukung:

- JSON normal OpenAI-compatible.
- `message.content` string atau list.
- `choices[0].text`.
- Streaming/SSE `data: {...}`.
- NDJSON/multiple JSON object.
- Deteksi `finish_reason="length"` agar otomatis fallback.

## Catatan keselamatan

Jawaban kesehatan hewan bersifat edukatif dan triase awal. Untuk gejala berat, kematian mendadak, outbreak, penyakit menular, kembung parah, tidak mau makan lebih dari 24 jam, atau penurunan produksi ekstrem, tetap hubungi dokter hewan/tenaga kesehatan hewan setempat.

---

Developed by Galuh Adi Insani

## Backup Sesi dalam Format XLSX

Aplikasi ini menyimpan snapshot sesi aktif ke file `.xlsx` secara otomatis pada folder sementara server Streamlit. Karena filesystem Streamlit Online dapat hilang ketika aplikasi restart, redeploy, atau sesi cloud berakhir, peternak tetap harus menekan **Download Backup XLSX** secara berkala dari sidebar.

File backup XLSX berisi sheet berikut:

- `Ringkasan` — ringkasan farm, sesi, catatan, jadwal, chat, dan pemakaian AI.
- `Profil` — profil peternakan yang dipakai sebagai konteks AI.
- `Catatan_Performa` — recording performa plus kolom analisis offline seperti ADG dan FCR estimasi.
- `Kalender` — jadwal manajemen farm.
- `Chat` — riwayat percakapan.
- `Kesehatan` — kasus kesehatan terakhir.
- `Insight_AI` — insight AI terakhir.
- `Pakan` — bahan pakan terpilih.
- `Pemakaian_AI` — pemakaian token dan estimasi biaya.
- `RAW_JSON` — sheet tersembunyi untuk restore data secara akurat.

Untuk melanjutkan sesi, buka sidebar **Backup XLSX → Pulihkan sesi dari XLSX**, unggah file backup, lalu klik **Pulihkan Data**.
