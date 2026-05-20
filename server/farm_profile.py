from __future__ import annotations

from typing import Any, Dict, List
from datetime import date, timedelta

from commodity_breeds import ANIMAL_TYPES, AQUACULTURE, POULTRY, RUMINANTS, breed_options, commodity_context, commodity_label

ANIMAL_PHASES: Dict[str, List[str]] = {
    "sapi": ["pedet", "grower", "penggemukan", "indukan kosong", "bunting awal", "bunting tua", "laktasi", "pejantan"],
    "kerbau": ["anak", "grower", "penggemukan", "indukan kosong", "bunting awal", "bunting tua", "laktasi", "pejantan"],
    "kambing": ["cempe", "grower", "penggemukan", "indukan kosong", "bunting awal", "bunting tua", "laktasi", "pejantan"],
    "domba": ["anak", "grower", "penggemukan", "indukan kosong", "bunting awal", "bunting tua", "laktasi", "pejantan"],
    "ayam": ["starter", "grower", "finisher", "layer awal produksi", "layer puncak produksi", "breeder", "afkir"],
    "bebek": ["starter", "grower", "petelur", "pedaging", "breeder", "afkir"],
    "puyuh": ["starter", "grower", "petelur", "breeder", "afkir"],
    "kelinci": ["anak", "grower", "penggemukan", "indukan kosong", "bunting", "menyusui", "pejantan"],
    "babi": ["starter", "grower", "finisher", "induk dara", "bunting", "laktasi", "pejantan"],
    "ikan lele": ["benih", "pendederan", "pembesaran", "pra-panen", "indukan"],
    "ikan nila": ["benih", "pendederan", "pembesaran", "pra-panen", "indukan"],
    "ikan gurame": ["benih", "pendederan", "pembesaran", "pra-panen", "indukan"],
    "ikan patin": ["benih", "pendederan", "pembesaran", "pra-panen", "indukan"],
    "ikan mas": ["benih", "pendederan", "pembesaran", "pra-panen", "indukan"],
}

PRODUCTION_GOALS: List[str] = [
    "pedaging", "petelur", "pembibitan", "susu", "penggemukan", "pembesaran ikan", "perah", "breeding", "hasil olahan", "pupuk/limbah", "campuran"
]

DEFAULT_PROFILE: Dict[str, Any] = {
    "farm_name": "",
    "animal_type": "kambing",
    "breed": "Peranakan Etawa/PE",
    "production_goal": "penggemukan",
    "phase": "penggemukan",
    "population": 10,
    "average_age": "",
    "average_weight_kg": 25.0,
    "location": "",
    "housing_system": "kandang panggung/kandang intensif",
    "feed_available": "rumput odot, dedak, ampas tahu",
    "water_source": "air sumur/PDAM",
    "main_problem": "",
    "budget_note": "",
    "market_target": "",
}


def normalise_profile(profile: Dict[str, Any] | None) -> Dict[str, Any]:
    result = dict(DEFAULT_PROFILE)
    if profile:
        result.update({k: v for k, v in profile.items() if v is not None})
    try:
        result["population"] = int(result.get("population") or 0)
    except Exception:
        result["population"] = 0
    try:
        result["average_weight_kg"] = float(result.get("average_weight_kg") or 0)
    except Exception:
        result["average_weight_kg"] = 0.0
    return result


def profile_completeness(profile: Dict[str, Any]) -> int:
    profile = normalise_profile(profile)
    required = [
        "animal_type", "breed", "production_goal", "phase", "population", "average_weight_kg",
        "housing_system", "feed_available", "main_problem",
    ]
    filled = 0
    for key in required:
        value = profile.get(key)
        if isinstance(value, (int, float)):
            filled += 1 if value > 0 else 0
        elif str(value or "").strip():
            filled += 1
    return int(round((filled / len(required)) * 100))


def summarize_profile(profile: Dict[str, Any], compact: bool = False) -> str:
    p = normalise_profile(profile)
    if compact:
        return (
            f"Profil farm: {p['population']} ekor {commodity_label(p['animal_type'])} bangsa/strain {p.get('breed', '-') or '-'} fase {p['phase']} untuk {p['production_goal']}; "
            f"bobot rata-rata {p['average_weight_kg']:.2f} kg; kandang {p['housing_system']}; "
            f"pakan tersedia: {p['feed_available']}; masalah utama: {p['main_problem'] or 'belum diisi'}."
        )
    lines = [
        "Profil peternakan saat ini:",
        f"- Nama farm: {p['farm_name'] or '-'}",
        f"- Komoditas: {commodity_label(p['animal_type'])}",
        f"- Bangsa/ras/strain: {p.get('breed', '-') or '-'}",
        f"- Tujuan usaha: {p['production_goal']}",
        f"- Fase ternak: {p['phase']}",
        f"- Populasi: {p['population']} ekor",
        f"- Umur rata-rata: {p['average_age'] or '-'}",
        f"- Bobot rata-rata: {p['average_weight_kg']:.2f} kg",
        f"- Lokasi/iklim: {p['location'] or '-'}",
        f"- Sistem kandang/kolam: {p['housing_system']}",
        f"- Pakan tersedia: {p['feed_available']}",
        f"- Sumber air: {p['water_source']}",
        f"- Masalah utama: {p['main_problem'] or '-'}",
        f"- Catatan modal/biaya: {p['budget_note'] or '-'}",
        f"- Target pasar: {p['market_target'] or '-'}",
    ]
    return "\n".join(lines)


def make_profile_context(profile: Dict[str, Any]) -> str:
    p = normalise_profile(profile)
    completeness = profile_completeness(p)
    return (
        "Gunakan profil peternakan pengguna ini sebagai konteks utama. "
        "Jika data tidak lengkap, nyatakan asumsi sebelum memberi rekomendasi.\n"
        f"Kelengkapan profil: {completeness}%.\n"
        f"{summarize_profile(p)}\n\n"
        "Konteks komoditas dan bangsa/strain:\n"
        f"{commodity_context(p.get('animal_type'), p.get('breed', ''))}"
    )

def phase_guidance(animal_type: str, phase: str) -> str:
    animal_type = (animal_type or "").lower()
    phase = (phase or "").lower()
    if animal_type in RUMINANTS:
        if "bunting tua" in phase:
            return "Fokus: cukup hijauan berkualitas, mineral, hindari stres, siapkan kandang melahirkan, pantau nafsu makan dan ambing."
        if "laktasi" in phase:
            return "Fokus: air melimpah, protein/energi cukup, mineral, kebersihan ambing, dan pantau body condition score."
        if "penggemukan" in phase:
            return "Fokus: adaptasi pakan bertahap, hijauan cukup, konsentrat terukur, kontrol cacing, dan timbang rutin untuk mengejar ADG."
    if animal_type in POULTRY:
        if "starter" in phase:
            return "Fokus: brooding, suhu, air gula/vitamin awal sesuai kebutuhan, pakan starter, litter kering, dan vaksin dasar."
        if "layer" in phase or "petelur" in phase:
            return "Fokus: kalsium, protein, cahaya, air minum, kestabilan pakan, dan catat produksi telur harian."
    if animal_type in AQUACULTURE:
        if "benih" in phase or "pendederan" in phase:
            return "Fokus: ukuran pakan sesuai bukaan mulut, kualitas air stabil, kepadatan wajar, dan grading bila ukuran tidak seragam."
        if "pembesaran" in phase:
            return "Fokus: FCR, kualitas air, aerasi, sampling bobot, dan hindari overfeeding."
    return "Fokus umum: pakan sesuai fase, air bersih, sanitasi, recording performa, dan deteksi dini penyakit."


def quick_management_checklist(profile: Dict[str, Any]) -> List[str]:
    p = normalise_profile(profile)
    animal = p["animal_type"]
    base = [
        "Cek nafsu makan dan minum setiap pagi/sore.",
        "Catat kematian, ternak sakit, dan perubahan produksi.",
        "Bersihkan area basah, sisa pakan, dan feses berlebih.",
        "Pastikan pakan tidak berjamur/busuk dan air minum tersedia.",
    ]
    if animal in RUMINANTS or animal in {"kelinci"}:
        base += ["Timbang atau ukur lingkar dada berkala.", "Pisahkan ternak sakit dan lakukan kontrol parasit sesuai program."]
    elif animal in POULTRY:
        base += ["Cek litter/kandang agar tidak lembap.", "Amati gejala pernapasan dan penurunan produksi telur."]
    elif animal in AQUACULTURE:
        base += ["Cek warna air, bau, ikan megap-megap, dan sisa pakan.", "Sampling bobot dan evaluasi FCR minimal mingguan."]
    return base


def breeding_dates(animal_type: str, breeding_date: date) -> Dict[str, date]:
    animal = animal_type.lower()
    gestation_days = {"sapi": 283, "kerbau": 310, "kambing": 150, "domba": 150, "kelinci": 31, "babi": 114}
    if animal not in gestation_days:
        return {}
    expected_birth = breeding_date + timedelta(days=gestation_days[animal])
    return {
        "Tanggal kawin/IB": breeding_date,
        "Perkiraan lahir": expected_birth,
        "Mulai persiapan kandang lahir": expected_birth - timedelta(days=21 if animal == "kerbau" else (14 if animal not in {"kelinci", "babi"} else 7)),
        "Evaluasi kebuntingan awal": breeding_date + timedelta(days=60 if animal == "kerbau" else (45 if animal == "sapi" else 30)),
    }
