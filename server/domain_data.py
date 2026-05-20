from __future__ import annotations

from typing import Dict, List

ANIMAL_TYPES: List[str] = ["sapi", "kambing", "ayam", "bebek", "ikan", "kelinci"]

FEED_RATES: Dict[str, float] = {
    "sapi": 0.03,
    "kambing": 0.04,
    "ayam": 0.10,
    "bebek": 0.08,
    "ikan": 0.05,
    "kelinci": 0.07,
}

DEFAULT_WEIGHTS: Dict[str, float] = {
    "sapi": 400.0,
    "kambing": 40.0,
    "ayam": 2.0,
    "bebek": 3.0,
    "ikan": 0.5,
    "kelinci": 4.0,
}

FARMING_KNOWLEDGE: Dict[str, Dict[str, str]] = {
    "sapi": {
        "info": "Sapi adalah ternak ruminansia utama untuk daging, susu, bibit, dan tenaga kerja. Di Indonesia, sapi Bali, Madura, PO, Simental, Limosin, dan FH sering dipelihara sesuai tujuan usaha.",
        "perawatan": "Perawatan sapi mencakup pakan hijauan dan konsentrat yang seimbang, air minum bersih, kandang kering dengan ventilasi baik, sanitasi rutin, recording bobot, program vaksinasi, dan pemeriksaan kesehatan berkala.",
        "pakan": "Pakan sapi umumnya terdiri dari hijauan, leguminosa, jerami terolah, konsentrat, mineral, dan air. Kebutuhan bahan kering dipengaruhi bobot badan, umur, fase produksi, dan target pertambahan bobot.",
        "reproduksi": "Masa kebuntingan sapi sekitar 9 bulan. Manajemen reproduksi perlu mencakup deteksi birahi, pencatatan kawin/IB, pemeriksaan kebuntingan, dan evaluasi calving interval.",
        "jenis": "Jenis sapi populer di Indonesia: Sapi Bali, Sapi Madura, Sapi PO, Sapi Simental, Sapi Limosin, dan Sapi FH. Pemilihan jenis perlu disesuaikan dengan iklim, pakan, modal, dan pasar.",
        "penyakit": "Gangguan umum pada sapi meliputi kembung, diare, cacingan, mastitis, gangguan reproduksi, dan penyakit infeksi tertentu. Penanganan gejala berat harus melibatkan dokter hewan.",
    },
    "kambing": {
        "info": "Kambing adalah ternak ruminansia kecil yang cocok untuk usaha skala rumah tangga sampai komersial. Produk utamanya daging, susu, bibit, dan pupuk kandang.",
        "perawatan": "Kambing memerlukan kandang panggung yang kering, pakan hijauan beragam, air bersih, mineral, pemangkasan kuku, sanitasi, pencegahan cacing, dan pemisahan ternak sakit.",
        "pakan": "Pakan kambing berupa rumput, leguminosa, daun-daunan, konsentrat, mineral, dan air. Hindari perubahan pakan mendadak karena dapat mengganggu rumen.",
        "reproduksi": "Masa kebuntingan kambing sekitar 5 bulan. Kambing dapat melahirkan 1-3 anak, tetapi performa reproduksi sangat bergantung pada body condition score, kesehatan, dan pakan.",
        "jenis": "Jenis kambing populer: Kambing Kacang, Peranakan Etawa/PE, Jawarandu, Boer, Saanen, dan Sapera. Pilih berdasarkan tujuan daging atau susu.",
        "penyakit": "Masalah umum pada kambing meliputi cacingan, scabies, diare, kembung, pneumonia, dan gangguan reproduksi. Kasus lemah, tidak mau makan, atau diare berat perlu penanganan cepat.",
    },
    "ayam": {
        "info": "Ayam dibudidayakan sebagai broiler, layer, ayam kampung, dan pejantan. Usaha ayam menuntut kontrol biosecurity, pakan, kepadatan kandang, suhu, dan vaksinasi.",
        "perawatan": "Perawatan ayam mencakup brooding yang tepat, pakan sesuai fase, air minum bersih, ventilasi, litter kering, biosecurity, vaksinasi, dan pemantauan mortalitas harian.",
        "pakan": "Pakan ayam perlu memenuhi energi, protein, asam amino, vitamin, mineral, dan kalsium/fosfor sesuai fase. Broiler, layer, dan ayam kampung membutuhkan formula berbeda.",
        "reproduksi": "Untuk pembibitan ayam, rasio jantan-betina, kualitas induk, manajemen telur tetas, sanitasi, dan inkubasi sangat menentukan daya tetas.",
        "jenis": "Jenis ayam: broiler, layer, ayam kampung, ayam Joper/Jawa Super, pejantan, dan ayam hias. Pemilihan jenis ditentukan oleh pasar, siklus produksi, dan modal.",
        "penyakit": "Penyakit umum pada ayam meliputi Newcastle Disease, Gumboro, CRD, colibacillosis, coccidiosis, dan Avian Influenza. Terapkan biosecurity dan konsultasi tenaga kesehatan hewan untuk outbreak.",
    },
    "bebek": {
        "info": "Bebek atau itik dipelihara untuk telur, daging, atau dwiguna. Bebek relatif tahan, tetapi tetap membutuhkan sanitasi, pakan cukup, dan pengelolaan air/litter.",
        "perawatan": "Perawatan bebek meliputi kandang tidak becek, ventilasi, area minum yang tidak membuat lantai selalu basah, pakan teratur, dan pemantauan produksi telur atau bobot.",
        "pakan": "Pakan bebek dapat berupa pakan komersial, dedak, jagung, sumber protein, mineral, dan hijauan. Kualitas pakan sangat memengaruhi produksi telur dan pertumbuhan.",
        "produksi": "Bebek petelur dapat menghasilkan telur tinggi jika bibit, pakan, pencahayaan, dan kesehatan terjaga. Bebek pedaging dipanen berdasarkan target bobot dan permintaan pasar.",
        "jenis": "Jenis bebek/itik populer: Peking, Mojosari, Alabio, Bali, Magelang, dan entok/itik Manila.",
        "penyakit": "Masalah umum pada bebek meliputi gangguan pencernaan, parasit, infeksi pernapasan, dan penurunan produksi telur akibat stres atau pakan kurang.",
    },
    "ikan": {
        "info": "Budidaya ikan air tawar mencakup lele, nila, gurame, mas, dan patin. Faktor kunci adalah kualitas air, kepadatan tebar, pakan, aerasi, dan manajemen penyakit.",
        "kolam": "Kolam perlu memiliki sumber air cukup, pembuangan baik, kedalaman sesuai komoditas, dan kontrol kualitas air seperti suhu, pH, oksigen terlarut, amonia, dan kekeruhan.",
        "pakan": "Pakan ikan dapat berupa pelet sesuai ukuran mulut dan fase, pakan alami, atau tambahan lokal yang aman. Overfeeding dapat menurunkan kualitas air.",
        "penyakit": "Penyakit umum ikan meliputi jamur, white spot, luka bakteri, dropsy, dan stres kualitas air. Pencegahan lebih efektif melalui air stabil dan kepadatan wajar.",
        "jenis": "Komoditas populer: lele, nila, gurame, patin, mas, bawal air tawar, dan mujair. Pilih berdasarkan pasar, air, pakan, dan lama pemeliharaan.",
    },
    "pupuk": {
        "info": "Limbah ternak dapat diolah menjadi pupuk organik padat, kompos, pupuk cair, bio-slurry, atau biogas. Pengolahan menurunkan bau, patogen, dan risiko pencemaran.",
        "kompos": "Kompos dibuat dari kotoran ternak, sisa pakan, sekam, jerami, atau bahan organik lain dengan pengaturan C/N ratio, kelembapan, aerasi, dan pembalikan.",
        "biogas": "Biogas memanfaatkan kotoran ternak dalam digester anaerob untuk menghasilkan gas metana dan residu bio-slurry yang dapat dipakai sebagai pupuk.",
        "aplikasi": "Pupuk organik sebaiknya diaplikasikan sebelum tanam dan disesuaikan dengan komoditas, kondisi tanah, serta hasil uji tanah bila tersedia.",
        "jenis": "Jenis pupuk organik peternakan: pupuk kandang matang, kompos, kascing, pupuk organik cair, dan bio-slurry.",
    },
    "kelinci": {
        "info": "Kelinci cocok untuk usaha daging, hias, atau bibit. Keunggulannya adalah siklus reproduksi cepat dan kebutuhan ruang relatif kecil.",
        "perawatan": "Kelinci perlu kandang kering, teduh, bersih, ventilasi baik, pakan serat cukup, air bersih, sanitasi rutin, dan pengamatan nafsu makan serta feses.",
        "pakan": "Pakan kelinci meliputi rumput layu, hijauan aman, pelet, dan air. Hindari hijauan basah berlebihan yang dapat memicu gangguan pencernaan.",
        "reproduksi": "Masa kebuntingan kelinci sekitar 30-32 hari. Induk perlu kotak beranak, pakan cukup, dan lingkungan minim stres.",
        "jenis": "Jenis kelinci populer: New Zealand White, Rex, Flemish Giant, Angora, Lop, dan lokal. Pilih berdasarkan tujuan daging, hias, atau bulu.",
        "penyakit": "Masalah umum meliputi diare, scabies, pilek, sore hocks, dan gangguan pencernaan. Gejala tidak mau makan harus ditangani cepat.",
    },
}

INTENTS = {
    "greeting": {
        "patterns": ["halo", "hai", "hello", "selamat pagi", "selamat siang", "selamat malam", "assalamualaikum"],
        "responses": [
            "Halo. Saya siap membantu sebagai konsultan peternakan. Silakan jelaskan jenis ternak, umur/bobot, jumlah populasi, dan kendala utamanya.",
            "Selamat datang. Untuk jawaban yang akurat, sebutkan komoditas ternak, skala usaha, kondisi kandang/kolam, dan tujuan produksi.",
        ],
    },
    "thanks": {
        "patterns": ["terima kasih", "makasih", "thank you", "thanks", "tq"],
        "responses": [
            "Sama-sama. Catat hasil pengamatan harian agar keputusan pakan, kesehatan, dan produksi lebih mudah dievaluasi.",
            "Dengan senang hati. Jika ada gejala penyakit atau penurunan produksi, sebutkan kronologi dan data kandangnya.",
        ],
    },
    "bye": {
        "patterns": ["bye", "sampai jumpa", "selamat tinggal", "dadah", "sudah cukup"],
        "responses": [
            "Sampai jumpa. Semoga manajemen ternaknya makin sehat dan produktif.",
            "Baik, sampai jumpa. Jangan lupa evaluasi pakan, sanitasi, dan recording secara rutin.",
        ],
    },
}

DOMAIN_TERMS = {
    "ternak", "peternakan", "sapi", "kambing", "domba", "ayam", "bebek", "itik", "ikan", "lele", "nila", "gurame", "kelinci",
    "pakan", "hijauan", "konsentrat", "ransum", "dedak", "silase", "fermentasi", "kandang", "kolam", "bioflok",
    "vaksin", "penyakit", "diare", "cacing", "scabies", "mastitis", "reproduksi", "bunting", "birahi", "ib", "inseminasi",
    "produksi", "telur", "susu", "daging", "bobot", "panen", "pupuk", "kompos", "biogas", "bep", "modal", "usaha",
}
