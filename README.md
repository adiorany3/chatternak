# Chatternak - Farming Chat Bot

Sebuah aplikasi chat bot interaktif yang dapat memberikan informasi tentang peternakan dan pertanian.

## Fitur

- Antarmuka chat yang sederhana dan responsif
- Basis pengetahuan tentang berbagai hewan ternak:
  - Sapi
  - Kambing
  - Ayam
  - Bebek
  - Ikan
- Informasi tentang pupuk organik dan pengomposan
- Informasi umum tentang memulai usaha peternakan
- Backend server dengan Python untuk pemrosesan pertanyaan yang lebih canggih

## Persyaratan

- Browser web modern (Chrome, Firefox, Safari, Edge)
- Python 3.6 atau lebih tinggi (untuk server backend)
- Node.js dan npm (opsional, untuk pengembangan frontend)

## Instalasi

### Frontend

1. Clone repositori ini:
   ```
   git clone https://github.com/yourusername/chatternak.git
   cd chatternak
   ```

2. Buka `index.html` di browser Anda atau gunakan server lokal.

### Backend Server

1. Pastikan Python 3.6+ sudah terpasang di sistem Anda
2. Masuk ke direktori server:
   ```
   cd server
   ```
3. Instal dependensi Python:
   ```
   pip install -r requirements.txt
   ```
4. Jalankan server:
   - Di macOS/Linux:
     ```
     ./start_server.sh
     ```
   - Di Windows:
     ```
     start_server.bat
     ```

## Cara Menggunakan

1. Jalankan server backend menggunakan langkah-langkah di atas
2. Buka file `index.html` di browser Anda
3. Ketik pertanyaan Anda tentang peternakan di kotak chat
4. Tekan Enter atau klik tombol "Kirim" untuk mendapatkan respons

## Contoh Pertanyaan

- "Apa saja jenis sapi yang populer di Indonesia?"
- "Bagaimana cara merawat kambing?"
- "Apa pakan yang baik untuk ayam?"
- "Berapa lama masa kebuntingan sapi?"
- "Bagaimana cara memulai peternakan untuk pemula?"
- "Berapa modal yang dibutuhkan untuk beternak ikan?"

## Struktur Proyek

```
chatternak/
├── index.html            # Halaman utama aplikasi
├── package.json          # Konfigurasi dependensi Node.js
├── README.md             # Dokumentasi proyek
├── server/               # Komponen server backend
│   ├── app.py            # Aplikasi server Python
│   ├── requirements.txt  # Dependensi Python
│   ├── start_server.bat  # Script untuk menjalankan server di Windows
│   └── start_server.sh   # Script untuk menjalankan server di macOS/Linux
└── src/                  # Kode sumber frontend
    ├── chatbot.js        # Logika chatbot
    └── styles.css        # Stylesheet aplikasi
```

## Cara Memperluas Basis Pengetahuan

Untuk menambahkan informasi baru atau topik baru ke dalam chat bot, Anda dapat mengedit file `src/chatbot.js` dan menambahkan data ke dalam objek `farmingKnowledge`.

Contoh menambahkan topik baru:

```javascript
// Tambahkan topik baru ke farmingKnowledge
'kelinci': {
    'info': 'Kelinci adalah hewan ternak yang mudah dibudidayakan dengan siklus reproduksi cepat...',
    'perawatan': 'Perawatan kelinci meliputi kandang yang bersih dan kering...',
    'pakan': 'Kelinci memakan berbagai jenis sayuran dan rumput...',
    'reproduksi': 'Kelinci betina dapat melahirkan 4-12 anak setiap kelahiran...'
}
```

Kemudian tambahkan pengecekan untuk pertanyaan spesifik tentang topik baru tersebut di fungsi `getBotResponse()`.

## Pengembangan Server

Server backend menggunakan Python dan dapat diperluas untuk:
- Menambahkan algoritma pemahaman bahasa alami yang lebih canggih
- Menghubungkan ke database untuk menyimpan percakapan
- Mengintegrasikan dengan API eksternal untuk informasi tambahan

## Pengembangan Lebih Lanjut

Beberapa ide untuk pengembangan lebih lanjut:
- Menambahkan lebih banyak topik dan informasi detail
- Mengimplementasikan algoritma NLP untuk pemahaman bahasa yang lebih baik
- Menambahkan gambar atau diagram untuk ilustrasi
- Mengembangkan ke aplikasi mobile
- Integrasi dengan API cuaca untuk memberikan rekomendasi peternakan berdasarkan kondisi cuaca
- Fitur otentikasi pengguna untuk menyimpan histori percakapan

## Kontribusi

Kontribusi selalu diterima! Silakan buat pull request atau buka issue untuk diskusi fitur baru atau perbaikan.

## Lisensi

MIT License