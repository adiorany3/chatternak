from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Tuple
import math

ROLE_OPTIONS = [
    "Owner / Direktur Utama",
    "Direktur Operasional",
    "Manager Farm",
    "Dokter Hewan / Konsultan",
    "Admin Data",
    "Petugas Kandang",
    "Peternak Rakyat",
]

ROLE_DESCRIPTIONS = {
    "Owner / Direktur Utama": "Fokus pada KPI lintas farm, risiko strategis, margin, cashflow, dan keputusan investasi.",
    "Direktur Operasional": "Fokus pada SOP, target produksi, efisiensi pakan, biosecurity, dan corrective action.",
    "Manager Farm": "Fokus pada eksekusi harian, recording, tenaga kerja, stok pakan, dan performa batch.",
    "Dokter Hewan / Konsultan": "Fokus pada kesehatan populasi, biosecurity, triase, pencegahan penyakit, dan batasan terapi aman.",
    "Admin Data": "Fokus pada kelengkapan data, audit trail, backup, dan validasi input.",
    "Petugas Kandang": "Fokus pada instruksi lapangan yang singkat, aman, dan mudah dilakukan.",
    "Peternak Rakyat": "Fokus pada bahasa sederhana, bahan lokal, langkah praktis, dan risiko biaya.",
}

DEFAULT_ENTERPRISE_STATE: Dict[str, Any] = {
    "current_role": "Owner / Direktur Utama",
    "company_name": "",
    "farms": [],
    "active_farm_id": "",
    "batches": [],
    "active_batch_id": "",
    "quick_inputs": [],
    "audit_trail": [],
    "knowledge_docs": [],
    "finance_transactions": [],
    "feed_stock_kg": 0.0,
    "notification_contacts": [],
    "last_sync_status": {},
    "target_kpi_override": {},
}

KPI_STANDARDS: Dict[str, Dict[str, Any]] = {
    "ayam": {
        "pedaging": {"fcr_max": 1.8, "mortality_max_pct": 5.0, "adg_min": 0.045, "panen_hari": 35},
        "petelur": {"mortality_max_pct": 8.0, "hen_day_min_pct": 80.0, "fcr_egg_max": 2.4},
        "dwiguna": {"fcr_max": 2.8, "mortality_max_pct": 7.0, "adg_min": 0.018},
    },
    "bebek": {
        "pedaging": {"fcr_max": 2.8, "mortality_max_pct": 6.0, "panen_hari": 60},
        "petelur": {"mortality_max_pct": 8.0, "hen_day_min_pct": 65.0},
        "dwiguna": {"fcr_max": 3.2, "mortality_max_pct": 8.0},
    },
    "puyuh": {"petelur": {"mortality_max_pct": 8.0, "hen_day_min_pct": 75.0, "fcr_egg_max": 2.7}},
    "sapi": {
        "pedaging": {"adg_min": 0.7, "mortality_max_pct": 2.0, "feed_cost_share_max_pct": 75.0},
        "perah": {"milk_liter_min": 8.0, "mastitis_alert": True, "calving_interval_max_day": 420},
        "dwiguna": {"adg_min": 0.45, "milk_liter_min": 4.0},
    },
    "kerbau": {"pedaging": {"adg_min": 0.35, "mortality_max_pct": 2.5}, "perah": {"milk_liter_min": 2.5}},
    "kambing": {
        "pedaging": {"adg_min": 0.08, "mortality_max_pct": 4.0, "feed_cost_share_max_pct": 75.0},
        "perah": {"milk_liter_min": 1.0, "mortality_max_pct": 4.0},
        "dwiguna": {"adg_min": 0.06, "milk_liter_min": 0.7},
    },
    "domba": {"pedaging": {"adg_min": 0.09, "mortality_max_pct": 4.0}},
    "kelinci": {"pedaging": {"adg_min": 0.025, "mortality_max_pct": 10.0}},
    "babi": {"pedaging": {"fcr_max": 3.2, "mortality_max_pct": 4.0, "adg_min": 0.55}},
    "ikan": {"pedaging": {"fcr_max": 1.5, "survival_min_pct": 85.0, "mortality_max_pct": 15.0}},
    "lele": {"pedaging": {"fcr_max": 1.3, "survival_min_pct": 85.0, "panen_hari": 75}},
    "nila": {"pedaging": {"fcr_max": 1.5, "survival_min_pct": 85.0, "panen_hari": 120}},
    "gurame": {"pedaging": {"fcr_max": 1.8, "survival_min_pct": 80.0, "panen_hari": 240}},
    "patin": {"pedaging": {"fcr_max": 1.6, "survival_min_pct": 85.0, "panen_hari": 180}},
    "mas": {"pedaging": {"fcr_max": 1.6, "survival_min_pct": 85.0, "panen_hari": 120}},
}

DOWNSTREAM_CHECKLIST = {
    "daging": [
        "puasakan ternak sesuai SOP sebelum potong bila relevan",
        "jaga kebersihan alat, meja, dan air",
        "hindari kontaminasi silang karkas dengan isi saluran pencernaan",
        "catat bobot hidup, bobot karkas, dan susut",
        "jaga rantai dingin bila produk disimpan/diangkut",
    ],
    "susu": [
        "cuci ambing dan alat perah",
        "saring susu segera setelah pemerahan",
        "dinginkan susu secepat mungkin",
        "pisahkan susu dari induk sakit/mastitis",
        "catat liter susu dan penolakan mutu harian",
    ],
    "telur": [
        "ambil telur beberapa kali sehari bila memungkinkan",
        "pisahkan telur retak/kotor",
        "simpan di tempat sejuk dan kering",
        "catat jumlah, grade, dan kerusakan telur",
        "jaga kebersihan nest box/litter",
    ],
    "ikan": [
        "puasakan ikan sebelum panen sesuai kebutuhan pasar",
        "gunakan air bersih saat sortasi",
        "hindari kepadatan tinggi saat transportasi",
        "catat bobot panen, survival rate, dan susut",
        "pakai es/rantai dingin bila ikan dijual segar jarak jauh",
    ],
}


def normalise_enterprise_state(value: Dict[str, Any] | None) -> Dict[str, Any]:
    state = dict(DEFAULT_ENTERPRISE_STATE)
    if isinstance(value, dict):
        for key, default in DEFAULT_ENTERPRISE_STATE.items():
            incoming = value.get(key, default)
            if isinstance(default, list):
                state[key] = list(incoming or []) if isinstance(incoming, list) else []
            elif isinstance(default, dict):
                state[key] = dict(incoming or {}) if isinstance(incoming, dict) else {}
            elif isinstance(default, float):
                try:
                    state[key] = float(incoming or 0)
                except Exception:
                    state[key] = default
            else:
                state[key] = str(incoming or default)
    if state["current_role"] not in ROLE_OPTIONS:
        state["current_role"] = DEFAULT_ENTERPRISE_STATE["current_role"]
    return state


def today_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def make_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def make_audit_event(action: str, actor_role: str, detail: str, source: str = "app") -> Dict[str, Any]:
    return {
        "created_at": today_text(),
        "actor_role": actor_role,
        "action": action,
        "detail": detail,
        "source": source,
    }


def kpi_standard_for(animal_type: str, production_goal: str) -> Dict[str, Any]:
    animal = (animal_type or "").lower()
    goal = (production_goal or "pedaging").lower()
    candidates = [animal]
    if animal.startswith("ikan_"):
        candidates.append(animal.replace("ikan_", ""))
        candidates.append("ikan")
    if animal in {"lele", "nila", "gurame", "patin", "mas"}:
        candidates.append("ikan")
    for key in candidates:
        if key in KPI_STANDARDS:
            by_goal = KPI_STANDARDS[key]
            return dict(by_goal.get(goal) or by_goal.get("pedaging") or next(iter(by_goal.values())))
    return {"mortality_max_pct": 5.0, "fcr_max": 2.5, "adg_min": 0.05}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _latest_records(records: List[Dict[str, Any]], limit: int = 2) -> List[Dict[str, Any]]:
    return sorted(records or [], key=lambda r: str(r.get("date", "")))[-limit:]


def compute_record_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    recs = sorted(records or [], key=lambda r: str(r.get("date", "")))
    if not recs:
        return {"record_count": 0}
    latest = recs[-1]
    first = recs[0]
    pop = max(_num(latest.get("population"), _num(first.get("population"), 0)), 0)
    total_feed = sum(_num(r.get("feed_kg")) for r in recs)
    total_cost = sum(_num(r.get("cost_rp")) for r in recs)
    total_mortality = sum(_num(r.get("mortality")) for r in recs)
    mortality_pct = (total_mortality / max(pop + total_mortality, 1)) * 100 if pop or total_mortality else 0
    adg = None
    fcr = None
    try:
        if len(recs) >= 2:
            d0 = datetime.fromisoformat(str(first.get("date"))).date()
            d1 = datetime.fromisoformat(str(latest.get("date"))).date()
            days = max((d1 - d0).days, 1)
            gain = _num(latest.get("avg_weight_kg")) - _num(first.get("avg_weight_kg"))
            adg = gain / days
            total_gain = gain * max(pop, 1)
            if total_gain > 0:
                fcr = total_feed / total_gain
    except Exception:
        pass
    eggs = sum(_num(r.get("eggs")) for r in recs)
    milk = sum(_num(r.get("milk_liter")) for r in recs)
    return {
        "record_count": len(recs),
        "latest": latest,
        "population": pop,
        "total_feed_kg": total_feed,
        "total_cost_rp": total_cost,
        "total_mortality": total_mortality,
        "mortality_pct": mortality_pct,
        "adg": adg,
        "fcr": fcr,
        "eggs_total": eggs,
        "milk_liter_total": milk,
    }


def validate_record_data(record: Dict[str, Any], profile: Dict[str, Any] | None = None) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    pop = _num(record.get("population"))
    weight = _num(record.get("avg_weight_kg"))
    feed = _num(record.get("feed_kg"))
    mortality = _num(record.get("mortality"))
    if pop < 0:
        issues.append({"level": "Merah", "field": "Populasi", "message": "Populasi tidak boleh negatif."})
    if mortality > pop and pop > 0:
        issues.append({"level": "Merah", "field": "Mortalitas", "message": "Mortalitas harian melebihi populasi aktif."})
    if weight < 0:
        issues.append({"level": "Merah", "field": "Bobot", "message": "Bobot tidak boleh negatif."})
    if feed < 0:
        issues.append({"level": "Merah", "field": "Pakan", "message": "Pakan terpakai tidak boleh negatif."})
    animal = (profile or {}).get("animal_type", "")
    if animal in {"kambing", "domba"} and weight > 150:
        issues.append({"level": "Kuning", "field": "Bobot", "message": "Bobot ruminansia kecil tampak terlalu tinggi; cek satuan kg/ekor."})
    if animal == "ayam" and weight > 10:
        issues.append({"level": "Kuning", "field": "Bobot", "message": "Bobot ayam rata-rata tampak terlalu tinggi; cek satuan gram vs kg."})
    if pop > 0 and feed / max(pop, 1) > 100:
        issues.append({"level": "Kuning", "field": "Pakan", "message": "Pakan per ekor sangat tinggi; cek apakah input total harian/mingguan."})
    return issues


def early_warnings(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any], biosecurity_checked: List[str], enterprise_state: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    state = normalise_enterprise_state(enterprise_state)
    metrics = compute_record_metrics(records)
    standard = kpi_standard_for(profile.get("animal_type", ""), profile.get("production_goal", ""))
    warnings: List[Dict[str, Any]] = []

    def add(level: str, area: str, finding: str, action: str) -> None:
        warnings.append({"level": level, "area": area, "finding": finding, "action": action})

    if metrics.get("record_count", 0) == 0:
        add("Kuning", "Recording", "Belum ada catatan performa.", "Mulai input data harian: populasi, bobot, pakan, biaya, mortalitas, produksi.")
    mort = metrics.get("mortality_pct")
    if mort is not None and mort > _num(standard.get("mortality_max_pct"), 5.0):
        add("Merah", "Kesehatan", f"Mortalitas kumulatif {mort:.1f}% melewati target {standard.get('mortality_max_pct')}%.", "Audit penyebab kematian, isolasi ternak sakit, cek pakan-air, dan hubungi dokter hewan bila pola berulang.")
    fcr = metrics.get("fcr")
    if fcr is not None and standard.get("fcr_max") and fcr > _num(standard.get("fcr_max")):
        add("Kuning", "Pakan", f"FCR estimasi {fcr:.2f} lebih buruk dari target {standard.get('fcr_max')}.", "Evaluasi kualitas pakan, jumlah terbuang, bobot mingguan, dan kepadatan kandang/kolam.")
    adg = metrics.get("adg")
    if adg is not None and standard.get("adg_min") and adg < _num(standard.get("adg_min")):
        add("Kuning", "Produksi", f"ADG estimasi {adg:.3f} kg/hari di bawah target {standard.get('adg_min')}.", "Cek fase, formulasi pakan, kesehatan subklinis, kualitas bibit, dan kenyamanan kandang.")

    if health_case:
        text = " ".join(str(v).lower() for v in health_case.values())
        red_terms = ["mati mendadak", "sesak", "darah", "kejang", "kembung", "tidak mau makan", "lumpuh"]
        if any(term in text for term in red_terms):
            add("Merah", "Triase", "Kasus kesehatan terakhir mengandung tanda bahaya.", "Pisahkan ternak sakit, catat gejala, dan hubungi dokter hewan/paramedik bila berat/menyebar.")

    checked = len(biosecurity_checked or [])
    if checked < 5:
        add("Kuning", "Biosecurity", "Checklist biosecurity masih rendah.", "Lengkapi minimal sanitasi alat, isolasi ternak sakit, kontrol tamu, kebersihan tempat pakan-minum, dan drainase/litter.")

    stock = _num(state.get("feed_stock_kg"))
    latest = metrics.get("latest") or {}
    daily_feed = _num(latest.get("feed_kg"))
    if stock > 0 and daily_feed > 0:
        days = stock / daily_feed
        if days < 7:
            add("Kuning", "Stok Pakan", f"Stok pakan diperkirakan hanya cukup {days:.1f} hari.", "Segera rencanakan pembelian/produksi pakan untuk minimal 14-30 hari ke depan.")
    return warnings[:20]


def executive_summary(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any], biosecurity_checked: List[str], enterprise_state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state = normalise_enterprise_state(enterprise_state)
    metrics = compute_record_metrics(records)
    warnings = early_warnings(profile, records, calendar_events, health_case, biosecurity_checked, state)
    red = sum(1 for w in warnings if w["level"] == "Merah")
    yellow = sum(1 for w in warnings if w["level"] == "Kuning")
    score = max(0, 100 - red * 22 - yellow * 8)
    if score >= 80:
        level = "Hijau"
    elif score >= 55:
        level = "Kuning"
    else:
        level = "Merah"
    priority = warnings[0]["action"] if warnings else "Pertahankan recording, kontrol pakan, biosecurity, dan evaluasi margin mingguan."
    return {
        "company_name": state.get("company_name", ""),
        "role": state.get("current_role", "Owner / Direktur Utama"),
        "score": score,
        "level": level,
        "red_warnings": red,
        "yellow_warnings": yellow,
        "metrics": metrics,
        "warnings": warnings,
        "priority": priority,
        "farms": len(state.get("farms", [])),
        "batches": len(state.get("batches", [])),
    }


def finance_snapshot(profile: Dict[str, Any], records: List[Dict[str, Any]], transactions: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    metrics = compute_record_metrics(records)
    transactions = transactions or []
    revenue = sum(_num(t.get("amount_rp")) for t in transactions if str(t.get("type", "")).lower() in {"pendapatan", "revenue", "income"})
    extra_cost = sum(_num(t.get("amount_rp")) for t in transactions if str(t.get("type", "")).lower() not in {"pendapatan", "revenue", "income"})
    recorded_cost = _num(metrics.get("total_cost_rp"))
    total_cost = recorded_cost + extra_cost
    margin = revenue - total_cost
    population = max(_num(profile.get("population")), _num(metrics.get("population")), 1)
    hpp_per_head = total_cost / population if population else 0
    total_gain = None
    recs = _latest_records(records, 2)
    if len(recs) >= 2:
        gain = _num(recs[-1].get("avg_weight_kg")) - _num(recs[0].get("avg_weight_kg"))
        if gain > 0:
            total_gain = gain * max(_num(recs[-1].get("population"), population), 1)
    hpp_per_kg_gain = total_cost / total_gain if total_gain else None
    roi = (margin / total_cost * 100) if total_cost > 0 else None
    return {
        "revenue_rp": revenue,
        "recorded_cost_rp": recorded_cost,
        "extra_cost_rp": extra_cost,
        "total_cost_rp": total_cost,
        "gross_margin_rp": margin,
        "hpp_per_head_rp": hpp_per_head,
        "hpp_per_kg_gain_rp": hpp_per_kg_gain,
        "roi_pct": roi,
    }


def knowledge_search(query: str, docs: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    terms = [t.lower() for t in str(query or "").replace("/", " ").split() if len(t) >= 3]
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for doc in docs or []:
        text = (str(doc.get("title", "")) + " " + str(doc.get("content", "")) + " " + str(doc.get("tags", ""))).lower()
        score = sum(text.count(term) for term in terms)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [dict(item) for _, item in scored[:limit]]


def downstream_guidance(profile: Dict[str, Any]) -> Dict[str, Any]:
    goal = (profile.get("production_goal") or "").lower()
    animal = (profile.get("animal_type") or "").lower()
    if goal == "perah":
        key = "susu"
    elif goal == "petelur":
        key = "telur"
    elif animal in {"lele", "nila", "gurame", "patin", "mas", "ikan"} or animal.startswith("ikan"):
        key = "ikan"
    else:
        key = "daging"
    return {"category": key, "checklist": DOWNSTREAM_CHECKLIST[key]}


def notification_messages(summary: Dict[str, Any]) -> List[str]:
    messages = []
    for warn in summary.get("warnings", [])[:5]:
        messages.append(f"[{warn['level']}] {warn['area']}: {warn['finding']} Tindakan: {warn['action']}")
    if not messages:
        messages.append("Status farm relatif aman. Tetap input data harian dan cek biosecurity.")
    return messages


def enterprise_context(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any], biosecurity_checked: List[str], enterprise_state: Dict[str, Any] | None = None) -> str:
    state = normalise_enterprise_state(enterprise_state)
    summary = executive_summary(profile, records, calendar_events, health_case, biosecurity_checked, state)
    finance = finance_snapshot(profile, records, state.get("finance_transactions", []))
    downstream = downstream_guidance(profile)
    warnings = summary.get("warnings", [])[:6]
    warning_text = "\n".join(f"- {w['level']} | {w['area']}: {w['finding']} -> {w['action']}" for w in warnings) or "- Belum ada peringatan utama."
    return f"""
KONTEKS ENTERPRISE AI PAKAR TERNAK:
- Peran pengguna aktif: {state.get('current_role')}
- Konteks perusahaan/farm: {state.get('company_name') or 'belum diisi'}
- Jumlah farm/unit: {len(state.get('farms', []))}; jumlah batch: {len(state.get('batches', []))}
- Skor eksekutif: {summary.get('score')}/100 ({summary.get('level')})
- Prioritas direksi/manager: {summary.get('priority')}
- Ringkasan keuangan: pendapatan Rp {finance.get('revenue_rp', 0):,.0f}; biaya Rp {finance.get('total_cost_rp', 0):,.0f}; margin Rp {finance.get('gross_margin_rp', 0):,.0f}
- Hilirisasi utama: {downstream.get('category')}; cek mutu: {', '.join(downstream.get('checklist', [])[:4])}
- Early warning aktif:
{warning_text}
ATURAN JAWABAN ENTERPRISE:
1. Beri ringkasan eksekutif dahulu untuk role direktur/owner.
2. Untuk manager/petugas, ubah menjadi instruksi operasional yang bisa dieksekusi.
3. Gunakan KPI, risiko, biaya, timeline 24 jam/7 hari/30 hari, dan dampak hulu-hilir.
4. Jangan memberi dosis obat keras/antibiotik sembarangan; arahkan ke dokter hewan untuk kasus merah.
""".strip()


def enterprise_report_markdown(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any], biosecurity_checked: List[str], enterprise_state: Dict[str, Any] | None = None) -> str:
    state = normalise_enterprise_state(enterprise_state)
    summary = executive_summary(profile, records, calendar_events, health_case, biosecurity_checked, state)
    finance = finance_snapshot(profile, records, state.get("finance_transactions", []))
    downstream = downstream_guidance(profile)
    lines = [
        "# Laporan Enterprise Decision Support System Ternak",
        f"Tanggal: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        f"Perusahaan/Farm: {state.get('company_name') or profile.get('farm_name') or '-'}",
        f"Role pembaca: {state.get('current_role')}",
        "",
        "## Ringkasan Eksekutif",
        f"- Skor farm/perusahaan: **{summary['score']}/100 ({summary['level']})**",
        f"- Peringatan merah: {summary['red_warnings']}; kuning: {summary['yellow_warnings']}",
        f"- Prioritas utama: {summary['priority']}",
        "",
        "## Keuangan",
        f"- Pendapatan: Rp {finance['revenue_rp']:,.0f}",
        f"- Total biaya: Rp {finance['total_cost_rp']:,.0f}",
        f"- Margin kasar: Rp {finance['gross_margin_rp']:,.0f}",
        f"- HPP/ekor atau unit: Rp {finance['hpp_per_head_rp']:,.0f}",
        "",
        "## Early Warning",
    ]
    for warn in summary.get("warnings", []) or [{"level": "Hijau", "area": "Operasional", "finding": "Tidak ada peringatan utama", "action": "Pertahankan recording dan evaluasi mingguan."}]:
        lines.append(f"- **{warn['level']} | {warn['area']}**: {warn['finding']} Tindakan: {warn['action']}")
    lines.extend([
        "",
        "## Hilirisasi / Teknologi Hasil",
        f"- Fokus produk: {downstream['category']}",
    ])
    for item in downstream.get("checklist", []):
        lines.append(f"- {item}")
    lines.append("\n## Audit Trail dan Database\n- Simpan laporan, XLSX, dan sinkronisasi database permanen bila Supabase dikonfigurasi.")
    return "\n".join(lines)
