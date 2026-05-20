from __future__ import annotations

from datetime import date
from typing import Any, Dict, List


def add_record(records: List[Dict[str, Any]], record: Dict[str, Any]) -> List[Dict[str, Any]]:
    cleaned = dict(record)
    cleaned["date"] = str(cleaned.get("date") or date.today())
    records.append(cleaned)
    return records


def summarize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {
            "count": 0,
            "latest": None,
            "adg": None,
            "fcr": None,
            "mortality_total": 0,
            "egg_total": 0,
            "milk_total": 0.0,
            "feed_total": 0.0,
            "cost_total": 0.0,
        }
    sorted_records = sorted(records, key=lambda r: str(r.get("date", "")))
    first = sorted_records[0]
    latest = sorted_records[-1]
    mortality_total = sum(int(r.get("mortality", 0) or 0) for r in records)
    egg_total = sum(int(r.get("eggs", 0) or 0) for r in records)
    milk_total = sum(float(r.get("milk_liter", 0) or 0) for r in records)
    feed_total = sum(float(r.get("feed_kg", 0) or 0) for r in records)
    cost_total = sum(float(r.get("cost_rp", 0) or 0) for r in records)
    adg = None
    try:
        from datetime import datetime
        d1 = datetime.fromisoformat(str(first.get("date"))).date()
        d2 = datetime.fromisoformat(str(latest.get("date"))).date()
        days = max((d2 - d1).days, 1)
        w1 = float(first.get("avg_weight_kg", 0) or 0)
        w2 = float(latest.get("avg_weight_kg", 0) or 0)
        if w1 > 0 and w2 > 0:
            adg = (w2 - w1) / days
    except Exception:
        adg = None
    fcr = None
    try:
        w1 = float(first.get("avg_weight_kg", 0) or 0)
        w2 = float(latest.get("avg_weight_kg", 0) or 0)
        pop = int(latest.get("population", first.get("population", 1)) or 1)
        gain = max((w2 - w1) * pop, 0)
        if gain > 0 and feed_total > 0:
            fcr = feed_total / gain
    except Exception:
        fcr = None
    return {
        "count": len(records),
        "latest": latest,
        "adg": adg,
        "fcr": fcr,
        "mortality_total": mortality_total,
        "egg_total": egg_total,
        "milk_total": milk_total,
        "feed_total": feed_total,
        "cost_total": cost_total,
    }


def records_context(records: List[Dict[str, Any]]) -> str:
    summary = summarize_records(records)
    if summary["count"] == 0:
        return "Belum ada catatan performa ternak. Sarankan user mulai mencatat bobot, pakan, mortalitas, produksi, dan biaya."
    latest = summary["latest"] or {}
    adg = summary["adg"]
    fcr = summary["fcr"]
    adg_text = f"ADG estimasi: {adg:.3f} kg/hari. " if adg is not None else "ADG belum bisa dihitung. "
    fcr_text = f"FCR estimasi: {fcr:.2f}. " if fcr is not None else "FCR belum bisa dihitung. "
    cost_text = f"Rp {summary['cost_total']:,.0f}".replace(",", ".")
    return (
        f"Ringkasan catatan performa: {summary['count']} catatan. "
        f"Catatan terbaru {latest.get('date')}: populasi {latest.get('population', '-')}, bobot rata-rata {latest.get('avg_weight_kg', '-')} kg. "
        f"{adg_text}{fcr_text}"
        f"Total mortalitas: {summary['mortality_total']}; total pakan tercatat: {summary['feed_total']:.2f} kg; total biaya tercatat: {cost_text}."
    )


def performance_flags(records: List[Dict[str, Any]]) -> List[str]:
    flags: List[str] = []
    summary = summarize_records(records)
    latest = summary.get("latest") or {}
    if summary["mortality_total"]:
        flags.append(f"Ada mortalitas tercatat {summary['mortality_total']} ekor; cek penyebab dan biosecurity.")
    if summary.get("adg") is not None and summary["adg"] <= 0:
        flags.append("ADG tidak naik; evaluasi pakan, penyakit, kepadatan, dan kualitas bibit.")
    if summary.get("fcr") is not None and summary["fcr"] > 8:
        flags.append("FCR tinggi; indikasi pakan boros, pertumbuhan lambat, atau data belum akurat.")
    if latest and float(latest.get("feed_kg", 0) or 0) <= 0:
        flags.append("Catatan terbaru belum memuat konsumsi pakan; FCR sulit dievaluasi.")
    return flags
