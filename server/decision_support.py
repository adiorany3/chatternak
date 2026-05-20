from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Tuple

from domain_data import FEED_RATES, DEFAULT_WEIGHTS
from ugm_departments import UGM_DEPARTMENTS
from farm_profile import profile_completeness, normalise_profile
from farm_records import summarize_records
from health_triage import triage_level

USER_MODES = ["Peternak Rakyat", "Industri Modern"]
EXPLANATION_LEVELS = ["Sangat sederhana", "Normal", "Teknis"]
CONSULTATION_TOPICS = ["Kesehatan", "Pakan", "Reproduksi", "Usaha/Biaya", "Kandang/Kolam", "Produksi"]

AUDIENCE_GUIDANCE = {
    "Peternak Rakyat": "Gunakan bahasa sederhana, istilah lapangan Indonesia, langkah bertahap, contoh praktis, dan hindari jargon kecuali dijelaskan. Prioritaskan bahan lokal murah, tindakan aman, dan pencatatan sederhana.",
    "Industri Modern": "Gunakan bahasa manajerial dan teknis. Sertakan KPI, SOP, audit trail, batch, risiko operasional, efisiensi biaya, biosecurity, target performa, dan rekomendasi berbasis data.",
}

LEVEL_GUIDANCE = {
    "Sangat sederhana": "Jelaskan seperti penyuluh ke peternak pemula. Pakai poin pendek dan contoh lapangan.",
    "Normal": "Berikan jawaban praktis dengan istilah teknis secukupnya.",
    "Teknis": "Berikan analisis lebih detail, asumsi, KPI, formula/perhitungan, dan implikasi manajemen.",
}

LOCAL_LIBRARY: Dict[str, Dict[str, str]] = {
    "rumput odot": {
        "kategori": "Hijauan",
        "ringkas": "Hijauan populer untuk ruminansia, produktif, palatabilitas baik, cocok untuk sapi/kambing jika dipanen tidak terlalu tua.",
        "catatan": "Jangan diberikan terlalu basah/terlalu muda berlebihan pada ruminansia sensitif; kombinasikan dengan serat dan konsentrat sesuai fase.",
    },
    "indigofera": {
        "kategori": "Leguminosa protein",
        "ringkas": "Sumber protein hijauan yang baik untuk kambing/sapi, berguna saat konsentrat mahal.",
        "catatan": "Berikan bertahap dan kombinasikan dengan rumput; jangan semua hijauan diganti leguminosa.",
    },
    "dedak/bekatul": {
        "kategori": "Energi-konsentrat",
        "ringkas": "Bahan pakan lokal murah, umum dipakai sebagai sumber energi dan sedikit protein.",
        "catatan": "Mudah tengik/berjamur; simpan kering dan jangan pakai jika bau apek.",
    },
    "ampas tahu": {
        "kategori": "Protein basah",
        "ringkas": "Bahan lokal bernilai untuk ruminansia, tetapi kadar air tinggi sehingga cepat rusak.",
        "catatan": "Gunakan segar, jangan bau asam/busuk; adaptasikan bertahap agar tidak mengganggu pencernaan.",
    },
    "maggot bsf": {
        "kategori": "Protein alternatif",
        "ringkas": "Sumber protein untuk unggas/ikan; potensial menekan biaya jika produksi lokal stabil.",
        "catatan": "Perhatikan proses pengeringan, sanitasi, dan konsistensi kualitas.",
    },
    "kandang panggung": {
        "kategori": "Kandang",
        "ringkas": "Banyak dipakai untuk kambing/domba karena feses jatuh ke bawah dan lantai lebih kering.",
        "catatan": "Celah lantai harus aman untuk kaki; ventilasi dan kemiringan pembuangan limbah tetap penting.",
    },
    "bioflok": {
        "kategori": "Budidaya ikan",
        "ringkas": "Sistem intensif yang memanfaatkan mikroba/flok untuk membantu kualitas air dan pakan alami.",
        "catatan": "Butuh aerasi kuat, kontrol kepadatan, pH, amonia, dan disiplin manajemen air.",
    },
    "silase": {
        "kategori": "Pengawetan pakan",
        "ringkas": "Teknik menyimpan hijauan secara anaerob agar stok pakan tersedia saat musim sulit.",
        "catatan": "Silase baik berbau asam segar, bukan busuk; hindari jamur dan adaptasikan bertahap.",
    },
}
# Kerangka akademik hulu-hilir peternakan. Dipakai agar aplikasi tidak hanya menjawab budidaya,
# tetapi juga mencakup nutrisi, produksi, sosial-ekonomi, teknologi hasil, serta reproduksi/pemuliaan.
for _dept in UGM_DEPARTMENTS:
    LOCAL_LIBRARY.setdefault(
        _dept["short_name"].lower(),
        {
            "kategori": "Kerangka 5 Departemen",
            "ringkas": f"{_dept['name']} mencakup {_dept['hulu_hilir_role']}",
            "catatan": "Cakupan: " + "; ".join(_dept.get("scope", [])[:3]),
        },
    )

EDUCATION_MODULES: Dict[str, List[Dict[str, str]]] = {
    "Dasar Beternak": [
        {"judul": "Mulai dari tujuan usaha", "materi": "Tentukan dulu apakah usaha untuk pedaging, petelur, pembibitan, susu, atau pembesaran. Tujuan menentukan bibit, pakan, kandang, dan jadwal panen.", "kuis": "Apa tujuan utama usaha ternak Anda?"},
        {"judul": "Catat data sederhana", "materi": "Minimal catat tanggal, populasi, pakan, bobot, mati/sakit, biaya, dan penjualan. Tanpa catatan, keuntungan sulit dihitung.", "kuis": "Sebutkan tiga data yang wajib dicatat setiap minggu."},
    ],
    "Pakan dan Nutrisi": [
        {"judul": "Pakan adalah biaya terbesar", "materi": "Efisiensi pakan menentukan untung rugi. Pakan murah belum tentu hemat jika pertumbuhan turun atau mortalitas naik.", "kuis": "Mengapa FCR penting untuk usaha ternak?"},
        {"judul": "Ganti pakan bertahap", "materi": "Perubahan pakan mendadak bisa menyebabkan stres pencernaan. Lakukan transisi 7-10 hari, terutama pada ruminansia.", "kuis": "Berapa hari ideal transisi pakan?"},
    ],
    "Kesehatan dan Biosecurity": [
        {"judul": "Isolasi ternak sakit", "materi": "Pisahkan ternak sakit untuk menekan penularan dan memudahkan pengamatan. Catat jumlah sakit dan gejala.", "kuis": "Apa tindakan pertama saat ada ternak sakit?"},
        {"judul": "Tanda bahaya", "materi": "Kematian mendadak, sesak, kembung parah, kejang, dan banyak ternak sakit bersamaan harus ditangani sebagai darurat.", "kuis": "Sebutkan dua tanda bahaya kesehatan ternak."},
    ],
    "Manajemen Industri": [
        {"judul": "Kelola berbasis KPI", "materi": "Farm modern perlu memantau ADG, FCR, mortalitas, produksi telur/susu, biaya pakan/kg gain, dan kepatuhan SOP.", "kuis": "Apa hubungan FCR dengan biaya produksi?"},
        {"judul": "Audit trail", "materi": "Keputusan pakan, vaksin, obat, panen, dan mortalitas harus punya tanggal, pelaksana, alasan, dan hasil evaluasi.", "kuis": "Mengapa audit trail penting di farm industri?"},
    ],
    "Kerangka 5 Departemen": [
        {"judul": "Hulu sampai hilir", "materi": "Peternakan tidak hanya budidaya. Keputusan harus membaca pakan, produksi, reproduksi/genetik, ekonomi usaha, serta mutu dan pengolahan hasil ternak.", "kuis": "Sebutkan lima bagian besar yang perlu diperhatikan dalam usaha peternakan."},
        {"judul": "Teknologi hasil ternak", "materi": "Setelah ternak dipanen, mutu daging, susu, telur, ikan, atau pupuk tetap harus dijaga melalui sortasi, kebersihan, penyimpanan, dan pengolahan yang aman.", "kuis": "Mengapa pascapanen penting dalam usaha peternakan?"},
    ],
}

SOP_TEMPLATES: Dict[str, List[str]] = {
    "Pemberian pakan": [
        "Cek kondisi pakan: tidak berjamur, tidak bau busuk/tengik, dan tidak tercampur benda asing.",
        "Berikan pakan sesuai fase, bobot, populasi, dan target produksi.",
        "Catat jumlah pakan masuk, pakan tersisa, dan perubahan konsumsi harian.",
        "Lakukan perubahan ransum bertahap 7-10 hari, terutama untuk ruminansia.",
        "Bersihkan tempat pakan secara rutin agar tidak menjadi sumber penyakit.",
    ],
    "Sanitasi kandang/kolam": [
        "Bersihkan feses, sisa pakan, litter basah, atau endapan organik sesuai komoditas.",
        "Pastikan ventilasi baik, lantai tidak licin, drainase lancar, dan area pakan-minum kering.",
        "Pisahkan alat untuk ternak sakit dan ternak sehat.",
        "Catat jadwal sanitasi dan masalah yang ditemukan.",
        "Untuk kolam, amati warna/bau air, aerasi, kepadatan, dan perilaku ikan saat pagi.",
    ],
    "Isolasi ternak sakit": [
        "Pindahkan ternak sakit ke kandang isolasi yang kering, tenang, dan mudah diamati.",
        "Gunakan alat terpisah untuk isolasi dan cuci tangan/alas kaki setelah kontak.",
        "Catat gejala, suhu bila tersedia, nafsu makan, feses, dan waktu mulai sakit.",
        "Jangan menjual atau memindahkan ternak sakit tanpa evaluasi.",
        "Hubungi dokter hewan bila ada tanda darurat atau kasus menyebar.",
    ],
    "Penerimaan bibit/bakalan/DOC": [
        "Siapkan kandang/kolam sebelum ternak datang: bersih, kering, air/pakan tersedia, suhu sesuai.",
        "Periksa fisik awal: aktif, tidak cacat, tidak lemah, tidak diare, dan bobot seragam.",
        "Lakukan karantina/adaptasi dan catat sumber, tanggal masuk, jumlah, bobot, dan kondisi awal.",
        "Jangan langsung mencampur ternak baru dengan populasi lama tanpa observasi.",
        "Evaluasi performa 3-7 hari pertama sebagai dasar keputusan lanjutan.",
    ],
    "Panen dan penjualan": [
        "Tentukan target bobot/umur/pasar sebelum panen.",
        "Sortir ternak berdasarkan bobot dan kondisi kesehatan.",
        "Hitung total biaya, bobot panen, harga jual, dan margin sebelum mengambil keputusan.",
        "Minimalkan stres saat penangkapan/pengangkutan.",
        "Catat hasil panen untuk evaluasi batch berikutnya.",
    ],
}

BIOSECURITY_ITEMS = [
    "Ada kandang/area isolasi ternak sakit atau ternak baru",
    "Tempat pakan dan minum dibersihkan rutin",
    "Litter/lantai/kandang tidak lembap berlebihan",
    "Akses tamu/kendaraan ke kandang dibatasi",
    "Ada desinfeksi alas kaki/peralatan dasar",
    "Bangkai/ternak mati ditangani aman dan dicatat",
    "Pakan disimpan kering dan terlindung dari tikus/air hujan",
    "Ada catatan sakit, mati, vaksin, dan perlakuan kesehatan",
]

KPI_TARGETS: Dict[str, Dict[str, Tuple[float | None, float | None, str]]] = {
    "sapi": {"adg": (0.4, None, "ADG sapi penggemukan sebaiknya positif dan stabil; target sangat tergantung genetik, pakan, dan fase."), "fcr": (None, 12.0, "FCR terlalu tinggi menandakan pakan boros/pertumbuhan lambat atau data belum rapi.")},
    "kambing": {"adg": (0.05, None, "ADG kambing penggemukan rakyat minimal harus positif dan konsisten."), "fcr": (None, 14.0, "FCR kambing sulit akurat bila pakan hijauan tidak ditimbang; gunakan sebagai indikator kasar.")},
    "ayam": {"fcr": (None, 2.5, "FCR unggas yang naik menandakan efisiensi turun, pakan/penyakit/suhu perlu dicek."), "mortality_rate": (None, 5.0, "Mortalitas tinggi perlu evaluasi kualitas bibit, brooding, pakan, air, dan biosecurity.")},
    "bebek": {"fcr": (None, 3.5, "FCR bebek dipengaruhi sistem pemeliharaan, kualitas pakan, dan umur panen."), "mortality_rate": (None, 5.0, "Mortalitas tinggi butuh evaluasi air, litter, kepadatan, dan penyakit." )},
    "ikan": {"fcr": (None, 2.0, "FCR ikan tinggi sering terkait kualitas air, pakan, kepadatan, atau penyakit."), "mortality_rate": (None, 10.0, "Mortalitas ikan tinggi harus cek oksigen, amonia, pH, dan kepadatan." )},
    "kelinci": {"adg": (0.015, None, "ADG kelinci rendah bisa terkait pakan, kepadatan, stres, atau penyakit pencernaan."), "mortality_rate": (None, 5.0, "Mortalitas kelinci harus diawasi ketat karena penyakit pencernaan dapat cepat menyebar." )},
}


def audience_context(mode: str, level: str) -> str:
    mode_text = AUDIENCE_GUIDANCE.get(mode, AUDIENCE_GUIDANCE["Peternak Rakyat"])
    level_text = LEVEL_GUIDANCE.get(level, LEVEL_GUIDANCE["Normal"])
    return f"Mode pengguna: {mode}. {mode_text}\nTingkat penjelasan: {level}. {level_text}"


def guided_questions(topic: str, case: Dict[str, Any]) -> List[str]:
    base = ["jenis_ternak", "jumlah_populasi", "umur_fase", "target_masalah"]
    topic_fields = {
        "Kesehatan": ["jumlah_terdampak", "gejala", "durasi", "kematian", "pakan_air", "kondisi_kandang"],
        "Pakan": ["bobot_rata_rata", "bahan_pakan", "harga_bahan", "konsumsi_pakan", "tujuan_formula"],
        "Reproduksi": ["tanggal_kawin_ib", "riwayat_beranak", "tanda_birahi", "kondisi_induk"],
        "Usaha/Biaya": ["modal", "biaya_pakan", "harga_jual", "target_panen", "tenaga_kerja"],
        "Kandang/Kolam": ["tipe_kandang", "ukuran", "kepadatan", "drainase_ventilasi", "masalah_lingkungan"],
        "Produksi": ["produksi_harian", "bobot_awal", "bobot_sekarang", "pakan_harian", "mortalitas"],
    }
    labels = {
        "jenis_ternak": "Jenis ternak/budidaya apa?",
        "jumlah_populasi": "Berapa jumlah populasi?",
        "umur_fase": "Umur atau fase produksinya apa?",
        "target_masalah": "Target atau masalah utama yang ingin diselesaikan?",
        "jumlah_terdampak": "Berapa ekor/kolam yang terdampak?",
        "gejala": "Gejala apa saja yang terlihat?",
        "durasi": "Sudah berapa lama terjadi?",
        "kematian": "Ada kematian? Berapa dan sejak kapan?",
        "pakan_air": "Pakan dan air terakhir seperti apa? Ada perubahan?",
        "kondisi_kandang": "Kondisi kandang/kolam: kering, lembap, bau amonia, air keruh, atau padat?",
        "bobot_rata_rata": "Berapa bobot rata-rata?",
        "bahan_pakan": "Bahan pakan lokal apa yang tersedia?",
        "harga_bahan": "Berapa harga tiap bahan pakan?",
        "konsumsi_pakan": "Berapa konsumsi pakan harian saat ini?",
        "tujuan_formula": "Target formula: murah, cepat gemuk, produksi telur/susu, atau aman untuk bunting?",
        "tanggal_kawin_ib": "Kapan tanggal kawin/IB terakhir?",
        "riwayat_beranak": "Riwayat beranak/kebuntingan sebelumnya bagaimana?",
        "tanda_birahi": "Ada tanda birahi atau tidak?",
        "kondisi_induk": "Kondisi induk: skor tubuh, nafsu makan, kesehatan?",
        "modal": "Berapa modal atau biaya berjalan yang tersedia?",
        "biaya_pakan": "Berapa biaya pakan per hari/bulan?",
        "harga_jual": "Berapa harga jual target?",
        "target_panen": "Kapan target panen atau penjualan?",
        "tenaga_kerja": "Berapa tenaga kerja yang mengelola?",
        "tipe_kandang": "Tipe kandang/kolam apa yang digunakan?",
        "ukuran": "Ukuran kandang/kolam berapa?",
        "kepadatan": "Kepadatan ternak/ikan seperti apa?",
        "drainase_ventilasi": "Bagaimana drainase, ventilasi, dan aliran udara/air?",
        "masalah_lingkungan": "Masalah lingkungan apa yang terlihat?",
        "produksi_harian": "Produksi harian/mingguan berapa?",
        "bobot_awal": "Bobot awal berapa?",
        "bobot_sekarang": "Bobot sekarang berapa?",
        "pakan_harian": "Pakan harian berapa kg?",
        "mortalitas": "Mortalitas/sakit berapa?",
    }
    fields = base + topic_fields.get(topic, [])
    missing = [labels[field] for field in fields if not str(case.get(field, "")).strip()]
    return missing


def guided_case_context(topic: str, case: Dict[str, Any]) -> str:
    lines = [f"Konsultasi bertahap topik: {topic}."]
    for key, value in case.items():
        if str(value).strip():
            lines.append(f"- {key}: {value}")
    missing = guided_questions(topic, case)
    if missing:
        lines.append("Data yang belum lengkap: " + "; ".join(missing[:8]))
    if topic == "Kesehatan":
        combined = " ".join(str(case.get(k, "")) for k in ["gejala", "kematian", "target_masalah"])
        level, flags = triage_level(combined)
        lines.append(f"Triase lokal: {level}. Tanda bahaya: {', '.join(flags) if flags else 'tidak terdeteksi dari teks'}.")
    return "\n".join(lines)


def benchmark_kpi(profile: Dict[str, Any], records: List[Dict[str, Any]]) -> Dict[str, Any]:
    p = normalise_profile(profile)
    animal = p.get("animal_type", "")
    summary = summarize_records(records)
    targets = KPI_TARGETS.get(animal, {})
    mortality_rate = None
    population = float(p.get("population", 0) or 0)
    if population > 0:
        mortality_rate = float(summary.get("mortality_total", 0) or 0) / population * 100
    metrics = {
        "adg": summary.get("adg"),
        "fcr": summary.get("fcr"),
        "mortality_rate": mortality_rate,
    }
    findings: List[str] = []
    risk = 0
    for metric, value in metrics.items():
        if value is None:
            findings.append(f"{metric.upper()}: belum cukup data.")
            continue
        low, high, note = targets.get(metric, (None, None, "Belum ada target spesifik; gunakan tren internal."))
        status = "Normal/terkendali"
        if low is not None and value < low:
            status = "Di bawah target"
            risk += 1
        if high is not None and value > high:
            status = "Di atas batas waspada"
            risk += 1
        findings.append(f"{metric.upper()}: {value:.3f} → {status}. {note}")
    level = "Rendah" if risk == 0 else "Sedang" if risk == 1 else "Tinggi"
    return {"animal_type": animal, "summary": summary, "metrics": metrics, "risk_level": level, "findings": findings}


def biosecurity_score(checked_items: List[str]) -> Dict[str, Any]:
    total = len(BIOSECURITY_ITEMS)
    checked = len(set(checked_items))
    score = round(checked / max(total, 1) * 100)
    if score >= 80:
        level = "Baik"
    elif score >= 50:
        level = "Sedang"
    else:
        level = "Berisiko"
    missing = [item for item in BIOSECURITY_ITEMS if item not in checked_items]
    return {"score": score, "level": level, "checked": checked, "total": total, "missing": missing}


def generate_sop(profile: Dict[str, Any], sop_type: str, mode: str = "Peternak Rakyat") -> str:
    p = normalise_profile(profile)
    items = SOP_TEMPLATES.get(sop_type, [])
    intro = f"SOP {sop_type} untuk {p.get('animal_type')} fase {p.get('phase')} - mode {mode}."
    if not items:
        items = ["Tentukan tujuan kegiatan.", "Siapkan alat dan bahan.", "Lakukan pekerjaan sesuai urutan.", "Catat hasil dan masalah.", "Evaluasi ulang 24 jam/7 hari berikutnya."]
    lines = [intro, "", "Langkah kerja:"]
    for idx, item in enumerate(items, 1):
        lines.append(f"{idx}. {item}")
    lines.extend([
        "", "Catatan wajib:",
        "- Tanggal, pelaksana, jumlah ternak terdampak, bahan/alat yang dipakai, dan hasil pengamatan.",
        "- Bila ada kasus sakit/kematian, prioritaskan isolasi dan konsultasi dokter hewan/paramedik.",
    ])
    return "\n".join(lines)


def predict_operations(profile: Dict[str, Any], records: List[Dict[str, Any]], feed_stock_kg: float, target_weight_kg: float, sale_price_per_unit: float, extra_cost_rp: float) -> Dict[str, Any]:
    p = normalise_profile(profile)
    animal = p.get("animal_type", "")
    population = int(p.get("population", 0) or 0)
    avg_weight = float(p.get("average_weight_kg", 0) or DEFAULT_WEIGHTS.get(animal, 1.0))
    summary = summarize_records(records)
    daily_need = avg_weight * float(FEED_RATES.get(animal, 0.03)) * max(population, 1)
    stock_days = float(feed_stock_kg or 0) / daily_need if daily_need > 0 else 0
    adg = summary.get("adg")
    if not adg or adg <= 0:
        adg = 0.05 if animal in {"kambing", "kelinci"} else 0.1 if animal in {"ayam", "bebek"} else 0.4 if animal == "sapi" else 0.01
    days_to_harvest = max((float(target_weight_kg or avg_weight) - avg_weight) / adg, 0) if target_weight_kg else None
    harvest_date = (date.today() + timedelta(days=int(days_to_harvest))).isoformat() if days_to_harvest is not None else "Belum dihitung"
    feed_needed_to_harvest = daily_need * float(days_to_harvest or 0)
    estimated_revenue = float(sale_price_per_unit or 0) * max(population, 1)
    estimated_margin = estimated_revenue - float(extra_cost_rp or 0)
    return {
        "daily_feed_need_kg": daily_need,
        "feed_stock_days": stock_days,
        "adg_used_kg_day": adg,
        "days_to_harvest": days_to_harvest,
        "harvest_date": harvest_date,
        "feed_needed_to_harvest_kg": feed_needed_to_harvest,
        "estimated_revenue_rp": estimated_revenue,
        "estimated_margin_before_unrecorded_cost_rp": estimated_margin,
    }


def readiness_score(profile: Dict[str, Any], records: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], checked_biosecurity: List[str]) -> Dict[str, Any]:
    p = normalise_profile(profile)
    score = 0
    reasons: List[str] = []
    completeness = profile_completeness(p)
    score += min(completeness, 100) * 0.30
    if records:
        score += 20
    else:
        reasons.append("Belum ada catatan performa/recording.")
    if calendar_events:
        score += 15
    else:
        reasons.append("Kalender manajemen belum dibuat.")
    bio = biosecurity_score(checked_biosecurity)
    score += bio["score"] * 0.25
    if p.get("feed_available"):
        score += 10
    else:
        reasons.append("Bahan pakan tersedia belum dicatat.")
    final = round(min(score, 100))
    if final >= 80:
        level = "Siap/terkendali"
    elif final >= 60:
        level = "Cukup, perlu perbaikan"
    else:
        level = "Belum siap/berisiko"
    reasons.extend([f"Biosecurity belum lengkap: {item}" for item in bio["missing"][:3]])
    return {"score": final, "level": level, "reasons": reasons[:6], "biosecurity": bio}
