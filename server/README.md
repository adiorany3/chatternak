# Chat Ternak - OpenAI/SlashAI Integration

Project ini adalah versi Chat Ternak yang sudah ditambahkan integrasi OpenAI-compatible Chat Completions API. Endpoint default diarahkan ke:

```text
https://api.slashai.my.id/v1/chat/completions
```

## Fitur tambahan pada versi ini

- API key dibaca dari **Streamlit Secrets** agar aman untuk Streamlit Online / Community Cloud.
- `config.toml` hanya menyimpan konfigurasi umum dan tidak menyimpan API key.
- Daftar model dan harga per 1 juta token disimpan di `models.toml`.
- Model awal default memakai `slashai/gpt-5-nano` karena lebih murah/ringan.
- Fallback otomatis: jika jawaban dari model awal gagal, kosong, terlalu pendek, atau tidak menjawab, aplikasi mencoba model lain sesuai urutan fallback.
- Setelah fallback dipakai, request berikutnya tetap kembali lagi ke model awal.
- Sidebar menampilkan urutan percobaan model dan model yang berhasil digunakan.
- Ada tombol **Tes koneksi API** dengan token test lebih besar agar tidak mudah terkena `finish_reason=length`.
- Jika semua model AI gagal, aplikasi tetap berjalan memakai jawaban rule-based bawaan.

## Cara menjalankan lokal

1. Install dependency:

```bash
pip install -r requirements.txt
```

2. Buat file secrets lokal:

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

3. Isi API key di `.streamlit/secrets.toml`:

```toml
[openai]
api_key = "ISI_API_KEY_ANDA_DI_SINI"
```

4. Jalankan aplikasi:

```bash
streamlit run app.py
```

## Cara deploy di Streamlit Online / Community Cloud

1. Upload/push project ini ke GitHub.
2. Buka aplikasi di Streamlit Cloud.
3. Masuk ke **App settings**.
4. Buka bagian **Secrets**.
5. Masukkan konfigurasi berikut:

```toml
[openai]
api_key = "ISI_API_KEY_ANDA_DI_SINI"
```

6. Simpan, lalu restart/reboot aplikasi.

> Jangan masukkan API key asli ke `config.toml`, `README.md`, atau file lain yang ikut di-push ke GitHub.

## Konfigurasi umum

File `config.toml` boleh ikut di repository karena tidak berisi API key:

```toml
[openai]
enabled = true
chat_completions_url = "https://api.slashai.my.id/v1/chat/completions"
model = "slashai/gpt-5-nano"
fallback_models = [
  "slashai/gpt-5-mini",
  "slashai/claude-haiku-4.5",
  "slashai/gemini-3-flash",
  "slashai/deepseek-v3.2"
]
smart_fallback_enabled = true
temperature = 0.7
max_tokens = 1600
test_max_tokens = 200
timeout = 60
min_answer_chars = 30
```

Nilai di atas juga bisa dioverride dari Streamlit Secrets bila diperlukan:

```toml
[openai]
api_key = "ISI_API_KEY_ANDA_DI_SINI"
model = "slashai/gpt-5-nano"
fallback_models = ["slashai/gpt-5-mini", "slashai/claude-haiku-4.5"]
temperature = 0.6
```

## Mengganti model

Ada dua cara:

1. Lewat sidebar aplikasi, pilih **Model awal AI**.
2. Lewat `config.toml`, ubah nilai `model`, misalnya:

```toml
model = "slashai/gpt-5-nano"
```

Daftar fallback bisa diatur lewat `fallback_models` di `config.toml` atau Streamlit Secrets. Daftar model lengkap berada di `models.toml`. Total model yang dimasukkan: 86 model.

## Cara kerja fallback otomatis

Urutan default:

```text
slashai/gpt-5-nano → slashai/gpt-5-mini → slashai/claude-haiku-4.5 → slashai/gemini-3-flash → slashai/deepseek-v3.2
```

Aplikasi akan naik ke model berikutnya jika respons:

- Berisi error API.
- Kosong.
- Terlalu pendek.
- Terdeteksi tidak menjawab.
- Terlihat keluar konteks peternakan/pertanian.

Fallback tidak mengubah model awal secara permanen. Setiap pertanyaan baru tetap mulai dari `slashai/gpt-5-nano` atau model awal yang dipilih di sidebar.

## Urutan pembacaan API key

Aplikasi membaca API key dengan prioritas berikut:

1. Environment variable `OPENAI_API_KEY` atau `SLASHAI_API_KEY`.
2. Streamlit Secrets: `[openai] api_key = "..."`.
3. `config.toml` sebagai fallback legacy saja.

Untuk Streamlit Online, gunakan prioritas nomor 2.

## Struktur file

```text
app.py                            # Aplikasi Streamlit utama
openai_integration.py             # Client API OpenAI-compatible + fallback model otomatis
model_catalog.py                  # Loader daftar model dari models.toml
models.toml                       # Daftar model dan harga per 1 juta token
deepseek_integration.py           # Wrapper kompatibilitas lama
config.toml                       # Konfigurasi umum tanpa API key
config.example.toml               # Contoh konfigurasi umum
.streamlit/secrets.toml.example   # Contoh format Streamlit Secrets
requirements.txt                  # Dependency Python
```

## Troubleshooting status "API belum aktif"

Cek hal berikut:

1. Di Streamlit Online, pastikan Secrets berisi:

```toml
[openai]
api_key = "TOKEN_ANDA"
```

2. Setelah mengubah Secrets, restart/reboot aplikasi.
3. Pastikan tidak ada spasi tambahan di token.
4. Pastikan model yang dipilih tersedia di provider.
5. Klik tombol **Tes koneksi API** di sidebar untuk melihat error asli dari API.

Jika berhasil, sidebar akan menampilkan **OpenAI-compatible API aktif** dan sumber API key menjadi **Streamlit Secrets** atau **Environment variable**.

## Perbaikan error `Extra data: line 2 column 1`

Versi ini sudah memakai parser respons API yang lebih fleksibel. Aplikasi dapat membaca:

- JSON standar OpenAI-compatible.
- Streaming/SSE dengan format `data: {...}`.
- NDJSON atau beberapa objek JSON yang dikirim berurutan.

Error tersebut biasanya muncul saat endpoint mengembalikan beberapa objek JSON dalam satu respons, sedangkan parser lama hanya menerima satu JSON utuh.

## Perbaikan error `finish_reason=length` dengan content kosong

Versi ini menaikkan `test_max_tokens` menjadi `200` dan `max_tokens` menjadi `1600`. Jika API tetap mengembalikan content kosong karena `finish_reason=length`, respons tersebut dianggap tidak layak dan sistem akan mencoba fallback model berikutnya secara otomatis.
