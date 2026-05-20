from __future__ import annotations

from typing import Any, Dict, List

DEPARTMENT_FRAMEWORK_SOURCE = "Kerangka akademik 5 departemen Fakultas Peternakan UGM"

UGM_DEPARTMENTS: List[Dict[str, Any]] = [
    {
        "id": "nutrisi_pakan",
        "name": "Nutrisi dan Makanan Ternak",
        "short_name": "Nutrisi & Pakan",
        "hulu_hilir_role": "Hulu - penyediaan, evaluasi, formulasi, dan efisiensi pakan.",
        "scope": [
            "kebutuhan nutrien berdasarkan komoditas dan fase",
            "bahan pakan lokal dan batas aman penggunaannya",
            "formulasi hijauan-konsentrat atau pakan lengkap",
            "FCR, konsumsi bahan kering, biaya pakan, dan efisiensi ransum",
            "silase, fermentasi, bank pakan, dan strategi musim hujan/kemarau",
        ],
        "questions": [
            "Bahan pakan apa yang tersedia dan berapa harganya?",
            "Berapa bobot, fase, dan target produksi ternak?",
            "Berapa konsumsi pakan harian dan sisa pakan?",
            "Apakah ada perubahan ransum 7-10 hari terakhir?",
        ],
        "outputs": ["formula ransum", "estimasi biaya pakan", "evaluasi FCR", "strategi stok pakan"],
        "keywords": ["pakan", "ransum", "nutrisi", "dedak", "bekatul", "ampas tahu", "konsentrat", "hijauan", "silase", "fcr", "protein", "energi"],
    },
    {
        "id": "produksi_ternak",
        "name": "Produksi Ternak",
        "short_name": "Produksi & Manajemen",
        "hulu_hilir_role": "On-farm - manajemen pemeliharaan, kandang/kolam, performa, panen, dan SOP harian.",
        "scope": [
            "manajemen kandang, kolam, brooding, kepadatan, ventilasi, dan kenyamanan ternak",
            "recording bobot, ADG, mortalitas, produksi telur/susu, dan performa batch",
            "SOP pakan, sanitasi, panen, sortasi, dan pengendalian stres",
            "kontrol kualitas air untuk ikan dan kontrol litter untuk unggas",
            "perencanaan panen dan evaluasi produktivitas",
        ],
        "questions": [
            "Berapa populasi, umur/fase, dan sistem pemeliharaan?",
            "Bagaimana tren bobot, produksi, mortalitas, dan konsumsi pakan?",
            "Apakah kandang/kolam padat, lembap, panas, bau, atau kurang aerasi?",
            "Kapan target panen dan bobot/produksi yang diinginkan?",
        ],
        "outputs": ["SOP pemeliharaan", "benchmark KPI", "jadwal recording", "rencana panen"],
        "keywords": ["produksi", "kandang", "kolam", "bobot", "adg", "panen", "mortalitas", "brooding", "litter", "kepadatan", "manajemen"],
    },
    {
        "id": "sosial_ekonomi",
        "name": "Sosial Ekonomi Peternakan",
        "short_name": "Sosial Ekonomi & Agribisnis",
        "hulu_hilir_role": "Bisnis - kelayakan usaha, biaya produksi, pemasaran, kemitraan, dan keputusan ekonomi.",
        "scope": [
            "BEP, margin, harga jual minimal, cashflow sederhana, dan biaya produksi",
            "analisis usaha peternak rakyat, kelompok ternak, dan farm modern",
            "strategi pemasaran, target pasar, kemitraan, koperasi, dan skala usaha",
            "risiko harga pakan, harga jual, tenaga kerja, dan siklus produksi",
            "laporan manajemen untuk pengambilan keputusan",
        ],
        "questions": [
            "Berapa biaya pakan, bibit, tenaga kerja, obat/vitamin, dan operasional?",
            "Berapa target harga jual dan pasar tujuan?",
            "Apakah usaha individu, kelompok, kemitraan, atau industri?",
            "Berapa target margin dan periode balik modal?",
        ],
        "outputs": ["BEP", "margin kasar", "harga jual minimal", "rencana cashflow", "analisis kelayakan"],
        "keywords": ["usaha", "biaya", "modal", "bep", "margin", "untung", "rugi", "harga", "pasar", "kemitraan", "cashflow", "agribisnis"],
    },
    {
        "id": "teknologi_hasil",
        "name": "Teknologi Hasil Ternak",
        "short_name": "Teknologi Hasil Ternak",
        "hulu_hilir_role": "Hilir - penanganan, mutu, pengolahan, penyimpanan, dan nilai tambah produk ternak.",
        "scope": [
            "penanganan daging, karkas, susu, telur, dan hasil ikutan secara higienis",
            "mutu produk, penyimpanan dingin/suhu ruang, sortasi, grading, dan masa simpan",
            "pengolahan sederhana: telur asin, susu pasteurisasi sederhana, abon/dendeng, kompos/pupuk",
            "risiko kontaminasi, kebersihan alat, air, pekerja, dan rantai distribusi",
            "nilai tambah produk dan standar kebersihan pascapanen",
        ],
        "questions": [
            "Produk utama apa: daging, susu, telur, ikan, pupuk, atau olahan?",
            "Bagaimana proses panen, sortasi, pencucian, penyimpanan, dan distribusi?",
            "Berapa lama produk disimpan sebelum dijual/dikonsumsi?",
            "Apakah ada keluhan bau, cepat rusak, retak, kontaminasi, atau mutu tidak seragam?",
        ],
        "outputs": ["SOP pascapanen", "checklist higienitas", "saran penyimpanan", "ide nilai tambah produk"],
        "keywords": ["hasil ternak", "daging", "susu", "telur", "karkas", "pascapanen", "olahan", "penyimpanan", "mutu", "higienis", "produk"],
    },
    {
        "id": "pemuliaan_reproduksi",
        "name": "Pemuliaan dan Reproduksi Ternak",
        "short_name": "Pemuliaan & Reproduksi",
        "hulu_hilir_role": "Hulu genetik - seleksi bibit, reproduksi, kebuntingan, kelahiran, dan perbaikan produktivitas.",
        "scope": [
            "seleksi bibit, pejantan, induk, replacement stock, dan recording silsilah sederhana",
            "deteksi birahi, kawin alami, IB, kebuntingan, kelahiran, dan sapih",
            "evaluasi service per conception, calving interval, litter size, hatchability, dan fertilitas",
            "manajemen induk bunting/laktasi, cempe/pedet/anak, dan produktivitas keturunan",
            "keputusan afkir, seleksi, dan perbaikan mutu populasi",
        ],
        "questions": [
            "Tanggal kawin/IB terakhir kapan?",
            "Induk sudah berapa kali beranak dan bagaimana riwayat anaknya?",
            "Bagaimana tanda birahi, kondisi tubuh, dan status kesehatan reproduksi?",
            "Apa target: pembibitan, penggemukan, telur tetas, susu, atau replacement?",
        ],
        "outputs": ["kalender reproduksi", "prediksi kelahiran", "seleksi bibit", "evaluasi induk/pejantan"],
        "keywords": ["reproduksi", "pemuliaan", "bibit", "induk", "pejantan", "bunting", "birahi", "kawin", "ib", "kelahiran", "sapih", "genetik"],
    },
]

DEPARTMENT_IDS = [item["id"] for item in UGM_DEPARTMENTS]
DEPARTMENT_NAMES = [item["name"] for item in UGM_DEPARTMENTS]

HULU_HILIR_FLOW = [
    ("Hulu Genetik", "Pemuliaan dan Reproduksi Ternak", "Pilih bibit/induk/pejantan, atur reproduksi, dan perbaiki mutu populasi."),
    ("Hulu Pakan", "Nutrisi dan Makanan Ternak", "Siapkan bahan pakan, susun ransum, dan kendalikan biaya pakan."),
    ("On-Farm", "Produksi Ternak", "Kelola kandang/kolam, produksi, performa, kesehatan harian, dan panen."),
    ("Bisnis", "Sosial Ekonomi Peternakan", "Hitung biaya, margin, BEP, pasar, kemitraan, dan kelayakan usaha."),
    ("Hilir Produk", "Teknologi Hasil Ternak", "Tangani, simpan, olah, dan tingkatkan nilai produk ternak secara higienis."),
]


def department_context() -> str:
    lines = [
        f"Kerangka wajib: {DEPARTMENT_FRAMEWORK_SOURCE}.",
        "Setiap jawaban penting harus mempertimbangkan minimal satu dari lima domain berikut, dan bila relevan hubungkan hulu sampai hilir:",
    ]
    for dept in UGM_DEPARTMENTS:
        lines.append(f"- {dept['name']}: {dept['hulu_hilir_role']} Fokus: {', '.join(dept['scope'][:3])}.")
    lines.append("Jika pertanyaan menyangkut produk pascapanen, mutu, pengolahan, penyimpanan, atau nilai tambah, aktifkan perspektif Teknologi Hasil Ternak; jangan berhenti di budidaya saja.")
    return "\n".join(lines)


def department_markdown() -> str:
    rows = []
    for dept in UGM_DEPARTMENTS:
        rows.append(
            f"### {dept['name']}\n"
            f"**Peran hulu-hilir:** {dept['hulu_hilir_role']}\n\n"
            f"**Cakupan:**\n" + "\n".join(f"- {item}" for item in dept["scope"]) + "\n\n"
            f"**Output aplikasi:** {', '.join(dept['outputs'])}."
        )
    return "\n\n".join(rows)


def hulu_hilir_markdown() -> str:
    return "\n".join(
        f"**{idx}. {stage}** — {dept}: {desc}"
        for idx, (stage, dept, desc) in enumerate(HULU_HILIR_FLOW, start=1)
    )


def classify_department(text: str) -> Dict[str, Any]:
    lowered = (text or "").lower()
    scores = []
    for dept in UGM_DEPARTMENTS:
        score = sum(1 for keyword in dept.get("keywords", []) if keyword in lowered)
        if score:
            scores.append((score, dept))
    if not scores:
        return UGM_DEPARTMENTS[1]  # produksi/manajemen as default operational lens
    scores.sort(key=lambda item: item[0], reverse=True)
    return scores[0][1]


def department_prompt_for_text(text: str) -> str:
    dept = classify_department(text)
    return "\n".join([
        f"Lensa departemen utama: {dept['name']} ({dept['short_name']}).",
        f"Peran hulu-hilir: {dept['hulu_hilir_role']}",
        "Pertanyaan kritis yang perlu dipertimbangkan:",
        *[f"- {q}" for q in dept.get("questions", [])],
        "Output yang diharapkan: " + ", ".join(dept.get("outputs", [])),
    ])


def department_coverage_check(profile: Dict[str, Any] | None, records: List[Dict[str, Any]] | None, calendar_events: List[Dict[str, Any]] | None, health_case: Dict[str, Any] | None, app_state: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    profile = profile or {}
    records = records or []
    calendar_events = calendar_events or []
    health_case = health_case or {}
    app_state = app_state or {}
    formula_selected = app_state.get("formula_selected") or []
    decision_log = app_state.get("decision_log") or []
    coverage = []
    checks = {
        "nutrisi_pakan": bool(profile.get("feed_available") or formula_selected or any(float(r.get("feed_kg", 0) or 0) > 0 for r in records)),
        "produksi_ternak": bool(records or profile.get("housing_system") or calendar_events),
        "sosial_ekonomi": bool(profile.get("budget_note") or profile.get("market_target") or any(float(r.get("cost_rp", 0) or 0) > 0 for r in records)),
        "teknologi_hasil": bool(profile.get("market_target") or any(word in str(profile.get("main_problem", "")).lower() for word in ["daging", "susu", "telur", "karkas", "produk", "olahan", "pascapanen", "mutu"])),
        "pemuliaan_reproduksi": bool(profile.get("phase") in {"bunting", "laktasi", "indukan", "pejantan"} or any("reproduksi" in str(e).lower() or "kawin" in str(e).lower() or "kelahiran" in str(e).lower() for e in calendar_events + decision_log)),
    }
    for dept in UGM_DEPARTMENTS:
        covered = checks.get(dept["id"], False)
        coverage.append({
            "Departemen": dept["name"],
            "Status Data": "Ada data awal" if covered else "Belum cukup data",
            "Perlu Dilengkapi": "; ".join(dept["questions"][:2]) if not covered else "Lanjutkan recording dan evaluasi berkala.",
        })
    return coverage


def report_section_markdown(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any], app_state: Dict[str, Any] | None = None) -> str:
    coverage = department_coverage_check(profile, records, calendar_events, health_case, app_state)
    lines = ["## Cakupan 5 Departemen Fakultas Peternakan UGM"]
    for item in coverage:
        lines.append(f"- **{item['Departemen']}**: {item['Status Data']}. {item['Perlu Dilengkapi']}")
    lines.append("\n## Alur Hulu-Hilir")
    lines.append(hulu_hilir_markdown())
    return "\n".join(lines)
