from __future__ import annotations

from typing import Dict, List, Tuple

RED_FLAGS = [
    "kematian mendadak", "banyak yang mati", "mati mendadak", "tidak bisa berdiri", "kejang",
    "sesak", "megap-megap", "perut kembung parah", "darah", "lumpuh", "demam tinggi",
    "tidak mau makan lebih dari 24 jam", "mortalitas", "menular", "wabah",
]

SYMPTOM_HINTS: Dict[str, Dict[str, str]] = {
    "diare": {
        "dugaan": "gangguan pencernaan, perubahan pakan mendadak, parasit/cacing, infeksi bakteri, atau kualitas air/pakan buruk",
        "awal": "pisahkan ternak sakit, sediakan air bersih, hentikan pakan yang dicurigai rusak, cek feses dan dehidrasi",
    },
    "mencret": {
        "dugaan": "gangguan pencernaan, perubahan pakan mendadak, parasit/cacing, infeksi bakteri, atau kualitas air/pakan buruk",
        "awal": "pisahkan ternak sakit, sediakan air bersih, hentikan pakan yang dicurigai rusak, cek feses dan dehidrasi",
    },
    "batuk": {
        "dugaan": "gangguan pernapasan, ventilasi buruk, litter/kandang lembap, debu/amonia, atau infeksi",
        "awal": "perbaiki ventilasi, kurangi debu/amonia, pisahkan yang berat, dan catat suhu/gejala pernapasan",
    },
    "kembung": {
        "dugaan": "bloat akibat hijauan terlalu muda/basah, konsentrat berlebih, perubahan pakan mendadak, atau gangguan rumen",
        "awal": "hentikan pakan pemicu, ajak ternak bergerak pelan, jangan beri pakan fermentasi/leguminosa berlebih, segera hubungi dokter hewan bila parah",
    },
    "pincang": {
        "dugaan": "luka kuku, lantai licin, infeksi kuku, trauma, atau defisiensi mineral",
        "awal": "cek kuku/luka, bersihkan area, pindahkan ke kandang kering, kurangi lantai licin, catat kaki yang terdampak",
    },
    "produksi telur turun": {
        "dugaan": "stres panas, pakan kurang protein/kalsium, penyakit, perubahan cahaya, air kurang, atau umur produksi",
        "awal": "cek konsumsi pakan-air, kualitas pakan, cahaya, suhu, mortalitas, dan gejala pernapasan/pencernaan",
    },
    "ikan megap-megap": {
        "dugaan": "oksigen terlarut rendah, amonia tinggi, kepadatan terlalu padat, atau kualitas air memburuk",
        "awal": "tambah aerasi/ganti sebagian air, hentikan pakan sementara, cek bau/warna air, kurangi kepadatan bila perlu",
    },
}


def detect_red_flags(text: str) -> List[str]:
    lowered = text.lower()
    return [flag for flag in RED_FLAGS if flag in lowered]


def triage_level(text: str) -> Tuple[str, List[str]]:
    flags = detect_red_flags(text)
    if flags:
        return "DARURAT", flags
    lowered = text.lower()
    if any(word in lowered for word in ["tidak mau makan", "lemas", "diare", "mencret", "batuk", "pincang", "luka", "kembung"]):
        return "PERLU DIPANTAU KETAT", []
    return "RINGAN / BUTUH DATA TAMBAHAN", []


def local_triage_summary(animal_type: str, symptoms: str, duration: str = "", affected: int | None = None, population: int | None = None) -> str:
    animal = animal_type or "ternak"
    level, flags = triage_level(symptoms)
    lowered = symptoms.lower()
    hints: List[str] = []
    for key, item in SYMPTOM_HINTS.items():
        if key in lowered:
            hints.append(f"- {key}: kemungkinan {item['dugaan']}. Tindakan awal: {item['awal']}.")
    if not hints:
        hints.append("- Data gejala belum spesifik. Amati nafsu makan, suhu tubuh, feses, pernapasan, kondisi kandang/kolam, dan perubahan pakan.")

    spread = ""
    if affected is not None and population:
        rate = affected / max(population, 1) * 100
        spread = f"\n- Terdampak: {affected}/{population} ekor ({rate:.1f}%)."

    warning = ""
    if flags:
        warning = "\n\nPeringatan: ada tanda bahaya: " + ", ".join(flags) + ". Segera hubungi dokter hewan/paramedik setempat dan lakukan isolasi/biosecurity."

    return (
        f"Triase awal untuk {animal}: **{level}**.{spread}\n"
        f"- Durasi gejala: {duration or 'belum diisi'}.\n"
        "\nDugaan awal dan tindakan aman:\n"
        + "\n".join(hints)
        + "\n\nData yang perlu dicatat: suhu bila ada termometer, jumlah sakit/mati, pakan terakhir, perubahan pakan, kondisi kandang/kolam, dan foto feses/luka bila tersedia."
        + warning
    )


def health_prompt_context(case: Dict[str, object]) -> str:
    return (
        "Kasus kesehatan ternak. Berikan triase, kemungkinan penyebab, tindakan awal aman, isolasi/biosecurity, pencegahan, dan kapan harus memanggil dokter hewan. "
        "Jangan memberikan dosis obat keras/antibiotik spesifik tanpa pemeriksaan.\n"
        f"Jenis ternak: {case.get('animal_type', '-')}; populasi: {case.get('population', '-')}; terdampak: {case.get('affected', '-')}; "
        f"umur/fase: {case.get('phase', '-')}; gejala: {case.get('symptoms', '-')}; durasi: {case.get('duration', '-')}; "
        f"pakan/air: {case.get('feed_water', '-')}; kandang/kolam: {case.get('housing', '-')}; kematian: {case.get('mortality', '-')}."
    )
