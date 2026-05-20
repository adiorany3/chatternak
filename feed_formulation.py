from __future__ import annotations

from typing import Dict, List, Tuple

LOCAL_FEED_INGREDIENTS: Dict[str, Dict[str, float | str]] = {
    "rumput odot": {"protein": 10.0, "energy": 55.0, "type": "hijauan"},
    "rumput gajah": {"protein": 8.0, "energy": 52.0, "type": "hijauan"},
    "kaliandra": {"protein": 20.0, "energy": 55.0, "type": "leguminosa"},
    "indigofera": {"protein": 24.0, "energy": 58.0, "type": "leguminosa"},
    "dedak": {"protein": 12.0, "energy": 68.0, "type": "energi"},
    "bekatul": {"protein": 11.0, "energy": 66.0, "type": "energi"},
    "jagung giling": {"protein": 8.5, "energy": 85.0, "type": "energi"},
    "ampas tahu": {"protein": 18.0, "energy": 62.0, "type": "protein"},
    "bungkil kelapa": {"protein": 20.0, "energy": 65.0, "type": "protein"},
    "onggok": {"protein": 3.0, "energy": 72.0, "type": "energi"},
    "maggot bsf": {"protein": 35.0, "energy": 70.0, "type": "protein"},
    "mineral mix": {"protein": 0.0, "energy": 0.0, "type": "mineral"},
}

TARGET_PROTEIN: Dict[Tuple[str, str], float] = {
    ("sapi", "penggemukan"): 12.0,
    ("sapi", "laktasi"): 14.0,
    ("kerbau", "penggemukan"): 11.0,
    ("kerbau", "laktasi"): 13.0,
    ("kambing", "penggemukan"): 13.0,
    ("kambing", "bunting tua"): 14.0,
    ("kambing", "laktasi"): 15.0,
    ("domba", "penggemukan"): 13.0,
    ("domba", "bunting tua"): 14.0,
    ("ayam", "starter"): 20.0,
    ("ayam", "grower"): 17.0,
    ("ayam", "finisher"): 18.0,
    ("ayam", "layer awal produksi"): 17.0,
    ("bebek", "petelur"): 17.0,
    ("puyuh", "petelur"): 20.0,
    ("babi", "starter"): 20.0,
    ("babi", "grower"): 17.0,
    ("babi", "finisher"): 15.0,
    ("ikan lele", "pembesaran"): 30.0,
    ("ikan nila", "pembesaran"): 28.0,
    ("ikan gurame", "pembesaran"): 26.0,
    ("ikan patin", "pembesaran"): 28.0,
    ("ikan mas", "pembesaran"): 28.0,
    ("kelinci", "penggemukan"): 16.0,
}


def target_protein(animal_type: str, phase: str) -> float:
    animal = (animal_type or "").lower()
    ph = (phase or "").lower()
    for (a, p), target in TARGET_PROTEIN.items():
        if a == animal and p in ph:
            return target
    defaults = {"sapi": 12.0, "kerbau": 11.0, "kambing": 13.0, "domba": 13.0, "ayam": 18.0, "bebek": 17.0, "puyuh": 20.0, "kelinci": 16.0, "babi": 17.0, "ikan lele": 30.0, "ikan nila": 28.0, "ikan gurame": 26.0, "ikan patin": 28.0, "ikan mas": 28.0}
    return defaults.get(animal, 14.0)


def calculate_formula(ingredients: List[Dict[str, float | str]]) -> Dict[str, float]:
    total_pct = sum(float(item.get("percent", 0) or 0) for item in ingredients)
    if total_pct <= 0:
        return {"total_percent": 0.0, "protein": 0.0, "energy_index": 0.0}
    protein = 0.0
    energy = 0.0
    for item in ingredients:
        pct = float(item.get("percent", 0) or 0)
        protein += pct * float(item.get("protein", 0) or 0)
        energy += pct * float(item.get("energy", 0) or 0)
    return {
        "total_percent": total_pct,
        "protein": protein / total_pct,
        "energy_index": energy / total_pct,
    }


def estimate_formula_cost(ingredients: List[Dict[str, float | str]]) -> float:
    total_pct = sum(float(item.get("percent", 0) or 0) for item in ingredients)
    if total_pct <= 0:
        return 0.0
    cost = 0.0
    for item in ingredients:
        cost += float(item.get("percent", 0) or 0) * float(item.get("price_per_kg", 0) or 0)
    return cost / total_pct


def formula_feedback(animal_type: str, phase: str, ingredients: List[Dict[str, float | str]]) -> str:
    result = calculate_formula(ingredients)
    cost = estimate_formula_cost(ingredients)
    target = target_protein(animal_type, phase)
    diff = result["protein"] - target
    if result["total_percent"] <= 0:
        return "Formula belum berisi bahan. Tambahkan bahan pakan dan persentasenya."
    total_note = "tepat 100%" if abs(result["total_percent"] - 100) < 0.01 else f"belum 100% ({result['total_percent']:.1f}%)"
    if diff >= 1.5:
        protein_note = "protein cenderung tinggi; cek biaya dan risiko pemborosan."
    elif diff <= -1.5:
        protein_note = "protein cenderung rendah; pertimbangkan sumber protein seperti ampas tahu, bungkil, indigofera, atau maggot sesuai komoditas."
    else:
        protein_note = "protein mendekati target awal."
    return (
        "Evaluasi formula pakan:\n"
        f"- Total komposisi: {total_note}\n"
        f"- Protein kasar estimasi: {result['protein']:.2f}% | target fase: ±{target:.1f}%\n"
        f"- Indeks energi relatif: {result['energy_index']:.1f}/100\n"
        f"- Estimasi biaya campuran: Rp {cost:,.0f}/kg\n".replace(",", ".")
        + f"- Catatan: {protein_note}\n\n"
        "Catatan lapangan: nilai ini estimasi edukatif. Untuk formula komersial, idealnya uji bahan, cek bahan kering, serat, mineral, dan performa aktual."
    )


def simple_ruminant_ration(animal_type: str, body_weight: float, population: int, forage_ratio: float = 70.0) -> str:
    bw = float(body_weight)
    pop = int(population)
    rates = {"sapi": 0.03, "kerbau": 0.025, "kambing": 0.04, "domba": 0.04}
    total_feed = bw * rates.get(animal_type, 0.035) * pop
    forage = total_feed * forage_ratio / 100
    concentrate = total_feed - forage
    return (
        f"Ransum awal {animal_type} {pop} ekor bobot rata-rata {bw:.1f} kg:\n"
        f"- Total pakan segar estimasi: {total_feed:.2f} kg/hari\n"
        f"- Hijauan ±{forage_ratio:.0f}%: {forage:.2f} kg/hari\n"
        f"- Konsentrat ±{100-forage_ratio:.0f}%: {concentrate:.2f} kg/hari\n"
        "- Adaptasikan bertahap 7-10 hari, jangan ganti pakan mendadak."
    )
