# Farming Chat Bot

Sebuah aplikasi chat bot sederhana yang dapat memberikan informasi tentang peternakan dan pertanian.

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

## Cara Menggunakan

1. Buka file `index.html` di browser Anda
2. Ketik pertanyaan Anda tentang peternakan di kotak chat
3. Tekan Enter atau klik tombol "Kirim" untuk mendapatkan respons

## Contoh Pertanyaan

- "Apa saja jenis sapi yang populer di Indonesia?"
- "Bagaimana cara merawat kambing?"
- "Apa pakan yang baik untuk ayam?"
- "Berapa lama masa kebuntingan sapi?"
- "Bagaimana cara memulai peternakan untuk pemula?"
- "Berapa modal yang dibutuhkan untuk beternak ikan?"

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

## Pengembangan Lebih Lanjut

Beberapa ide untuk pengembangan lebih lanjut:
- Menambahkan lebih banyak topik dan informasi detail
- Mengimplementasikan algoritma NLP untuk pemahaman bahasa yang lebih baik
- Menambahkan gambar atau diagram untuk ilustrasi
- Mengembangkan ke aplikasi mobile
- Integrasi dengan API cuaca untuk memberikan rekomendasi peternakan berdasarkan kondisi cuaca