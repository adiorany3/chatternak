from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import re

import numpy as np

from domain_data import DEFAULT_WEIGHTS, FEED_RATES


def parse_number(value: str | int | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).strip().lower().replace("rp", "").replace(" ", "")
    cleaned = cleaned.replace(".", "").replace(",", ".")
    return float(cleaned)


def rupiah(value: float) -> str:
    return f"Rp {value:,.0f}".replace(",", ".")


def analyze_data(data_type: str, values: List[float]) -> str:
    values_array = np.array(values, dtype=float)
    if values_array.size == 0:
        return "Data kosong. Masukkan minimal satu nilai."
    return (
        f"Analisis data {data_type}:\n"
        f"- Rata-rata: {np.mean(values_array):.2f}\n"
        f"- Median: {np.median(values_array):.2f}\n"
        f"- Standar deviasi: {np.std(values_array):.2f}\n"
        f"- Minimum: {np.min(values_array):.2f}\n"
        f"- Maksimum: {np.max(values_array):.2f}"
    )


def predict_growth(initial_weight: float, daily_gain: float, days: int) -> Dict[str, float | int | List[float]]:
    initial_weight = float(initial_weight)
    daily_gain = float(daily_gain)
    days = int(days)
    if initial_weight <= 0:
        raise ValueError("Berat awal harus lebih dari 0 kg.")
    if daily_gain < 0:
        raise ValueError("Pertambahan berat harian tidak boleh negatif.")
    if days <= 0:
        raise ValueError("Periode harus lebih dari 0 hari.")
    weights = [initial_weight + daily_gain * day for day in range(days + 1)]
    final_weight = weights[-1]
    return {
        "initial_weight": initial_weight,
        "daily_gain": daily_gain,
        "final_weight": final_weight,
        "weight_gain": final_weight - initial_weight,
        "days": days,
        "weights": weights,
    }


def calculate_feed_needs(animal_type: str, count: int, avg_weight: float | None = None) -> str:
    animal_type = animal_type.lower().strip()
    count = int(count)
    if count <= 0:
        return "Jumlah ternak harus lebih dari 0 ekor."
    if animal_type not in FEED_RATES:
        return f"Jenis ternak '{animal_type}' belum tersedia di kalkulator. Pilihan: {', '.join(FEED_RATES)}."
    avg_weight = DEFAULT_WEIGHTS.get(animal_type, 1.0) if avg_weight is None else float(avg_weight)
    if avg_weight <= 0:
        return "Berat rata-rata harus lebih dari 0 kg."

    daily_feed_per_animal = avg_weight * FEED_RATES[animal_type]
    total_daily_feed = daily_feed_per_animal * count
    weekly_feed = total_daily_feed * 7
    monthly_feed = total_daily_feed * 30
    return (
        f"Estimasi kebutuhan pakan untuk {count} ekor {animal_type} dengan bobot rata-rata {avg_weight:.2f} kg:\n"
        f"- Per ekor per hari: {daily_feed_per_animal:.2f} kg\n"
        f"- Total harian: {total_daily_feed:.2f} kg\n"
        f"- Total mingguan: {weekly_feed:.2f} kg\n"
        f"- Total bulanan: {monthly_feed:.2f} kg\n\n"
        "Catatan: angka ini estimasi awal. Sesuaikan lagi dengan umur, fase produksi, kualitas pakan, dan performa aktual."
    )


def calculate_bep(fixed_cost: float, price_per_unit: float, variable_cost_per_unit: float) -> str:
    fixed_cost = float(fixed_cost)
    price_per_unit = float(price_per_unit)
    variable_cost_per_unit = float(variable_cost_per_unit)
    if fixed_cost < 0 or price_per_unit < 0 or variable_cost_per_unit < 0:
        return "Biaya dan harga tidak boleh bernilai negatif."
    margin = price_per_unit - variable_cost_per_unit
    if margin <= 0:
        return "BEP tidak layak dihitung karena harga jual harus lebih besar dari biaya variabel per unit."
    bep_units = fixed_cost / margin
    bep_revenue = bep_units * price_per_unit
    return (
        "Analisis BEP (Break Even Point):\n"
        f"- Titik impas: {bep_units:.2f} unit\n"
        f"- Omzet pada titik impas: {rupiah(bep_revenue)}\n"
        f"- Margin kontribusi per unit: {rupiah(margin)}\n"
        f"- Artinya minimal perlu menjual {bep_units:.2f} unit agar tidak rugi."
    )


def detect_tool_response(message: str) -> str | None:
    """Menjawab pola hitung eksplisit tanpa biaya API."""
    text = message.lower().strip()

    feed_match = re.search(
        r"(?:hitung|berapa)\s+(?:kebutuhan|jumlah)?\s*pakan\s+(?:untuk|bagi)?\s*(\d+)\s+(?:ekor|benih|bibit)?\s*(sapi|kambing|ayam|bebek|ikan|kelinci)(?:\s+dengan\s+berat\s+(\d+(?:[\.,]\d+)?)\s*(?:kg|kilogram)?)?",
        text,
    )
    if feed_match:
        count, animal_type, weight = feed_match.groups()
        parsed_weight = float(weight.replace(",", ".")) if weight else None
        return calculate_feed_needs(animal_type, int(count), parsed_weight)

    growth_match = re.search(
        r"prediksi\s+(?:pertumbuhan|berat)\s+(?:\w+\s+)?(?:dari|berat)?\s*(\d+(?:[\.,]\d+)?)\s*(?:kg|kilogram)?\s+(?:dengan|dan)\s+(?:pertambahan|kenaikan)\s+(\d+(?:[\.,]\d+)?)\s*(?:kg|kilogram)?\s*(?:per|setiap|tiap)\s*hari\s+(?:selama|untuk)\s+(\d+)\s*hari",
        text,
    )
    if growth_match:
        init_weight, daily_gain, days = growth_match.groups()
        result = predict_growth(float(init_weight.replace(",", ".")), float(daily_gain.replace(",", ".")), int(days))
        return (
            "Prediksi pertumbuhan ternak:\n"
            f"- Berat awal: {result['initial_weight']:.2f} kg\n"
            f"- Pertambahan harian: {result['daily_gain']:.3f} kg/hari\n"
            f"- Berat akhir setelah {result['days']} hari: {result['final_weight']:.2f} kg\n"
            f"- Total pertambahan bobot: {result['weight_gain']:.2f} kg"
        )

    bep_match = re.search(
        r"(?:hitung|berapa)\s+(?:bep|break\s+even\s+point|titik\s+impas).*?(?:biaya\s+tetap|modal\s+tetap)\s+(\d+(?:[\.,]\d+)?)(?:\s*(juta|ribu))?.*?(?:harga\s+jual|harga)\s+(\d+(?:[\.,]\d+)?)(?:\s*(juta|ribu))?.*?(?:biaya\s+variabel|biaya\s+per\s+unit)\s+(\d+(?:[\.,]\d+)?)(?:\s*(juta|ribu))?",
        text,
    )
    if bep_match:
        fixed, fixed_unit, price, price_unit, variable, variable_unit = bep_match.groups()
        def convert(number: str, unit: str | None) -> float:
            value = float(number.replace(",", "."))
            if unit == "juta":
                return value * 1_000_000
            if unit == "ribu":
                return value * 1_000
            return value
        return calculate_bep(convert(fixed, fixed_unit), convert(price, price_unit), convert(variable, variable_unit))

    return None
