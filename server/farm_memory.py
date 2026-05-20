from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

DEFAULT_EXPERT_MEMORY: List[Dict[str, Any]] = [
    {
        "category": "Identitas Pakar",
        "memory": "AI Pakar Ternak harus berperan sebagai ahli peternakan hulu-hilir Indonesia: nutrisi/pakan, produksi, sosial-ekonomi, teknologi hasil, pemuliaan-reproduksi, kesehatan, biosecurity, SOP, KPI, dan manajemen usaha.",
        "priority": "Tinggi",
        "source": "default",
    },
    {
        "category": "Standar Keputusan",
        "memory": "Jawaban harus layak untuk dua kelas pengguna: peternak rakyat yang membutuhkan langkah sederhana, serta industri modern/direksi perusahaan multinasional yang membutuhkan KPI, risiko, prioritas, biaya, target, SOP, dan audit trail.",
        "priority": "Tinggi",
        "source": "default",
    },
    {
        "category": "Kerangka Hulu-Hilir",
        "memory": "Setiap masalah utama perlu dibaca dari hulu ke hilir: bahan pakan dan nutrisi, sistem produksi, reproduksi/genetik, biaya/pasar, mutu hasil ternak, limbah, dan keberlanjutan.",
        "priority": "Tinggi",
        "source": "default",
    },
    {
        "category": "Konteks Lokal Indonesia",
        "memory": "Prioritaskan solusi yang relevan di Indonesia seperti rumput odot, rumput gajah, indigofera, kaliandra, lamtoro, dedak/bekatul, ampas tahu, onggok, bungkil kelapa, maggot BSF, silase, fermentasi pakan, kandang panggung, kandang postal, kolam terpal, bioflok, musim hujan, dan musim kemarau.",
        "priority": "Tinggi",
        "source": "default",
    },
    {
        "category": "Kesehatan dan Etika",
        "memory": "Untuk kasus kesehatan, berikan triase risiko dan tindakan aman. Jangan memberi diagnosis pasti atau dosis antibiotik/obat keras/injeksi hanya dari teks. Sarankan dokter hewan/paramedik jika ada tanda bahaya.",
        "priority": "Tinggi",
        "source": "default",
    },
    {
        "category": "Manajemen Data",
        "memory": "Dorong peternak mencatat populasi, bobot, konsumsi pakan, biaya, mortalitas, produksi telur/susu, reproduksi, vaksinasi, sanitasi, dan tindak lanjut rekomendasi AI agar insight makin akurat.",
        "priority": "Sedang",
        "source": "default",
    },
]

MEMORY_CATEGORIES = [
    "Identitas Pakar",
    "Persona Ahli",
    "Peran Strategis",
    "Keahlian Teknis",
    "Pembelajaran Kasus",
    "Strategi Perusahaan",
    "Kerangka Hulu-Hilir",
    "Konteks Lokal Indonesia",
    "Kesehatan dan Etika",
    "Nutrisi dan Pakan",
    "Produksi dan KPI",
    "Reproduksi dan Pemuliaan",
    "Sosial Ekonomi dan Agribisnis",
    "Teknologi Hasil Ternak",
    "Kebiasaan Peternak",
    "Manajemen Data",
    "Catatan Lapangan",
]

PRIORITIES = ["Tinggi", "Sedang", "Rendah"]


def now_stamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def make_memory_item(
    memory: str,
    *,
    category: str = "Catatan Lapangan",
    priority: str = "Sedang",
    source: str = "manual",
    created_at: str | None = None,
) -> Dict[str, Any]:
    return {
        "created_at": created_at or now_stamp(),
        "category": category if category in MEMORY_CATEGORIES else "Catatan Lapangan",
        "priority": priority if priority in PRIORITIES else "Sedang",
        "memory": str(memory or "").strip(),
        "source": str(source or "manual"),
    }


def normalise_memory_items(items: Any) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    normalised: List[Dict[str, Any]] = []
    seen = set()
    for raw in items:
        if isinstance(raw, str):
            item = make_memory_item(raw)
        elif isinstance(raw, dict):
            item = make_memory_item(
                str(raw.get("memory") or raw.get("catatan") or raw.get("note") or ""),
                category=str(raw.get("category") or raw.get("kategori") or "Catatan Lapangan"),
                priority=str(raw.get("priority") or raw.get("prioritas") or "Sedang"),
                source=str(raw.get("source") or raw.get("sumber") or "manual"),
                created_at=str(raw.get("created_at") or raw.get("tanggal") or "") or None,
            )
        else:
            continue
        if not item["memory"]:
            continue
        key = item["memory"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        normalised.append(item)
    return normalised[-200:]


def memory_from_secrets(secrets_like: Any) -> List[Dict[str, Any]]:
    """Read optional expert memory from Streamlit Secrets.

    Supported TOML shapes:
    [expert_memory]
    organization_context = "..."
    strategic_role = "..."
    notes = ["...", "..."]
    [[expert_memory.items]]
    category = "Strategi Perusahaan"
    priority = "Tinggi"
    memory = "..."
    """
    try:
        section = secrets_like.get("expert_memory", {}) if secrets_like is not None else {}
    except Exception:
        return []
    if not section:
        return []
    items: List[Dict[str, Any]] = []
    try:
        organization_context = str(section.get("organization_context", "")).strip()
        strategic_role = str(section.get("strategic_role", "")).strip()
        notes = section.get("notes", []) or []
        item_rows = section.get("items", []) or []
    except Exception:
        return []

    if organization_context:
        items.append(make_memory_item(organization_context, category="Strategi Perusahaan", priority="Tinggi", source="streamlit_secrets"))
    if strategic_role:
        items.append(make_memory_item(strategic_role, category="Strategi Perusahaan", priority="Tinggi", source="streamlit_secrets"))
    if isinstance(notes, (list, tuple)):
        for note in notes:
            items.append(make_memory_item(str(note), category="Catatan Lapangan", priority="Sedang", source="streamlit_secrets"))
    if isinstance(item_rows, (list, tuple)):
        items.extend(normalise_memory_items(list(item_rows)))
        for item in items:
            if item.get("source") == "manual":
                item["source"] = "streamlit_secrets"
    return normalise_memory_items(items)


def all_memory_items(dynamic_items: Any = None, secret_items: Any = None, include_default: bool = True) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    if include_default:
        result.extend(make_memory_item(row["memory"], category=row["category"], priority=row["priority"], source=row.get("source", "default")) for row in DEFAULT_EXPERT_MEMORY)
    result.extend(normalise_memory_items(secret_items))
    result.extend(normalise_memory_items(dynamic_items))
    # Deduplicate while preserving the last occurrence by memory text.
    merged: Dict[str, Dict[str, Any]] = {}
    for item in result:
        merged[item["memory"].strip().lower()] = item
    ordered = list(merged.values())
    priority_rank = {"Tinggi": 0, "Sedang": 1, "Rendah": 2}
    return sorted(ordered, key=lambda x: (priority_rank.get(x.get("priority", "Sedang"), 1), x.get("category", ""), x.get("created_at", "")))[:240]


def memory_context(dynamic_items: Any = None, secret_items: Any = None, *, include_default: bool = True) -> str:
    items = all_memory_items(dynamic_items, secret_items, include_default=include_default)
    if not items:
        return ""
    lines = [
        "MEMORY AHLI AI PAKAR TERNAK:",
        "Gunakan memory berikut sebagai pengetahuan operasional jangka panjang. Memory ini tidak menggantikan data farm aktual; bila bertentangan, prioritaskan data terbaru dari profil, catatan performa, dan kasus pengguna.",
    ]
    for idx, item in enumerate(items[:80], start=1):
        lines.append(f"{idx}. [{item['priority']}] {item['category']}: {item['memory']}")
    return "\n".join(lines)


def memory_table_rows(dynamic_items: Any = None, secret_items: Any = None, *, include_default: bool = True) -> List[Dict[str, Any]]:
    rows = []
    for item in all_memory_items(dynamic_items, secret_items, include_default=include_default):
        rows.append({
            "Tanggal": item.get("created_at", ""),
            "Kategori": item.get("category", ""),
            "Prioritas": item.get("priority", ""),
            "Memory": item.get("memory", ""),
            "Sumber": item.get("source", ""),
        })
    return rows


def suggest_memory_from_session(profile: Dict[str, Any], records: List[Dict[str, Any]], decision_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    suggestions: List[Dict[str, Any]] = []
    animal = str(profile.get("animal_type") or "").strip()
    breed = str(profile.get("breed") or "").strip()
    goal = str(profile.get("production_goal") or "").strip()
    phase = str(profile.get("phase") or "").strip()
    feed = str(profile.get("feed_available") or "").strip()
    main_problem = str(profile.get("main_problem") or "").strip()
    if animal or breed or goal or phase:
        suggestions.append(make_memory_item(
            f"Farm pengguna sering dianalisis dengan konteks komoditas {animal or '-'}, bangsa/strain {breed or '-'}, tujuan {goal or '-'}, dan fase {phase or '-'}.",
            category="Kebiasaan Peternak",
            priority="Sedang",
            source="auto_suggestion",
        ))
    if feed:
        suggestions.append(make_memory_item(
            f"Bahan pakan yang tersedia/sering dipakai pengguna: {feed}.",
            category="Nutrisi dan Pakan",
            priority="Sedang",
            source="auto_suggestion",
        ))
    if main_problem:
        suggestions.append(make_memory_item(
            f"Masalah utama yang sedang dipantau di farm pengguna: {main_problem}.",
            category="Catatan Lapangan",
            priority="Tinggi",
            source="auto_suggestion",
        ))
    if records:
        suggestions.append(make_memory_item(
            f"Pengguna sudah memiliki {len(records)} catatan performa; setiap insight berikutnya perlu membaca tren data recording sebelum memberi keputusan.",
            category="Manajemen Data",
            priority="Sedang",
            source="auto_suggestion",
        ))
    if decision_log:
        last = decision_log[-1]
        decision = str(last.get("main_decision") or "").strip()
        if decision:
            suggestions.append(make_memory_item(
                f"Keputusan AI terakhir yang perlu ditindaklanjuti: {decision}",
                category="Catatan Lapangan",
                priority=str(last.get("priority") or "Sedang"),
                source="auto_suggestion",
            ))
    return normalise_memory_items(suggestions)
