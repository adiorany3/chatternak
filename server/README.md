# Pakar Ternak Nusantara

Aplikasi Streamlit chatbot peternakan dengan integrasi OpenAI-compatible Chat Completions via SlashAI endpoint:

```text
https://api.slashai.my.id/v1/chat/completions
```

Persona utama aplikasi adalah **Pakar Ternak Nusantara**: konsultan peternakan praktis untuk pakan, kandang/kolam, kesehatan, reproduksi, produksi, pupuk organik, biogas, dan analisis usaha.

## Fitur utama

- Integrasi API via Streamlit Secrets, bukan hardcode di repo.
- Default model murah: `slashai/gpt-5-nano`.
- Fallback bertingkat jika respons kosong, error, kepotong, atau tidak layak.
- Riwayat chat dikirim ke model agar konteks percakapan tetap nyambung.
- Persona ahli peternakan dibuat melalui `persona.py`.
- Estimasi token dan biaya berdasarkan `usage` dari API.
- Limit sederhana per sesi untuk menahan biaya.
- Tombol reset chat dan ekspor riwayat JSON.
- Panel teknis/API disembunyikan dalam Admin Mode dengan kunci dari Streamlit Secrets.
- Kalkulator pakan, prediksi pertumbuhan, dan analisis BEP.
- Struktur kode modular agar mudah dirawat.

## Struktur file

```text
app.py                    # UI Streamlit utama
openai_integration.py     # Client OpenAI-compatible + parser respons fleksibel
chat_router.py            # Routing chat: lokal, tools, AI, fallback
persona.py                # System prompt/persona ahli peternakan
calculators.py            # Kalkulator pakan, pertumbuhan, BEP
domain_data.py            # Basis pengetahuan lokal dan intent sederhana
model_catalog.py          # Daftar model, harga, estimasi biaya
models.toml               # Katalog model dan harga per 1 juta token
config.toml               # Konfigurasi umum tanpa API key
.streamlit/secrets.toml.example
requirements.txt
```

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

`[admin].password` dipakai untuk membuka panel admin di sidebar. Panel ini menyimpan status API, sumber API key, pilihan model, fallback model, temperature, token, estimasi biaya, batas sesi, tes koneksi, dan debug konfigurasi. Pengguna biasa hanya melihat mode aplikasi dan tombol percakapan.

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

## Catatan teknis

Parser respons API mendukung:

- JSON normal OpenAI-compatible.
- `message.content` string atau list.
- `choices[0].text`.
- Streaming/SSE `data: {...}`.
- NDJSON/multiple JSON object.
- Deteksi `finish_reason="length"` agar otomatis fallback.

## Catatan keselamatan

Jawaban kesehatan hewan bersifat edukatif. Untuk gejala berat, kematian mendadak, outbreak, penyakit menular, atau penurunan produksi ekstrem, tetap hubungi dokter hewan/tenaga kesehatan hewan setempat.
