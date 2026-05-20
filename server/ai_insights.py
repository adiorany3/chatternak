from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Tuple

from farm_profile import normalise_profile, profile_completeness, summarize_profile
from farm_records import performance_flags, records_context, summarize_records
from farm_calendar import calendar_context


PRIORITY_ORDER = {"KRITIS": 0, "TINGGI": 1, "SEDANG": 2, "RENDAH": 3}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except Exception:
        return None


def build_scorecard(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Ringkasan numerik untuk membaca kondisi farm secara cepat."""
    p = normalise_profile(profile)
    summary = summarize_records(records)
    completeness = profile_completeness(p)
    latest = summary.get("latest") or {}

    risk_points = 0
    if completeness < 60:
        risk_points += 1
    if summary["count"] == 0:
        risk_points += 2
    if summary.get("mortality_total", 0) > 0:
        risk_points += 3
    if summary.get("adg") is not None and summary["adg"] <= 0:
        risk_points += 2
    if summary.get("fcr") is not None and summary["fcr"] > 8:
        risk_points += 2
    if latest and _safe_float(latest.get("feed_kg"), 0) <= 0:
        risk_points += 1
    if health_case and str(health_case.get("symptoms", "")).strip():
        risk_points += 2
    if not calendar_events:
        risk_points += 1

    if risk_points >= 6:
        risk_level = "TINGGI"
    elif risk_points >= 3:
        risk_level = "SEDANG"
    else:
        risk_level = "RENDAH"

    today = date.today()
    upcoming = []
    overdue = []
    for event in calendar_events:
        event_date = _parse_date(event.get("date") or event.get("tanggal"))
        if not event_date:
            continue
        item = {**event, "_date": event_date}
        if event_date < today:
            overdue.append(item)
        elif 0 <= (event_date - today).days <= 14:
            upcoming.append(item)

    return {
        "profile_completeness": completeness,
        "risk_level": risk_level,
        "risk_points": risk_points,
        "records_count": summary["count"],
        "population": p["population"],
        "animal_type": p["animal_type"],
        "phase": p["phase"],
        "adg": summary.get("adg"),
        "fcr": summary.get("fcr"),
        "mortality_total": summary.get("mortality_total", 0),
        "feed_total": summary.get("feed_total", 0.0),
        "cost_total": summary.get("cost_total", 0.0),
        "egg_total": summary.get("egg_total", 0),
        "milk_total": summary.get("milk_total", 0.0),
        "calendar_count": len(calendar_events),
        "calendar_upcoming_14d": len(upcoming),
        "calendar_overdue": len(overdue),
        "has_health_case": bool(health_case and str(health_case.get("symptoms", "")).strip()),
    }


def local_operational_insights(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any] | None = None) -> List[Dict[str, str]]:
    """Membuat insight lokal deterministik sebelum AI memberi analisis lebih kaya."""
    p = normalise_profile(profile)
    summary = summarize_records(records)
    completeness = profile_completeness(p)
    insights: List[Dict[str, str]] = []

    if completeness < 60:
        insights.append({
            "priority": "TINGGI",
            "area": "Profil farm",
            "title": "Profil belum cukup lengkap untuk rekomendasi presisi",
            "evidence": f"Kelengkapan profil baru {completeness}%.",
            "action": "Lengkapi populasi, fase ternak, bobot rata-rata, lokasi, sistem kandang, bahan pakan, target pasar, dan masalah utama.",
        })

    if summary["count"] == 0:
        insights.append({
            "priority": "TINGGI",
            "area": "Recording",
            "title": "Belum ada catatan performa sebagai dasar insight",
            "evidence": "ADG, FCR, biaya, mortalitas, dan produksi belum dapat dihitung.",
            "action": "Mulai input catatan harian/mingguan: populasi, bobot rata-rata, konsumsi pakan, biaya, mortalitas, telur/susu, dan catatan lapangan.",
        })
    else:
        if summary.get("adg") is None:
            insights.append({
                "priority": "SEDANG",
                "area": "Pertumbuhan",
                "title": "ADG belum bisa dihitung",
                "evidence": "Minimal perlu dua catatan bobot pada tanggal berbeda.",
                "action": "Timbang sampel ternak secara rutin, gunakan tanggal konsisten, dan catat bobot rata-rata.",
            })
        elif summary["adg"] <= 0:
            insights.append({
                "priority": "TINGGI",
                "area": "Pertumbuhan",
                "title": "Pertumbuhan tidak naik",
                "evidence": f"ADG estimasi {summary['adg']:.3f} kg/hari.",
                "action": "Evaluasi kualitas pakan, kecukupan air, kepadatan kandang, parasit/penyakit, stres panas, dan kualitas bibit.",
            })
        elif summary["adg"] < 0.05 and p["animal_type"] in {"sapi", "kambing", "domba"}:
            insights.append({
                "priority": "SEDANG",
                "area": "Pertumbuhan",
                "title": "ADG terlihat rendah untuk penggemukan",
                "evidence": f"ADG estimasi {summary['adg']:.3f} kg/hari.",
                "action": "Cek ulang formula hijauan-konsentrat, mineral, kualitas bahan pakan, dan sanitasi kandang.",
            })

        if summary.get("fcr") is None:
            insights.append({
                "priority": "SEDANG",
                "area": "Efisiensi pakan",
                "title": "FCR belum bisa dihitung",
                "evidence": "Data kenaikan bobot dan konsumsi pakan belum cukup.",
                "action": "Catat pakan terpakai setiap hari dan bobot mingguan agar efisiensi pakan dapat dianalisis.",
            })
        elif summary["fcr"] > 8:
            insights.append({
                "priority": "TINGGI",
                "area": "Efisiensi pakan",
                "title": "FCR tinggi atau data pakan belum rapi",
                "evidence": f"FCR estimasi {summary['fcr']:.2f}.",
                "action": "Bandingkan jumlah pakan masuk dengan sisa pakan, evaluasi palatabilitas, pakan tercecer, penyakit subklinis, dan akurasi bobot.",
            })

        if summary.get("mortality_total", 0) > 0:
            insights.append({
                "priority": "KRITIS",
                "area": "Kesehatan",
                "title": "Ada mortalitas tercatat",
                "evidence": f"Total mortalitas {summary['mortality_total']} ekor.",
                "action": "Pisahkan ternak sakit, cek pola kematian, dokumentasikan gejala, periksa pakan-air, perkuat biosecurity, dan hubungi dokter hewan bila berulang/mendadak.",
            })

        if summary.get("feed_total", 0) <= 0:
            insights.append({
                "priority": "SEDANG",
                "area": "Pakan",
                "title": "Konsumsi pakan belum tercatat",
                "evidence": "Total pakan tercatat 0 kg.",
                "action": "Catat pakan harian per kelompok ternak agar kebutuhan stok, biaya, dan FCR dapat dihitung.",
            })

    if not calendar_events:
        insights.append({
            "priority": "SEDANG",
            "area": "Kalender",
            "title": "Kalender manajemen belum dibuat",
            "evidence": "Belum ada jadwal sanitasi, recording, evaluasi pakan, kontrol kesehatan, atau reproduksi.",
            "action": "Buka menu Kalender Manajemen dan buat jadwal otomatis minimal 60 hari.",
        })
    else:
        score = build_scorecard(profile, records, calendar_events, health_case)
        if score["calendar_overdue"] > 0:
            insights.append({
                "priority": "TINGGI",
                "area": "Kalender",
                "title": "Ada jadwal manajemen yang terlewat",
                "evidence": f"{score['calendar_overdue']} jadwal sudah melewati tanggal hari ini.",
                "action": "Prioritaskan sanitasi, recording, dan kontrol kesehatan yang terlewat sebelum menambah jadwal baru.",
            })
        if score["calendar_upcoming_14d"] > 0:
            insights.append({
                "priority": "RENDAH",
                "area": "Kalender",
                "title": "Ada kegiatan penting 14 hari ke depan",
                "evidence": f"{score['calendar_upcoming_14d']} kegiatan masuk periode dekat.",
                "action": "Siapkan tenaga, bahan pakan, vitamin/mineral, alat recording, dan kebutuhan sanitasi sebelum tanggal kegiatan.",
            })

    if health_case and str(health_case.get("symptoms", "")).strip():
        affected = _safe_int(health_case.get("affected"), 0)
        population = max(_safe_int(health_case.get("population"), p.get("population", 0)), 1)
        affected_pct = (affected / population) * 100
        priority = "KRITIS" if affected_pct >= 10 or "mati" in str(health_case.get("mortality", "")).lower() else "TINGGI"
        insights.append({
            "priority": priority,
            "area": "Kesehatan",
            "title": "Kasus kesehatan terakhir perlu ditindaklanjuti",
            "evidence": f"Terdampak {affected} dari {population} ekor ({affected_pct:.1f}%). Gejala: {health_case.get('symptoms', '-')}",
            "action": "Lakukan isolasi, pantau suhu/nafsu makan/feses/napas, cek pakan-air, bersihkan kandang, dan konsultasikan bila memburuk.",
        })

    insights.extend({
        "priority": "SEDANG",
        "area": "Performa",
        "title": flag.split(";", 1)[0],
        "evidence": flag,
        "action": "Gunakan data ini sebagai prioritas evaluasi minggu ini dan minta AI membuat rencana perbaikan 7 hari.",
    } for flag in performance_flags(records))

    unique: List[Dict[str, str]] = []
    seen = set()
    for item in insights:
        key = (item["area"], item["title"])
        if key not in seen:
            unique.append(item)
            seen.add(key)
    unique.sort(key=lambda item: PRIORITY_ORDER.get(item["priority"], 99))
    return unique


def format_insights_markdown(insights: List[Dict[str, str]], limit: int | None = None) -> str:
    if not insights:
        return "✅ Belum ada sinyal risiko besar. Tetap lanjutkan recording rutin agar insight makin akurat."
    selected = insights[:limit] if limit else insights
    lines = []
    for i, item in enumerate(selected, start=1):
        lines.append(
            f"**{i}. [{item['priority']}] {item['area']} — {item['title']}**\n"
            f"- Bukti: {item['evidence']}\n"
            f"- Aksi: {item['action']}"
        )
    return "\n\n".join(lines)


def build_ai_insight_context(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], health_case: Dict[str, Any] | None = None) -> str:
    score = build_scorecard(profile, records, calendar_events, health_case)
    insights = local_operational_insights(profile, records, calendar_events, health_case)
    health_text = "Tidak ada kasus kesehatan terakhir yang tercatat."
    if health_case:
        health_text = "Kasus kesehatan terakhir: " + "; ".join(f"{k}={v}" for k, v in health_case.items() if v)
    return "\n\n".join([
        "KONTEKS AI INSIGHT ENGINE",
        "Profil farm:\n" + summarize_profile(profile),
        "Scorecard:\n" + "\n".join(f"- {k}: {v}" for k, v in score.items()),
        "Catatan performa:\n" + records_context(records),
        "Kalender manajemen:\n" + calendar_context(calendar_events),
        health_text,
        "Insight lokal awal:\n" + format_insights_markdown(insights),
        "Instruksi output: buat insight manajemen peternakan berbasis data yang tersedia. Jangan mengarang data. Pisahkan antara fakta, asumsi, risiko, dan rekomendasi. Beri prioritas tindakan 24 jam, 7 hari, dan 30 hari. Sertakan indikator yang perlu dipantau.",
    ])


def insight_prompt() -> str:
    return (
        "Buatkan insight manajemen farm dari data aplikasi. Fokus pada keputusan praktis: risiko utama, anomali performa, pakan, kesehatan, kalender, biaya, dan tindakan prioritas. "
        "Gunakan format: 1) Kesimpulan eksekutif, 2) Temuan data, 3) Risiko prioritas, 4) Rekomendasi 24 jam, 5) Rekomendasi 7 hari, 6) Rekomendasi 30 hari, 7) Data yang masih perlu dicatat."
    )
