# Chat Ternak - OpenAI Integration

Project ini adalah versi Chat Ternak yang sudah ditambahkan integrasi OpenAI-compatible Chat Completions API. Endpoint default diarahkan ke:

```text
https://api.slashai.my.id/v1/chat/completions
```

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
model = "gpt-4o-mini"
```

3. Jalankan aplikasi:

```bash
streamlit run app.py
```

## Catatan konfigurasi

- API key dibaca dari `config.toml`.
- Untuk deployment, API key juga bisa dioverride memakai environment variable `OPENAI_API_KEY`.
- Jika API belum dikonfigurasi atau gagal, aplikasi tetap berjalan memakai jawaban rule-based bawaan.
- Ganti nilai `model` jika provider SlashAI menggunakan nama model berbeda.

## Struktur file

```text
app.py                  # Aplikasi Streamlit utama
openai_integration.py   # Client API OpenAI-compatible
deepseek_integration.py # Wrapper kompatibilitas lama
config.toml             # Konfigurasi API
requirements.txt        # Dependency Python
```
