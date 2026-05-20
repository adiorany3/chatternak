from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from farm_profile import normalise_profile, profile_completeness
from farm_records import summarize_records
from health_triage import triage_level

EXPERT_RESPONSE_FORMAT = """
Format wajib jawaban Pakar Ternak Nusantara:
1. Kesimpulan awal / keputusan utama.
2. Data yang diketahui dan asumsi jika data kurang.
3. Analisis penyebab atau peluang perbaikan.
4. Tindakan praktis hari ini / 24 jam.
5. Rencana 7 hari dan target terukur.
6. Risiko, tanda bahaya, dan kapan perlu dokter hewan/paramedik.
7. Data yang perlu dicatat berikutnya.

Untuk kasus kesehatan, gunakan juga:
- Status risiko: Hijau / Kuning / Merah.
- Yang tidak boleh dilakukan.
- Jangan memberi dosis antibiotik, obat keras, atau obat injeksi spesifik tanpa pemeriksaan dokter hewan.

Untuk mode Peternak Rakyat: gunakan bahasa sederhana dan jelaskan istilah.
Untuk mode Industri Modern: gunakan KPI, SOP, audit trail, batch, target, dan kontrol risiko.
""".strip()

TECHNICAL_GLOSSARY: Dict[str, str] = {
    "adg": "ADG adalah pertambahan bobot rata-rata per hari. Semakin stabil naik, pertumbuhan makin baik.",
    "fcr": "FCR adalah perbandingan jumlah pakan dengan kenaikan bobot/hasil. Semakin kecil, pakan makin efisien.",
    "mortalitas": "Mortalitas adalah jumlah atau persentase ternak yang mati dalam periode tertentu.",
    "biosecurity": "Biosecurity adalah tindakan mencegah penyakit masuk dan menyebar di kandang/kolam.",
    "uniformity": "Uniformity adalah keseragaman bobot/populasi. Semakin seragam, manajemen pakan dan panen lebih mudah.",
    "silase": "Silase adalah hijauan yang diawetkan secara anaerob agar stok pakan tetap tersedia.",
    "konsentrat": "Konsentrat adalah pakan padat nutrisi seperti dedak, jagung, bungkil, atau campuran pabrik.",
    "protein kasar": "Protein kasar adalah ukuran kandungan protein pakan secara umum untuk membantu menyusun ransum.",
    "starter": "Starter adalah fase awal pertumbuhan yang butuh pakan, suhu, dan sanitasi lebih ketat.",
    "grower": "Grower adalah fase pertumbuhan lanjutan sebelum finishing/produksi.",
    "finisher": "Finisher adalah fase akhir penggemukan sebelum panen.",
}

COMMODITY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "sapi": {
        "kpi": ["ADG", "FCR kasar", "BCS", "konsumsi bahan kering", "service per conception", "calving interval"],
        "critical_questions": ["bobot/lingkar dada", "fase bunting/laktasi/penggemukan", "jenis hijauan", "konsumsi konsentrat", "riwayat penyakit/cacing"],
        "red_flags": ["kembung parah", "tidak mau makan >24 jam", "demam tinggi", "ambruk", "diare berdarah", "sesak"],
        "daily_check": ["nafsu makan", "ruminasi", "feses", "air minum", "kondisi kuku", "kebersihan kandang"],
    },
    "kambing": {
        "kpi": ["ADG", "FCR kasar", "mortalitas cempe", "jumlah anak lahir/sapih", "BCS induk"],
        "critical_questions": ["bobot", "umur/fase", "pakan hijauan", "konsentrat", "kembung/mencret", "riwayat cacing"],
        "red_flags": ["kembung", "tidak mau makan", "mencret parah", "lendir/berdarah", "pincang berat", "banyak sakit bersamaan"],
        "daily_check": ["nafsu makan", "feses", "perut kiri", "hidung/mata", "lantai kandang", "air minum"],
    },
    "ayam": {
        "kpi": ["FCR", "mortalitas", "uniformity", "bobot mingguan", "konsumsi pakan", "produksi telur"],
        "critical_questions": ["umur hari/minggu", "strain/jenis", "jumlah populasi", "mortalitas", "pakan", "suhu/litter", "vaksin"],
        "red_flags": ["kematian mendadak", "ngorok massal", "diare berdarah", "lumpuh", "produksi telur turun drastis"],
        "daily_check": ["konsumsi pakan", "air", "litter", "suhu", "mortalitas", "gejala pernapasan"],
    },
    "bebek": {
        "kpi": ["FCR", "mortalitas", "produksi telur", "konsumsi pakan", "keseragaman bobot"],
        "critical_questions": ["umur/fase", "sistem kandang", "akses air", "pakan", "litter", "produksi telur"],
        "red_flags": ["kematian mendadak", "lemas massal", "diare", "produksi telur turun drastis", "gejala saraf"],
        "daily_check": ["pakan", "air", "litter", "kondisi kaki", "produksi telur", "mortalitas"],
    },
    "ikan": {
        "kpi": ["FCR", "SR/survival rate", "kualitas air", "sampling bobot", "kepadatan", "biaya pakan"],
        "critical_questions": ["jenis ikan", "ukuran tebar", "kepadatan", "umur pemeliharaan", "pH/DO/amonia", "aerasi", "pakan"],
        "red_flags": ["ikan megap-megap", "mati mendadak", "air bau", "air sangat keruh", "nafsu makan turun massal"],
        "daily_check": ["perilaku pagi", "warna/bau air", "sisa pakan", "aerasi", "mortalitas", "pH bila ada"],
    },
    "kelinci": {
        "kpi": ["ADG", "mortalitas anak", "jumlah anak lahir/sapih", "konsumsi pakan", "kasus diare"],
        "critical_questions": ["umur", "bobot", "jenis pakan", "feses", "kandang", "status bunting/menyusui"],
        "red_flags": ["diare parah", "tidak mau makan", "perut kembung", "lemas", "banyak mati"],
        "daily_check": ["pakan", "air", "feses", "suhu kandang", "anak kelinci", "kebersihan"],
    },
}

HEALTH_KEYWORDS = {
    "sakit", "penyakit", "gejala", "mencret", "diare", "batuk", "ngorok", "lumpuh", "pincang", "kembung",
    "tidak mau makan", "nafsu makan", "mati", "kematian", "demam", "sesak", "luka", "bengkak", "lemas",
    "ikan megap", "produksi turun", "telur turun", "berdarah", "kejang",
}

RISK_DIMENSIONS = ["Kesehatan", "Pakan", "Kandang/Kolam", "Recording", "Biaya", "Reproduksi/Produksi"]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _contains_any(text: str, terms: List[str] | set[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def commodity_context(profile: Dict[str, Any]) -> str:
    p = normalise_profile(profile)
    animal = p.get("animal_type", "").lower()
    template = COMMODITY_TEMPLATES.get(animal, {})
    if not template:
        return "Belum ada template komoditas spesifik. Gunakan prinsip umum peternakan: pakan, air, kandang, kesehatan, recording, dan biaya."
    return "\n".join([
        f"Template komoditas: {animal}.",
        "KPI yang perlu dipantau: " + ", ".join(template.get("kpi", [])),
        "Pertanyaan kritis: " + ", ".join(template.get("critical_questions", [])),
        "Tanda bahaya: " + ", ".join(template.get("red_flags", [])),
        "Cek harian: " + ", ".join(template.get("daily_check", [])),
    ])


def glossary_context_for_text(text: str) -> str:
    found = []
    lowered = text.lower()
    for term, meaning in TECHNICAL_GLOSSARY.items():
        if term in lowered:
            found.append(f"- {meaning}")
    if not found:
        return ""
    return "Istilah teknis yang perlu dijelaskan bila mode Peternak Rakyat:\n" + "\n".join(found[:6])


def detect_missing_questions(message: str, profile: Dict[str, Any], health_case: Dict[str, Any] | None = None) -> List[str]:
    p = normalise_profile(profile)
    text = " ".join([message, _text(p.get("main_problem")), _text(health_case)]).lower()
    questions: List[str] = []
    if _contains_any(text, HEALTH_KEYWORDS):
        if not p.get("animal_type"):
            questions.append("Jenis ternaknya apa?")
        if not _text(p.get("average_age")) and "umur" not in text:
            questions.append("Umur atau fase ternaknya berapa?")
        if not p.get("average_weight_kg") and "bobot" not in text:
            questions.append("Bobot rata-rata kira-kira berapa?")
        if "durasi" not in text and not any(x in text for x in ["hari", "jam", "minggu", "sejak"]):
            questions.append("Gejala sudah terjadi berapa lama?")
        if "feses" not in text and "mencret" not in text and "diare" not in text:
            questions.append("Feses normal, cair, berlendir, atau berdarah?")
        if "makan" not in text and "nafsu" not in text:
            questions.append("Nafsu makan dan minumnya masih normal atau turun?")
        if "mati" not in text and "kematian" not in text:
            questions.append("Ada kematian atau ternak lain yang ikut sakit?")
    else:
        if p.get("population", 0) <= 0:
            questions.append("Populasi ternak berapa ekor?")
        if not p.get("average_weight_kg"):
            questions.append("Bobot rata-rata atau ukuran ternak berapa?")
        if not _text(p.get("phase")):
            questions.append("Fase ternak saat ini apa: starter, grower, finisher, bunting, laktasi, petelur, atau pembesaran?")
        if not _text(p.get("feed_available")):
            questions.append("Bahan pakan yang tersedia apa saja?")
    return questions[:5]


def health_risk_level(text: str) -> Tuple[str, List[str]]:
    level, flags = triage_level(text)
    if level == "DARURAT":
        return "Merah", flags
    if level == "PERLU DIPANTAU KETAT":
        return "Kuning", flags
    return "Hijau", flags


def farm_risk_score(
    profile: Dict[str, Any],
    records: List[Dict[str, Any]],
    calendar_events: List[Dict[str, Any]],
    health_case: Dict[str, Any] | None = None,
    biosecurity_checked: List[str] | None = None,
) -> Dict[str, Any]:
    p = normalise_profile(profile)
    summary = summarize_records(records)
    completeness = profile_completeness(p)
    health_text = " ".join(str(v) for v in (health_case or {}).values())
    health_level, health_flags = health_risk_level(health_text)
    bio_count = len(biosecurity_checked or [])
    bio_score = min(100, int((bio_count / 8) * 100)) if bio_count else 0

    score = 0
    reasons: List[str] = []
    dimensions = {dim: "Hijau" for dim in RISK_DIMENSIONS}

    if completeness < 60:
        score += 20
        dimensions["Recording"] = "Kuning"
        reasons.append("Profil belum lengkap, sehingga rekomendasi masih banyak memakai asumsi.")
    if not records:
        score += 18
        dimensions["Recording"] = "Kuning"
        reasons.append("Belum ada catatan performa; ADG, FCR, mortalitas, dan biaya belum bisa diaudit.")
    elif summary.get("mortality_total", 0) > 0:
        score += min(22, 8 + int(summary.get("mortality_total", 0)) * 2)
        dimensions["Kesehatan"] = "Kuning"
        reasons.append("Ada mortalitas pada catatan performa; perlu evaluasi kesehatan dan biosecurity.")
    if summary.get("fcr") is not None and float(summary["fcr"]) > 4 and p.get("animal_type") in {"ayam", "bebek", "ikan"}:
        score += 18
        dimensions["Pakan"] = "Kuning"
        reasons.append("FCR terlihat tinggi untuk unggas/ikan; cek kualitas pakan, kesehatan, kepadatan, dan recording pakan.")
    if p.get("animal_type") in {"sapi", "kambing", "kelinci"} and summary.get("adg") is not None and float(summary["adg"]) <= 0:
        score += 20
        dimensions["Pakan"] = "Kuning"
        reasons.append("ADG tidak naik; evaluasi pakan, kesehatan, parasit, dan akurasi bobot.")
    if health_level == "Merah":
        score += 35
        dimensions["Kesehatan"] = "Merah"
        reasons.append("Terdeteksi tanda darurat kesehatan: " + ", ".join(health_flags[:5]))
    elif health_level == "Kuning":
        score += 18
        dimensions["Kesehatan"] = "Kuning"
        reasons.append("Ada tanda kesehatan yang perlu dipantau ketat: " + ", ".join(health_flags[:5]))
    if bio_score and bio_score < 50:
        score += 12
        dimensions["Kandang/Kolam"] = "Kuning"
        reasons.append("Checklist biosecurity masih rendah.")
    if not calendar_events:
        score += 8
        dimensions["Recording"] = "Kuning"
        reasons.append("Belum ada kalender manajemen; risiko jadwal vaksin, sanitasi, kontrol bobot, atau panen terlewat.")
    if not _text(p.get("budget_note")):
        score += 5
        dimensions["Biaya"] = "Kuning"
        reasons.append("Catatan biaya/modal belum diisi; analisis margin masih terbatas.")

    score = max(0, min(100, score))
    if score >= 70:
        level = "Merah"
    elif score >= 35:
        level = "Kuning"
    else:
        level = "Hijau"
    return {
        "score": score,
        "level": level,
        "dimensions": dimensions,
        "reasons": reasons[:8] or ["Belum ada risiko besar dari data yang tersedia."],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def build_expert_context(
    *,
    user_mode: str,
    explanation_level: str,
    profile: Dict[str, Any],
    records: List[Dict[str, Any]],
    calendar_events: List[Dict[str, Any]],
    health_case: Dict[str, Any] | None,
    biosecurity_checked: List[str] | None,
    user_message: str,
) -> str:
    risk = farm_risk_score(profile, records, calendar_events, health_case, biosecurity_checked)
    questions = detect_missing_questions(user_message, profile, health_case)
    parts = [
        "Konteks ahli tambahan:",
        EXPERT_RESPONSE_FORMAT,
        commodity_context(profile),
        glossary_context_for_text(user_message),
        "Skor risiko lokal: " + str(risk),
    ]
    if questions:
        parts.append("Data penting yang masih kurang. Bila relevan, tanyakan maksimal 5 hal ini sebelum menyimpulkan: " + "; ".join(questions))
    parts.append(f"Mode pengguna: {user_mode}. Kedalaman penjelasan: {explanation_level}.")
    return "\n\n".join(part for part in parts if part.strip())


def validate_ai_answer(answer: str, user_message: str, user_mode: str) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    text = (answer or "").strip()
    lower = text.lower()
    if len(text) < 220:
        issues.append("Jawaban terlalu pendek untuk konsultasi pakar.")
    action_terms = ["lakukan", "cek", "catat", "pisahkan", "evaluasi", "berikan", "hindari", "pantau", "bersihkan", "ukur"]
    if not any(term in lower for term in action_terms):
        issues.append("Belum ada tindakan praktis.")
    if _contains_any(user_message, HEALTH_KEYWORDS):
        if not any(term in lower for term in ["dokter hewan", "paramedik", "isolasi", "tanda bahaya", "risiko"]):
            issues.append("Jawaban kesehatan belum memuat isolasi/tanda bahaya/dokter hewan.")
        risky_drug = re.search(r"\b(antibiotik|oxytetracycline|amoxicillin|penicillin|ivermectin|suntik|injeksi|dosis)\b", lower)
        if risky_drug and not any(term in lower for term in ["dokter hewan", "paramedik", "pemeriksaan"]):
            issues.append("Ada saran obat/dosis tanpa pembatas dokter hewan.")
    if user_mode == "Peternak Rakyat" and any(term in lower for term in ["adg", "fcr", "biosecurity", "uniformity"]):
        if not any(simple in lower for simple in ["artinya", "maksudnya", "sederhananya"]):
            issues.append("Istilah teknis belum dijelaskan untuk Peternak Rakyat.")
    generic_phrases = ["tergantung kondisi", "konsultasikan dengan ahli", "perhatikan dengan baik"]
    if sum(1 for phrase in generic_phrases if phrase in lower) >= 2 and len(text) < 600:
        issues.append("Jawaban masih terlalu umum.")
    return len(issues) == 0, issues


def repair_prompt(user_message: str, answer: str, issues: List[str], user_mode: str) -> str:
    return (
        "Perbaiki jawaban sebelumnya agar sesuai standar Pakar Ternak Nusantara.\n"
        f"Pertanyaan pengguna: {user_message}\n"
        f"Mode pengguna: {user_mode}\n"
        "Masalah validasi: " + "; ".join(issues) + "\n"
        "Jawaban sebelumnya:\n" + answer + "\n\n"
        "Tulis ulang jawaban dengan format pakar, tindakan praktis, risiko, dan data yang perlu dicatat. "
        "Jangan menyebut proses validasi."
    )


def decision_card_from_answer(question: str, answer: str, risk: Dict[str, Any]) -> Dict[str, Any]:
    first_lines = [line.strip(" -*#") for line in (answer or "").splitlines() if line.strip()]
    summary = first_lines[0][:220] if first_lines else "Rekomendasi AI dibuat, tetapi ringkasan belum tersedia."
    priority = "Tinggi" if risk.get("level") == "Merah" else "Sedang" if risk.get("level") == "Kuning" else "Normal"
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "question": question[:500],
        "main_decision": summary,
        "priority": priority,
        "risk_level": risk.get("level", "-"),
        "risk_score": risk.get("score", 0),
        "follow_up_status": "Belum ditindaklanjuti",
        "result_note": "",
    }


def rewrite_instruction(style: str, last_answer: str) -> str:
    if style == "simple":
        return "Jelaskan ulang jawaban terakhir dengan bahasa sangat sederhana untuk peternak rakyat. Gunakan langkah 1-2-3 dan jelaskan istilah teknis."
    if style == "field_steps":
        return "Ubah jawaban terakhir menjadi instruksi lapangan yang singkat: apa yang dicek, apa yang dilakukan, kapan evaluasi, dan kapan panggil dokter hewan."
    if style == "technical":
        return "Ubah jawaban terakhir menjadi versi teknis untuk pengelola farm industri, sertakan KPI, SOP, risiko, dan target monitoring."
    if style == "sop":
        return "Ubah jawaban terakhir menjadi SOP praktis berisi tujuan, alat/data, langkah kerja, catatan keselamatan, dan indikator keberhasilan."
    return "Jelaskan ulang jawaban terakhir dengan format yang lebih jelas dan praktis."
