from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from commodity_breeds import AQUACULTURE, POULTRY, RUMINANTS


def generate_management_events(animal_type: str, start: date, days: int = 60, phase: str = "") -> List[Dict[str, Any]]:
    animal = animal_type.lower()
    events: List[Dict[str, Any]] = []
    end = start + timedelta(days=days)

    def add_every(title: str, every_days: int, description: str) -> None:
        current = start
        while current <= end:
            events.append({"date": str(current), "title": title, "description": description})
            current += timedelta(days=every_days)

    add_every("Sanitasi kandang/kolam", 7, "Bersihkan area basah, sisa pakan, feses/lumpur, dan cek drainase.")
    add_every("Evaluasi pakan dan air", 3, "Cek stok pakan, kualitas bahan, air minum, dan konsumsi aktual.")
    add_every("Recording performa", 7, "Catat bobot sampling, mortalitas, produksi, pakan, dan biaya.")

    if animal in RUMINANTS or animal in {"kelinci", "babi"}:
        add_every("Kontrol kesehatan ternak", 14, "Cek BCS/bobot, kulit, feses, nafsu makan, tanda parasit/penyakit, dan kondisi kandang.")
        add_every("Evaluasi reproduksi", 30, "Cek birahi, kebuntingan, induk laktasi, dan catatan kawin/IB.")
    elif animal in POULTRY:
        add_every("Cek biosecurity unggas", 7, "Cek footbath, litter, ventilasi, kepadatan, dan gejala pernapasan.")
        add_every("Evaluasi produksi telur/bobot", 7, "Catat produksi telur, berat badan sampling, FCR, dan mortalitas.")
    elif animal in AQUACULTURE:
        add_every("Cek kualitas air", 2, "Amati warna/bau air, ikan megap-megap, sisa pakan, dan aerasi.")
        add_every("Sampling bobot ikan", 10, "Sampling bobot untuk evaluasi pakan, FCR, dan waktu panen.")

    if "bunting" in phase.lower():
        events.append({"date": str(start + timedelta(days=14)), "title": "Persiapan kelahiran", "description": "Siapkan kandang bersih, alas kering, observasi induk, dan rencana bantuan bila terjadi distokia."})
    return sorted(events, key=lambda item: item["date"])


def calendar_context(events: List[Dict[str, Any]]) -> str:
    if not events:
        return "Belum ada kalender manajemen."
    upcoming = events[:8]
    return "Kalender manajemen terdekat:\n" + "\n".join(
        f"- {item.get('date')}: {item.get('title')} — {item.get('description', '')}" for item in upcoming
    )
