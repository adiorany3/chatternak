from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Iterable, List, Tuple
from xml.sax.saxutils import escape
from ugm_departments import UGM_DEPARTMENTS, HULU_HILIR_FLOW, department_coverage_check
from commodity_breeds import breed_detail, commodity_context as commodity_breed_context, commodity_label
from farm_profile import goal_context, goal_label

APP_NAME = "AI Pakar Ternak"
DEVELOPER = "Developed by Galuh Adi Insani (Fakultas Peternakan UGM)"


def _text(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}".replace(",", ".")
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    text = str(value).strip()
    return text if text else default


def _rp(value: Any) -> str:
    try:
        number = float(value or 0)
    except Exception:
        number = 0.0
    return "Rp " + f"{number:,.0f}".replace(",", ".")


def _pct(value: Any) -> str:
    try:
        return f"{float(value):.1f}%".replace(".", ",")
    except Exception:
        return "-"


def _safe_para(text: Any) -> str:
    cleaned = _text(text).replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("→", "->").replace("–", "-").replace("—", "-")
    return escape(cleaned).replace("\n", "<br/>")


def _first_items(items: Iterable[Any], limit: int = 6) -> List[str]:
    result: List[str] = []
    for item in items or []:
        if isinstance(item, dict):
            result.append(json.dumps(item, ensure_ascii=False))
        else:
            result.append(str(item))
        if len(result) >= limit:
            break
    return result


def _profile_rows(profile: Dict[str, Any]) -> List[Tuple[str, str]]:
    labels = {
        "farm_name": "Nama Farm / Kelompok",
        "animal_type": "Komoditas Ternak",
        "breed": "Bangsa / Ras / Strain",
        "production_goal": "Tujuan Pemeliharaan",
        "phase": "Fase Ternak",
        "population": "Populasi",
        "average_age": "Umur Rata-rata",
        "average_weight_kg": "Bobot Rata-rata (kg)",
        "location": "Lokasi / Iklim",
        "housing_system": "Sistem Kandang / Kolam",
        "feed_available": "Bahan Pakan Tersedia",
        "water_source": "Sumber Air",
        "main_problem": "Masalah Utama",
        "budget_note": "Catatan Modal / Biaya",
        "market_target": "Target Pasar",
    }
    rows: List[Tuple[str, str]] = []
    for key, label in labels.items():
        value = profile.get(key)
        if key == "animal_type":
            value = commodity_label(value)
        elif key == "production_goal":
            value = goal_label(value)
        rows.append((label, _text(value)))
    return rows


def _records_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {"count": 0, "mortality": 0, "feed": 0.0, "cost": 0.0, "latest": {}}
    sorted_records = sorted(records, key=lambda r: str(r.get("date", "")))
    mortality = sum(int(float(r.get("mortality", 0) or 0)) for r in sorted_records)
    feed = sum(float(r.get("feed_kg", 0) or 0) for r in sorted_records)
    cost = sum(float(r.get("cost_rp", 0) or 0) for r in sorted_records)
    return {"count": len(sorted_records), "mortality": mortality, "feed": feed, "cost": cost, "latest": sorted_records[-1]}


def _make_paragraph(text: Any, style: Any):
    from reportlab.platypus import Paragraph

    return Paragraph(_safe_para(text), style)


def _make_table(data: List[List[Any]], widths: List[float] | None = None, header: bool = True):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    table = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ]
    if header and data:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ])
    start_row = 1 if header else 0
    for row_idx in range(start_row, len(data)):
        if row_idx % 2 == 0:
            commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#F8FAFC")))
    table.setStyle(TableStyle(commands))
    return table


def pdf_report_filename(payload: Dict[str, Any]) -> str:
    profile = payload.get("profile", {}) or {}
    farm_name = str(profile.get("farm_name") or "farm").strip().lower()
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in farm_name).strip("-") or "farm"
    date_code = datetime.now().strftime("%Y%m%d-%H%M")
    return f"laporan-ai-pakar-ternak-{safe_name}-{date_code}.pdf"


def generate_pdf_report(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> bytes:
    """Generate a readable, professional PDF farm report from the current session payload.

    The function intentionally depends only on plain dictionaries so it can be reused by
    Streamlit download buttons, tests, or future batch exports.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import KeepTogether, PageBreak, SimpleDocTemplate, Spacer
    except Exception as error:  # pragma: no cover - user-facing dependency hint
        raise RuntimeError(
            "ReportLab belum terpasang. Pastikan requirements.txt memuat reportlab>=4.2.0 lalu redeploy aplikasi."
        ) from error

    context = context or {}
    profile = payload.get("profile", {}) or {}
    records = payload.get("records", []) or []
    calendar = payload.get("calendar_events", []) or []
    health = payload.get("last_health_case", {}) or {}
    insight = payload.get("last_ai_insight", {}) or {}
    usage = payload.get("usage", {}) or {}
    app_state = payload.get("app_state", {}) or {}
    decision_log = app_state.get("decision_log", []) or []
    benchmark = context.get("benchmark", {}) or {}
    readiness = context.get("readiness", {}) or {}
    risk = context.get("risk", {}) or app_state.get("last_risk_score", {}) or {}
    local_insights = context.get("local_insights", []) or []
    department_coverage = context.get("department_coverage") or department_coverage_check(profile, records, calendar, health, {"decision_log": decision_log})
    records_summary = _records_summary(records)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
        title="Laporan AI Pakar Ternak",
        author="Galuh Adi Insani (Fakultas Peternakan UGM)",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=29,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#14532D"),
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="CoverSub",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=18,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#166534"),
        spaceBefore=10,
        spaceAfter=7,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontSize=9.2,
        leading=12.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#475569"),
    ))
    styles.add(ParagraphStyle(
        name="Callout",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#DCFCE7"),
        borderColor=colors.HexColor("#86EFAC"),
        borderWidth=0.6,
        borderPadding=8,
        spaceAfter=8,
    ))

    def page_footer(canvas, doc_obj):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(1.35 * cm, 1.08 * cm, width - 1.35 * cm, 1.08 * cm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#475569"))
        canvas.drawString(1.35 * cm, 0.68 * cm, DEVELOPER)
        canvas.drawRightString(width - 1.35 * cm, 0.68 * cm, f"Halaman {doc_obj.page}")
        canvas.restoreState()

    story: List[Any] = []

    farm_name = _text(profile.get("farm_name"), "Nama farm belum diisi")
    generated_at = datetime.now().strftime("%d-%m-%Y %H:%M")
    user_mode = app_state.get("user_mode") or "-"
    explanation_level = app_state.get("explanation_level") or "-"

    story.append(Spacer(1, 1.5 * cm))
    story.append(_make_paragraph("Laporan Peternakan", styles["CoverTitle"]))
    story.append(_make_paragraph("AI Pakar Ternak", styles["CoverTitle"]))
    story.append(_make_paragraph(
        "Laporan profesional berbasis data session: profil farm, recording performa, biosecurity, agenda manajemen, insight AI, dan log keputusan.",
        styles["CoverSub"],
    ))
    cover_rows = [
        ["Nama Farm", _make_paragraph(farm_name, styles["Body"])],
        ["Komoditas", _make_paragraph(f"{commodity_label(profile.get('animal_type'))} - {_text(profile.get('breed'))} - {goal_label(profile.get('production_goal'))}", styles["Body"])],
        ["Populasi", _make_paragraph(f"{_text(profile.get('population'))} ekor", styles["Body"])],
        ["Tanggal Laporan", _make_paragraph(generated_at, styles["Body"])],
        ["Mode Pengguna", _make_paragraph(f"{user_mode} / {explanation_level}", styles["Body"])],
    ]
    story.append(_make_table(cover_rows, [4.2 * cm, 11.5 * cm], header=False))
    story.append(Spacer(1, 1.2 * cm))
    story.append(_make_paragraph(DEVELOPER, styles["CoverSub"]))
    story.append(PageBreak())

    story.append(_make_paragraph("1. Ringkasan Eksekutif", styles["SectionTitle"]))
    score = readiness.get("score", "-")
    ready_level = readiness.get("level", "-")
    risk_level = risk.get("level", "-")
    risk_score = risk.get("score", "-")
    summary_text = (
        f"Farm {farm_name} memiliki komoditas {commodity_label(profile.get('animal_type'))} bangsa/strain {_text(profile.get('breed'))}, tujuan pemeliharaan {goal_label(profile.get('production_goal'))}, fase {_text(profile.get('phase'))}. "
        f"Skor kesiapan saat ini {_text(score)}/100 dengan level {_text(ready_level)}. "
        f"Skor risiko farm {_text(risk_score)}/100 dengan status {_text(risk_level)}. "
        "Rekomendasi pada laporan ini perlu dibaca sebagai dasar pengambilan keputusan manajemen, bukan pengganti pemeriksaan dokter hewan pada kasus kesehatan serius."
    )
    story.append(_make_paragraph(summary_text, styles["Callout"]))
    score_table = [
        ["Indikator", "Nilai", "Catatan"],
        ["Kesiapan Farm", _text(score) + "/100", _text(ready_level)],
        ["Risiko Farm", _text(risk_score) + "/100", _text(risk_level)],
        ["Risiko KPI", _text(benchmark.get("risk_level")), "; ".join(_first_items(benchmark.get("findings", []), 2)) or "-"],
        ["Catatan Performa", _text(records_summary["count"]), f"Pakan: {_text(records_summary['feed'])} kg; Mortalitas: {_text(records_summary['mortality'])} ekor"],
        ["Agenda Manajemen", _text(len(calendar)), "Jumlah agenda/jadwal yang tersimpan"],
        ["Pemakaian AI", _text(usage.get("requests", 0)) + " request", f"Token: {_text(usage.get('total_tokens', 0))}; Estimasi: {_rp(usage.get('estimated_cost_rp', 0))}"],
    ]
    story.append(_make_table([[ _make_paragraph(c, styles["Body"]) for c in row] for row in score_table], [4.2 * cm, 3.2 * cm, 8.5 * cm]))

    story.append(_make_paragraph("Prioritas Rekomendasi", styles["SectionTitle"]))
    reasons = readiness.get("reasons", []) or []
    risk_reasons = risk.get("reasons", []) or []
    priorities = _first_items(local_insights, 5) or _first_items(reasons + risk_reasons, 6) or ["Lengkapi profil, catatan pakan, bobot, mortalitas, dan biaya agar insight makin akurat."]
    for idx, item in enumerate(priorities, 1):
        story.append(_make_paragraph(f"{idx}. {item}", styles["Body"]))

    story.append(_make_paragraph("2. Profil Farm", styles["SectionTitle"]))
    profile_table = [["Kolom", "Isi"]] + [[label, _make_paragraph(value, styles["Body"])] for label, value in _profile_rows(profile)]
    story.append(_make_table(profile_table, [5.0 * cm, 11.0 * cm]))
    story.append(Spacer(1, 0.18 * cm))
    story.append(_make_paragraph("Konteks Komoditas dan Bangsa/Ras/Strain", styles["SectionTitle"]))
    story.append(_make_paragraph(commodity_breed_context(profile.get("animal_type", ""), profile.get("breed", "")), styles["Body"]))
    story.append(Spacer(1, 0.18 * cm))
    story.append(_make_paragraph("Konteks Tujuan Pemeliharaan", styles["SectionTitle"]))
    story.append(_make_paragraph(goal_context(profile.get("production_goal", ""), profile.get("animal_type", "")), styles["Body"]))


    story.append(_make_paragraph("3. Kerangka 5 Departemen Hulu-Hilir", styles["SectionTitle"]))
    story.append(_make_paragraph(
        "Bagian ini memastikan laporan tidak berhenti pada budidaya, tetapi juga membaca nutrisi-pakan, produksi, sosial-ekonomi, teknologi hasil, serta pemuliaan-reproduksi.",
        styles["Body"],
    ))
    dept_data = [["Departemen", "Peran", "Status Data", "Perlu Dilengkapi"]]
    coverage_map = {item.get("Departemen"): item for item in department_coverage if isinstance(item, dict)}
    for dept in UGM_DEPARTMENTS:
        cov = coverage_map.get(dept["name"], {})
        dept_data.append([
            _make_paragraph(dept["name"], styles["Small"]),
            _make_paragraph(dept["hulu_hilir_role"], styles["Small"]),
            _text(cov.get("Status Data")),
            _make_paragraph(cov.get("Perlu Dilengkapi", "-"), styles["Small"]),
        ])
    story.append(_make_table(dept_data, [3.6 * cm, 5.0 * cm, 2.4 * cm, 5.0 * cm]))
    flow_data = [["Tahap", "Departemen", "Fungsi"]] + [[stage, dept, _make_paragraph(desc, styles["Small"])] for stage, dept, desc in HULU_HILIR_FLOW]
    story.append(_make_paragraph("Alur hulu-hilir", styles["Body"]))
    story.append(_make_table(flow_data, [3.0 * cm, 4.6 * cm, 8.4 * cm]))

    story.append(_make_paragraph("4. KPI dan Recording Performa", styles["SectionTitle"]))
    metric_rows = [["Metrik", "Nilai"]]
    metrics = benchmark.get("metrics", {}) or {}
    metric_rows.extend([
        ["ADG", _text(metrics.get("adg")) + (" kg/hari" if metrics.get("adg") is not None else "")],
        ["FCR", _text(metrics.get("fcr"))],
        ["Mortalitas", _pct(metrics.get("mortality_rate")) if metrics.get("mortality_rate") is not None else f"{_text(records_summary['mortality'])} ekor"],
        ["Total Pakan Tercatat", _text(records_summary["feed"]) + " kg"],
        ["Total Biaya Tercatat", _rp(records_summary["cost"])],
    ])
    story.append(_make_table([[ _make_paragraph(c, styles["Body"]) for c in row] for row in metric_rows], [6.0 * cm, 10.0 * cm]))
    findings = benchmark.get("findings", []) or []
    if findings:
        story.append(_make_paragraph("Temuan KPI:", styles["Body"]))
        for item in _first_items(findings, 6):
            story.append(_make_paragraph(f"- {item}", styles["Body"]))

    recent_records = sorted(records, key=lambda r: str(r.get("date", "")), reverse=True)[:10]
    if recent_records:
        record_data = [["Tanggal", "Populasi", "Bobot", "Pakan", "Biaya", "Mati", "Catatan"]]
        for rec in recent_records:
            record_data.append([
                _text(rec.get("date")),
                _text(rec.get("population")),
                _text(rec.get("avg_weight_kg")),
                _text(rec.get("feed_kg")),
                _rp(rec.get("cost_rp")),
                _text(rec.get("mortality")),
                _make_paragraph(rec.get("notes", "-"), styles["Small"]),
            ])
        story.append(_make_paragraph("10 Catatan Performa Terbaru", styles["SectionTitle"]))
        story.append(_make_table(record_data, [2.2 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 2.5 * cm, 1.5 * cm, 4.5 * cm]))
    else:
        story.append(_make_paragraph("Belum ada catatan performa. Mulai catat bobot, pakan, biaya, mortalitas, telur/susu, dan catatan harian.", styles["Body"]))

    story.append(_make_paragraph("5. Kesehatan, Biosecurity, dan Agenda", styles["SectionTitle"]))
    bio = readiness.get("biosecurity", {}) or {}
    health_rows = [
        ["Aspek", "Ringkasan"],
        ["Kasus kesehatan terakhir", _make_paragraph(json.dumps(health, ensure_ascii=False, indent=2) if health else "Belum ada kasus kesehatan tersimpan.", styles["Small"])],
        ["Biosecurity", _make_paragraph(f"Skor {_text(bio.get('score'))}/100 - level {_text(bio.get('level'))}. Checklist lengkap: {_text(bio.get('checked'))}/{_text(bio.get('total'))}.", styles["Body"])],
        ["Kekurangan utama", _make_paragraph("; ".join(_first_items(bio.get("missing", []), 8)) or "Checklist utama terpenuhi.", styles["Body"])],
    ]
    story.append(_make_table(health_rows, [4.5 * cm, 11.5 * cm]))

    upcoming = sorted(calendar, key=lambda r: str(r.get("date", "")))[:12]
    if upcoming:
        agenda_data = [["Tanggal", "Kegiatan", "Status", "Catatan"]]
        for event in upcoming:
            agenda_data.append([
                _text(event.get("date")),
                _make_paragraph(event.get("activity", event.get("kegiatan", "-")), styles["Small"]),
                _text(event.get("status")),
                _make_paragraph(event.get("notes", event.get("catatan", event.get("description", "-"))), styles["Small"]),
            ])
        story.append(_make_paragraph("Agenda Manajemen", styles["SectionTitle"]))
        story.append(_make_table(agenda_data, [2.7 * cm, 5.2 * cm, 2.4 * cm, 5.7 * cm]))

    story.append(_make_paragraph("6. Insight AI dan Log Keputusan", styles["SectionTitle"]))
    ai_content = insight.get("content") if isinstance(insight, dict) else ""
    if ai_content:
        excerpt = str(ai_content).strip()
        if len(excerpt) > 2400:
            excerpt = excerpt[:2400].rsplit(" ", 1)[0] + "..."
        story.append(_make_paragraph("Insight AI terakhir:", styles["Body"]))
        story.append(_make_paragraph(excerpt, styles["Small"]))
    else:
        story.append(_make_paragraph("Belum ada insight AI lengkap yang tersimpan. Gunakan menu Insight & Keputusan untuk membuat insight AI.", styles["Body"]))

    if decision_log:
        log_data = [["Tanggal", "Masalah", "Keputusan", "Prioritas", "Risiko", "Status"]]
        for item in decision_log[-10:]:
            log_data.append([
                _text(item.get("created_at")),
                _make_paragraph(item.get("question", "-"), styles["Small"]),
                _make_paragraph(item.get("main_decision", "-"), styles["Small"]),
                _text(item.get("priority")),
                _text(item.get("risk_level")),
                _text(item.get("follow_up_status")),
            ])
        story.append(_make_paragraph("10 Log Keputusan Terbaru", styles["SectionTitle"]))
        story.append(_make_table(log_data, [2.6 * cm, 3.6 * cm, 5.2 * cm, 1.8 * cm, 1.8 * cm, 1.8 * cm]))
    else:
        story.append(_make_paragraph("Belum ada log keputusan AI. Setiap insight/konsultasi penting akan tersimpan agar dapat dievaluasi kembali.", styles["Body"]))

    story.append(_make_paragraph("7. Catatan Penutup", styles["SectionTitle"]))
    story.append(_make_paragraph(
        "Laporan ini disusun dari data yang diinput pengguna. Akurasi rekomendasi bergantung pada kelengkapan data lapangan. Untuk kasus darurat, kematian mendadak, demam tinggi, sesak napas, diare berdarah, kembung berat, atau penurunan produksi drastis, segera hubungi dokter hewan/paramedik setempat.",
        styles["Body"],
    ))
    story.append(_make_paragraph(DEVELOPER, styles["Body"]))

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return buffer.getvalue()
