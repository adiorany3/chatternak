from __future__ import annotations

from typing import Any, Dict, List

# Katalog komoditas dan bangsa/ras/strain yang umum dipakai di Indonesia.
# Catatan: ini bukan daftar final akademik, tetapi basis praktis agar AI dapat
# menyesuaikan rekomendasi pakan, produksi, reproduksi, dan pasar berdasarkan
# komoditas serta bangsa/strain yang dipilih pengguna.
COMMODITY_CATALOG: Dict[str, Dict[str, Any]] = {
    "sapi": {
        "label": "Sapi",
        "group": "Ruminansia besar",
        "product_focus": ["daging", "susu", "bibit", "pupuk"],
        "breeds": [
            {"name": "Sapi Bali", "focus": "potong/bibit", "note": "Adaptif di tropis, fertilitas baik, cocok untuk sistem rakyat dan pembibitan."},
            {"name": "Sapi Madura", "focus": "potong/bibit", "note": "Tahan kondisi pakan terbatas, ukuran relatif sedang, cocok wilayah kering."},
            {"name": "Sapi PO/Peranakan Ongole", "focus": "potong/kerja", "note": "Tahan panas, banyak dipakai untuk penggemukan rakyat."},
            {"name": "Sapi Brahman Cross", "focus": "potong", "note": "Cocok penggemukan, responsif pada pakan baik, perlu adaptasi manajemen."},
            {"name": "Sapi Simmental", "focus": "potong", "note": "Pertumbuhan cepat, butuh pakan berkualitas dan recording bobot."},
            {"name": "Sapi Limousin", "focus": "potong", "note": "Karkas baik, perlu manajemen pakan intensif."},
            {"name": "Sapi Friesian Holstein/FH", "focus": "susu", "note": "Produksi susu tinggi, sensitif panas, perlu pakan, air, dan kenyamanan kandang baik."},
            {"name": "Sapi Jersey", "focus": "susu", "note": "Ukuran lebih kecil, kadar lemak susu tinggi, perlu manajemen laktasi."},
            {"name": "Sapi Wagyu", "focus": "daging premium", "note": "Pasar khusus, masa penggemukan panjang, biaya pakan tinggi."},
            {"name": "Campuran/Lokal", "focus": "sesuai tujuan", "note": "Evaluasi berdasarkan performa aktual, kondisi tubuh, dan asal bibit."},
        ],
    },
    "kerbau": {
        "label": "Kerbau",
        "group": "Ruminansia besar",
        "product_focus": ["daging", "susu", "tenaga kerja", "pupuk"],
        "breeds": [
            {"name": "Kerbau Lumpur", "focus": "daging/kerja", "note": "Tahan kondisi basah, umum di Indonesia, manajemen pakan mirip ruminansia besar."},
            {"name": "Kerbau Murrah", "focus": "susu", "note": "Tipe perah, butuh pakan dan air memadai serta manajemen laktasi."},
            {"name": "Kerbau Nili-Ravi", "focus": "susu", "note": "Tipe perah, cocok bila pasar susu kerbau tersedia."},
            {"name": "Kerbau Surti", "focus": "susu/daging", "note": "Produktivitas bergantung pakan dan iklim mikro kandang."},
            {"name": "Kerbau Jafarabadi", "focus": "susu/daging", "note": "Ukuran besar, kebutuhan pakan relatif tinggi."},
            {"name": "Kerbau Lokal", "focus": "daging/kerja", "note": "Gunakan recording bobot, reproduksi, dan kesehatan untuk seleksi."},
        ],
    },
    "kambing": {
        "label": "Kambing",
        "group": "Ruminansia kecil",
        "product_focus": ["daging", "susu", "bibit", "pupuk"],
        "breeds": [
            {"name": "Kambing Kacang", "focus": "daging/bibit", "note": "Adaptif, ukuran kecil, cocok peternak rakyat dan pembibitan lokal."},
            {"name": "Peranakan Etawa/PE", "focus": "susu/daging", "note": "Dwiguna, perlu pakan hijauan-leguminosa dan konsentrat cukup."},
            {"name": "Jawarandu", "focus": "daging/susu terbatas", "note": "Adaptif, banyak dijumpai di sistem rakyat."},
            {"name": "Boer", "focus": "pedaging", "note": "Pertumbuhan baik, perlu pakan dan seleksi bibit intensif."},
            {"name": "Saanen", "focus": "susu", "note": "Tipe perah, sensitif panas, perlu kandang teduh dan pakan laktasi."},
            {"name": "Sapera", "focus": "susu", "note": "Silangan Saanen-PE, cocok untuk usaha susu kambing dengan manajemen baik."},
            {"name": "Senduro", "focus": "susu/kontes", "note": "Potensi susu dan nilai bibit, perlu recording keturunan."},
            {"name": "Campuran/Lokal", "focus": "sesuai tujuan", "note": "Pilih berdasarkan bobot, kesehatan, ambing/testis, dan riwayat reproduksi."},
        ],
    },
    "domba": {
        "label": "Domba",
        "group": "Ruminansia kecil",
        "product_focus": ["daging", "bibit", "wol terbatas", "pupuk"],
        "breeds": [
            {"name": "Domba Garut", "focus": "daging/bibit", "note": "Pertumbuhan baik, nilai bibit tinggi, cocok penggemukan dan pembibitan."},
            {"name": "Domba Ekor Tipis", "focus": "daging/bibit", "note": "Adaptif, cocok sistem rakyat dan wilayah pakan terbatas."},
            {"name": "Domba Ekor Gemuk", "focus": "daging", "note": "Tahan kering, cadangan lemak ekor, cocok wilayah tertentu."},
            {"name": "Dorper", "focus": "pedaging", "note": "Pertumbuhan cepat, butuh manajemen pakan intensif."},
            {"name": "Merino", "focus": "wol/daging", "note": "Perlu adaptasi iklim dan perawatan bulu."},
            {"name": "Suffolk", "focus": "pedaging", "note": "Tipe terminal sire, cocok program persilangan dengan recording."},
            {"name": "Texel", "focus": "pedaging", "note": "Karkas baik, butuh pakan berkualitas."},
            {"name": "Campuran/Lokal", "focus": "sesuai tujuan", "note": "Seleksi berdasarkan ADG, kesehatan, dan performa reproduksi."},
        ],
    },
    "ayam": {
        "label": "Ayam",
        "group": "Unggas",
        "product_focus": ["daging", "telur", "bibit", "pupuk litter"],
        "breeds": [
            {"name": "Broiler komersial", "focus": "pedaging", "note": "Siklus cepat, sangat bergantung pakan, brooding, ventilasi, dan biosecurity."},
            {"name": "Layer komersial", "focus": "petelur", "note": "Perlu manajemen puncak produksi, kalsium, cahaya, dan uniformity."},
            {"name": "Ayam Kampung", "focus": "daging/telur lokal", "note": "Adaptif, pertumbuhan lebih lambat, nilai pasar lokal baik."},
            {"name": "Ayam KUB", "focus": "daging/telur lokal", "note": "Seleksi ayam kampung unggul, cocok peternak rakyat intensif/semi-intensif."},
            {"name": "Ayam Joper/Jawa Super", "focus": "pedaging lokal", "note": "Siklus lebih cepat dari kampung biasa, perlu pakan starter-grower baik."},
            {"name": "Ayam Sentul", "focus": "lokal/bibit", "note": "Plasma nutfah lokal, cocok program konservasi dan usaha lokal."},
            {"name": "Ayam Arab", "focus": "petelur lokal", "note": "Potensi telur lebih tinggi dari kampung, butuh manajemen pakan dan cahaya."},
            {"name": "Campuran/Lokal", "focus": "sesuai tujuan", "note": "Klasifikasikan dulu pedaging, petelur, atau pembibitan agar rekomendasi tepat."},
        ],
    },
    "bebek": {
        "label": "Bebek/Itik",
        "group": "Unggas air",
        "product_focus": ["telur", "daging", "bibit"],
        "breeds": [
            {"name": "Itik Mojosari", "focus": "petelur", "note": "Produktif untuk telur, perlu pakan stabil dan kandang tidak terlalu basah."},
            {"name": "Itik Alabio", "focus": "petelur/dwiguna", "note": "Adaptif, cocok produksi telur dan daging lokal."},
            {"name": "Itik Magelang", "focus": "dwiguna", "note": "Dikenal sebagai itik kalung, cocok petelur dan bibit."},
            {"name": "Itik Bali", "focus": "daging/telur", "note": "Adaptif lokal, sering terkait pasar kuliner khas."},
            {"name": "Bebek Peking", "focus": "pedaging", "note": "Pertumbuhan daging cepat, perlu pakan cukup dan sanitasi air."},
            {"name": "Entok/Itik Manila", "focus": "daging", "note": "Ukuran besar, pertumbuhan relatif lebih lama, pasar khusus."},
            {"name": "Hibrida/Campuran", "focus": "sesuai tujuan", "note": "Evaluasi produksi telur, bobot, FCR, dan mortalitas."},
        ],
    },
    "puyuh": {
        "label": "Puyuh",
        "group": "Unggas kecil",
        "product_focus": ["telur", "daging afkir", "bibit"],
        "breeds": [
            {"name": "Coturnix japonica", "focus": "petelur", "note": "Puyuh petelur paling umum, butuh pakan protein cukup dan manajemen cahaya."},
            {"name": "Puyuh Lokal", "focus": "telur/daging", "note": "Adaptif, produktivitas bergantung pakan dan seleksi bibit."},
            {"name": "Pharaoh", "focus": "telur/daging", "note": "Tipe warna umum, perlu seleksi performa produksi."},
            {"name": "Golden Manchurian", "focus": "hias/telur", "note": "Warna menarik, produktivitas harus dievaluasi per strain."},
            {"name": "Campuran", "focus": "sesuai tujuan", "note": "Fokus pada uniformity, produksi telur, dan mortalitas."},
        ],
    },
    "kelinci": {
        "label": "Kelinci",
        "group": "Monogastrik kecil",
        "product_focus": ["daging", "hias", "bibit", "bulu"],
        "breeds": [
            {"name": "New Zealand White", "focus": "daging/bibit", "note": "Pertumbuhan baik, umum untuk produksi daging dan penelitian."},
            {"name": "Rex", "focus": "daging/bulu", "note": "Bulu halus, juga bisa untuk daging."},
            {"name": "Flemish Giant", "focus": "daging/hias", "note": "Ukuran besar, kebutuhan pakan dan ruang lebih tinggi."},
            {"name": "Californian", "focus": "daging", "note": "Tipe pedaging, cocok pembibitan intensif."},
            {"name": "Angora", "focus": "bulu/hias", "note": "Butuh perawatan bulu dan kandang kering."},
            {"name": "Lop", "focus": "hias", "note": "Pasar hias, manajemen kesehatan telinga dan kebersihan penting."},
            {"name": "Campuran/Lokal", "focus": "sesuai tujuan", "note": "Pilih berdasarkan pertumbuhan, kesehatan, dan litter size."},
        ],
    },
    "babi": {
        "label": "Babi",
        "group": "Monogastrik besar",
        "product_focus": ["daging", "bibit"],
        "breeds": [
            {"name": "Landrace", "focus": "indukan/pedaging", "note": "Produktivitas anak baik, sering dipakai indukan dalam persilangan."},
            {"name": "Yorkshire/Large White", "focus": "indukan/pedaging", "note": "Adaptif di sistem intensif, performa reproduksi baik."},
            {"name": "Duroc", "focus": "terminal sire/daging", "note": "Pertumbuhan dan kualitas daging baik, umum untuk persilangan."},
            {"name": "Pietrain", "focus": "daging/karkas", "note": "Karkas berotot, perlu manajemen stres dan pakan baik."},
            {"name": "Berkshire", "focus": "daging premium", "note": "Kualitas daging baik, pasar khusus."},
            {"name": "Babi Lokal", "focus": "daging/bibit lokal", "note": "Adaptif lokal, evaluasi performa dan pasar setempat."},
        ],
    },
    "ikan lele": {
        "label": "Ikan Lele",
        "group": "Akuakultur air tawar",
        "product_focus": ["daging/pembesaran", "benih"],
        "breeds": [
            {"name": "Lele Dumbo", "focus": "pembesaran", "note": "Populer dan adaptif, perlu kontrol kualitas air dan padat tebar."},
            {"name": "Lele Sangkuriang", "focus": "pembesaran/benih", "note": "Seleksi perbaikan dari dumbo, umum untuk budidaya rakyat."},
            {"name": "Lele Mutiara", "focus": "pembesaran", "note": "Dikenal untuk pertumbuhan dan efisiensi, tetap perlu benih bermutu."},
            {"name": "Lele Masamo", "focus": "pembesaran", "note": "Pertumbuhan baik bila pakan dan air terkontrol."},
            {"name": "Lele Lokal/Campuran", "focus": "pembesaran", "note": "Evaluasi survival rate, FCR, dan keseragaman ukuran."},
        ],
    },
    "ikan nila": {
        "label": "Ikan Nila",
        "group": "Akuakultur air tawar",
        "product_focus": ["daging/pembesaran", "benih"],
        "breeds": [
            {"name": "Nila Nirwana", "focus": "pembesaran", "note": "Pertumbuhan baik, cocok kolam air tawar dengan kualitas air stabil."},
            {"name": "Nila GESIT", "focus": "pembesaran", "note": "Populasi jantan unggul untuk pertumbuhan, perlu benih terpercaya."},
            {"name": "Nila BEST", "focus": "pembesaran", "note": "Seleksi pertumbuhan, tetap perlu kontrol pakan dan kepadatan."},
            {"name": "Nila Merah", "focus": "pasar konsumsi", "note": "Warna menarik untuk pasar tertentu, performa bergantung strain."},
            {"name": "Nila Lokal/Campuran", "focus": "pembesaran", "note": "Pantau SR, FCR, dan keseragaman ukuran."},
        ],
    },
    "ikan gurame": {
        "label": "Ikan Gurame",
        "group": "Akuakultur air tawar",
        "product_focus": ["daging/pembesaran", "benih"],
        "breeds": [
            {"name": "Gurame Soang", "focus": "konsumsi", "note": "Ukuran besar, nilai jual baik, siklus lebih panjang."},
            {"name": "Gurame Bastar", "focus": "konsumsi", "note": "Populer untuk pembesaran, perlu air stabil dan pakan berkualitas."},
            {"name": "Gurame Paris", "focus": "konsumsi/benih", "note": "Pertumbuhan dan performa bergantung asal benih."},
            {"name": "Gurame Porselen", "focus": "benih/konsumsi", "note": "Perlu seleksi dan pemeliharaan intensif."},
            {"name": "Gurame Lokal/Campuran", "focus": "konsumsi", "note": "Fokus pada survival, kualitas air, dan lama pemeliharaan."},
        ],
    },
    "ikan patin": {
        "label": "Ikan Patin",
        "group": "Akuakultur air tawar",
        "product_focus": ["daging/pembesaran", "fillet", "benih"],
        "breeds": [
            {"name": "Patin Siam", "focus": "pembesaran", "note": "Umum dibudidayakan, cocok kolam dengan pakan dan air stabil."},
            {"name": "Patin Jambal", "focus": "lokal/benih", "note": "Plasma nutfah lokal, perlu manajemen pembenihan baik."},
            {"name": "Patin Pasupati", "focus": "pembesaran", "note": "Hasil seleksi/persilangan, evaluasi pertumbuhan dan pasar."},
            {"name": "Patin Lokal/Campuran", "focus": "pembesaran", "note": "Pantau FCR, SR, dan kualitas air."},
        ],
    },
    "ikan mas": {
        "label": "Ikan Mas",
        "group": "Akuakultur air tawar",
        "product_focus": ["daging/pembesaran", "benih"],
        "breeds": [
            {"name": "Mas Majalaya", "focus": "pembesaran", "note": "Populer untuk konsumsi, perlu kualitas air baik."},
            {"name": "Mas Rajadanu", "focus": "pembesaran/benih", "note": "Performa dipengaruhi asal benih dan pakan."},
            {"name": "Mas Punten", "focus": "pembesaran", "note": "Salah satu strain lokal, perlu adaptasi kondisi kolam."},
            {"name": "Mas Sinyonya", "focus": "pembesaran", "note": "Gunakan recording pertumbuhan untuk seleksi."},
            {"name": "Mas Lokal/Campuran", "focus": "pembesaran", "note": "Pantau kualitas air, penyakit kulit/insang, dan FCR."},
        ],
    },
}

COMMODITY_ORDER: List[str] = list(COMMODITY_CATALOG.keys())
ANIMAL_TYPES: List[str] = COMMODITY_ORDER

RUMINANTS = {"sapi", "kerbau", "kambing", "domba"}
LARGE_RUMINANTS = {"sapi", "kerbau"}
SMALL_RUMINANTS = {"kambing", "domba"}
POULTRY = {"ayam", "bebek", "puyuh"}
AQUACULTURE = {"ikan lele", "ikan nila", "ikan gurame", "ikan patin", "ikan mas"}
MONOGASTRIC = {"kelinci", "babi"}


def commodity_label(commodity: str) -> str:
    item = COMMODITY_CATALOG.get(str(commodity or "").lower().strip())
    return item["label"] if item else str(commodity or "-")


def breed_options(commodity: str) -> List[str]:
    item = COMMODITY_CATALOG.get(str(commodity or "").lower().strip(), {})
    names = [b["name"] for b in item.get("breeds", [])]
    if "Lainnya/Campuran" not in names:
        names.append("Lainnya/Campuran")
    return names


def breed_detail(commodity: str, breed: str) -> Dict[str, str]:
    key = str(commodity or "").lower().strip()
    target = str(breed or "").lower().strip()
    for item in COMMODITY_CATALOG.get(key, {}).get("breeds", []):
        if str(item.get("name", "")).lower().strip() == target:
            return dict(item)
    return {"name": breed or "-", "focus": "belum ditentukan", "note": "Gunakan evaluasi performa aktual dan asal bibit untuk rekomendasi."}


def commodity_context(commodity: str, breed: str = "") -> str:
    key = str(commodity or "").lower().strip()
    item = COMMODITY_CATALOG.get(key)
    if not item:
        return "Komoditas belum ada di katalog. Gunakan prinsip umum pakan, produksi, kesehatan, reproduksi, dan ekonomi usaha."
    detail = breed_detail(key, breed) if breed else {}
    lines = [
        f"Komoditas: {item['label']} ({item['group']}).",
        "Fokus produk: " + ", ".join(item.get("product_focus", [])),
    ]
    if breed:
        lines.append(f"Bangsa/ras/strain: {detail.get('name', breed)} - fokus {detail.get('focus', '-')}. Catatan: {detail.get('note', '-')}")
    lines.append("Bangsa/strain tersedia: " + ", ".join(b["name"] for b in item.get("breeds", [])[:10]))
    return "\n".join(lines)


def catalog_markdown() -> str:
    parts: List[str] = []
    for key in COMMODITY_ORDER:
        item = COMMODITY_CATALOG[key]
        breeds = ", ".join(b["name"] for b in item.get("breeds", []))
        parts.append(f"### {item['label']}\n- Kelompok: {item['group']}\n- Fokus produk: {', '.join(item.get('product_focus', []))}\n- Bangsa/ras/strain: {breeds}")
    return "\n\n".join(parts)


def catalog_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for key in COMMODITY_ORDER:
        item = COMMODITY_CATALOG[key]
        for breed in item.get("breeds", []):
            rows.append({
                "Komoditas": item["label"],
                "Key": key,
                "Kelompok": item["group"],
                "Bangsa/Ras/Strain": breed.get("name", ""),
                "Fokus": breed.get("focus", ""),
                "Catatan": breed.get("note", ""),
            })
    return rows
