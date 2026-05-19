# Chat Ternak - OpenAI/SlashAI Integration

Project ini adalah versi Chat Ternak yang sudah ditambahkan integrasi OpenAI-compatible Chat Completions API. Endpoint default diarahkan ke:

```text
https://api.slashai.my.id/v1/chat/completions
```

## Fitur tambahan pada versi ini

- API key, endpoint, model default, temperature, max_tokens, dan timeout disimpan di `config.toml`.
- Daftar model dan harga per 1 juta token disimpan di `models.toml`.
- Model bisa dipilih langsung dari sidebar Streamlit.
- Harga input/output model tampil di sidebar sebagai referensi biaya.
- Jika API belum dikonfigurasi atau gagal, aplikasi tetap berjalan memakai jawaban rule-based bawaan.

## Cara menjalankan

1. Install dependency:

```bash
pip install -r requirements.txt
```

2. Buka `config.toml`, lalu isi API key:

```toml
[openai]
enabled = true
api_key = "ISI_API_KEY_ANDA_DI_SINI"
chat_completions_url = "https://api.slashai.my.id/v1/chat/completions"
model = "slashai/gpt-5-mini"
temperature = 0.7
max_tokens = 1000
timeout = 60
```

3. Jalankan aplikasi:

```bash
streamlit run app.py
```

## Mengganti model

Ada dua cara:

1. Lewat sidebar aplikasi, pilih model pada bagian **Model AI**.
2. Lewat `config.toml`, ubah nilai `model`, misalnya:

```toml
model = "slashai/gemini-3-flash"
```

Daftar model lengkap berada di `models.toml`. Total model yang dimasukkan: 86 model.

## Struktur file

```text
app.py                  # Aplikasi Streamlit utama
openai_integration.py   # Client API OpenAI-compatible
model_catalog.py        # Loader daftar model dari models.toml
models.toml             # Daftar model dan harga per 1 juta token
deepseek_integration.py # Wrapper kompatibilitas lama
config.toml             # Konfigurasi API
config.example.toml     # Contoh konfigurasi
requirements.txt        # Dependency Python
```

## Catatan keamanan

Jangan unggah `config.toml` berisi API key asli ke repository publik. Untuk deployment, API key juga bisa dioverride memakai environment variable `OPENAI_API_KEY`.
