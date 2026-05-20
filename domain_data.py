from __future__ import annotations

from typing import Dict, List

from commodity_breeds import ANIMAL_TYPES

FEED_RATES: Dict[str, float] = {
    "sapi": 0.03,
    "kerbau": 0.025,
    "kambing": 0.04,
    "domba": 0.04,
    "ayam": 0.10,
    "bebek": 0.08,
    "puyuh": 0.08,
    "kelinci": 0.07,
    "babi": 0.04,
    "ikan lele": 0.05,
    "ikan nila": 0.05,
    "ikan gurame": 0.04,
    "ikan patin": 0.05,
    "ikan mas": 0.05,
}

DEFAULT_WEIGHTS: Dict[str, float] = {
    "sapi": 400.0,
    "kerbau": 450.0,
    "kambing": 40.0,
    "domba": 35.0,
    "ayam": 2.0,
    "bebek": 3.0,
    "puyuh": 0.15,
    "kelinci": 4.0,
    "babi": 60.0,
    "ikan lele": 0.15,
    "ikan nila": 0.25,
    "ikan gurame": 0.50,
    "ikan patin": 0.35,
    "ikan mas": 0.25,
}

FARMING_KNOWLEDGE: Dict[str, Dict[str, str]] = {
    "sapi": {
        "info": "Sapi adalah ternak ruminansia utama untuk daging, susu, bibit, dan tenaga kerja. Di Indonesia, sapi Bali, Madura, PO, Simental, Limosin, dan FH sering dipelihara sesuai tujuan pemeliharaan.",
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

FARMING_KNOWLEDGE.update({
    "kerbau": {
        "info": "Kerbau adalah ruminansia besar untuk daging, susu, tenaga kerja, dan pupuk. Bangsa umum: kerbau lumpur, Murrah, Nili-Ravi, Surti, Jafarabadi, dan lokal.",
        "perawatan": "Kerbau membutuhkan pakan serat cukup, air bersih, tempat teduh/berendam sesuai kondisi, sanitasi, recording reproduksi, dan kontrol parasit.",
        "pakan": "Pakan kerbau berupa hijauan, jerami terolah, leguminosa, konsentrat, mineral, dan air. Kebutuhan dipengaruhi bobot, kerja, laktasi, dan tujuan daging/susu.",
        "reproduksi": "Masa kebuntingan kerbau sekitar 10 bulan. Deteksi birahi bisa lebih sulit sehingga recording dan pengamatan rutin penting.",
        "jenis": "Bangsa/tipe kerbau: kerbau lumpur, Murrah, Nili-Ravi, Surti, Jafarabadi, Pampangan, Toraya, dan lokal/campuran.",
        "penyakit": "Masalah umum meliputi parasit, gangguan pencernaan, penyakit kulit, gangguan reproduksi, dan infeksi. Kasus berat perlu dokter hewan.",
    },
    "domba": {
        "info": "Domba adalah ruminansia kecil untuk daging, bibit, dan pupuk. Bangsa umum: Garut, Ekor Tipis, Ekor Gemuk, Dorper, Merino, Suffolk, Texel, dan lokal.",
        "perawatan": "Domba membutuhkan kandang kering, pakan hijauan-leguminosa, air bersih, mineral, kontrol cacing, pemotongan kuku, dan recording bobot.",
        "pakan": "Pakan domba mirip kambing tetapi pemilihan hijauan dan adaptasi konsentrat perlu bertahap untuk mencegah gangguan rumen.",
        "reproduksi": "Masa kebuntingan domba sekitar 5 bulan. Evaluasi BCS, riwayat kawin, kelahiran, dan jumlah anak sapih penting untuk seleksi induk.",
        "jenis": "Bangsa/tipe domba: Garut, Ekor Tipis, Ekor Gemuk, Dorper, Merino, Suffolk, Texel, dan campuran/lokal.",
        "penyakit": "Masalah umum meliputi cacingan, scabies, foot rot, diare, kembung, dan pneumonia. Pisahkan ternak sakit dan perkuat sanitasi.",
    },
    "puyuh": {
        "info": "Puyuh adalah unggas kecil yang umum dipelihara untuk telur dan daging afkir. Strain umum: Coturnix japonica, lokal, Pharaoh, dan campuran.",
        "perawatan": "Puyuh perlu kandang bersih, kepadatan wajar, ventilasi baik, cahaya stabil, air bersih, pakan protein cukup, dan biosecurity.",
        "pakan": "Pakan puyuh petelur membutuhkan protein, energi, kalsium, vitamin, dan mineral yang stabil agar produksi telur tidak turun.",
        "reproduksi": "Untuk pembibitan, perhatikan rasio jantan-betina, kualitas telur tetas, sanitasi, dan inkubasi.",
        "jenis": "Strain/tipe puyuh: Coturnix japonica, lokal, Pharaoh, Golden Manchurian, dan campuran.",
        "penyakit": "Masalah umum meliputi gangguan pernapasan, diare, stres panas, kanibalisme, dan penurunan produksi telur.",
    },
    "babi": {
        "info": "Babi adalah ternak monogastrik untuk daging dan bibit. Bangsa umum: Landrace, Yorkshire/Large White, Duroc, Pietrain, Berkshire, Hampshire, dan lokal.",
        "perawatan": "Babi membutuhkan kandang bersih-kering, ventilasi, pakan sesuai fase, air cukup, biosecurity, recording reproduksi, dan manajemen limbah.",
        "pakan": "Pakan babi disusun menurut fase starter, grower, finisher, induk bunting, dan laktasi. Protein, energi, asam amino, mineral, dan kebersihan pakan penting.",
        "reproduksi": "Manajemen reproduksi meliputi deteksi birahi, service, kebuntingan, farrowing, jumlah anak lahir hidup, dan sapih.",
        "jenis": "Bangsa babi: Landrace, Yorkshire/Large White, Duroc, Pietrain, Berkshire, Hampshire, dan lokal/campuran.",
        "penyakit": "Masalah umum meliputi diare, gangguan pernapasan, parasit, penyakit kulit, dan penyakit menular. Wabah/mortalitas tinggi harus segera dilaporkan ke petugas kesehatan hewan.",
    },
    "ikan lele": FARMING_KNOWLEDGE.get("ikan", {}),
    "ikan nila": FARMING_KNOWLEDGE.get("ikan", {}),
    "ikan gurame": FARMING_KNOWLEDGE.get("ikan", {}),
    "ikan patin": FARMING_KNOWLEDGE.get("ikan", {}),
    "ikan mas": FARMING_KNOWLEDGE.get("ikan", {}),
})


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
    "nutrisi", "makanan ternak", "sosial ekonomi", "agribisnis", "teknologi hasil", "hasil ternak",
    "pemuliaan", "genetik", "bibit", "karkas", "pascapanen", "mutu", "olahan",
}


DOMAIN_TERMS.update({
    "kerbau", "domba", "puyuh", "babi", "itik", "lele", "nila", "gurame", "patin", "ikan mas",
    "bali", "madura", "po", "ongole", "brahman", "simmental", "limousin", "fh", "friesian holstein",
    "murrah", "kacang", "peranakan etawa", "pe", "boer", "saanen", "sapera", "garut", "dorper",
    "broiler", "layer", "kub", "joper", "mojosari", "alabio", "peking", "coturnix", "landrace", "duroc",
    "sangkuriang", "dumbo", "mutiara", "nirwana", "gesit", "majala", "majalaya", "strain", "bangsa", "ras"
})
