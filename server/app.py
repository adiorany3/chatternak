from __future__ import annotations

import hashlib
import inspect
import json
import os
import tempfile
import traceback
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import quote

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from calculators import calculate_bep, calculate_feed_needs, predict_growth
from ai_insights import (
    build_ai_insight_context,
    build_scorecard,
    format_insights_markdown,
    insight_prompt,
    local_operational_insights,
)
from chat_router import answer_message
from domain_data import ANIMAL_TYPES, DEFAULT_WEIGHTS, FEED_RATES
from farm_calendar import generate_management_events
from farm_profile import (
    ANIMAL_PHASES,
    DEFAULT_PROFILE,
    PRODUCTION_GOALS,
    breeding_dates,
    goal_context,
    goal_label,
    goal_options,
    normalise_profile,
    phase_guidance,
    profile_completeness,
    quick_management_checklist,
    summarize_profile,
)
from farm_records import add_record, performance_flags, records_context, summarize_records
from feed_formulation import LOCAL_FEED_INGREDIENTS, formula_feedback, simple_ruminant_ration
from health_triage import health_prompt_context, local_triage_summary, triage_level
from decision_support import (
    BIOSECURITY_ITEMS,
    CONSULTATION_TOPICS,
    EDUCATION_MODULES,
    EXPLANATION_LEVELS,
    LOCAL_LIBRARY,
    SOP_TEMPLATES,
    USER_MODES,
    audience_context,
    benchmark_kpi,
    biosecurity_score,
    generate_sop,
    guided_case_context,
    guided_questions,
    predict_operations,
    readiness_score,
)
from model_catalog import format_model_option, format_rupiah, get_model_by_id, load_model_catalog
from openai_integration import DEFAULT_CONFIG, OpenAIChatAPI
from session_storage import build_session_payload, export_session_xlsx, import_session_xlsx, session_filename
from pdf_report import generate_pdf_report, pdf_report_filename
from ui_theme import apply_accessible_theme
from commodity_breeds import (
    AQUACULTURE,
    RUMINANTS,
    POULTRY,
    breed_detail,
    breed_options,
    catalog_markdown,
    catalog_rows,
    commodity_context as commodity_breed_context,
    commodity_label,
)
from ugm_departments import (
    UGM_DEPARTMENTS,
    HULU_HILIR_FLOW,
    department_coverage_check,
    department_markdown,
    hulu_hilir_markdown,
    department_prompt_for_text,
    report_section_markdown,
)
from farm_memory import (
    MEMORY_CATEGORIES,
    PRIORITIES,
    memory_context,
    memory_from_secrets,
    memory_table_rows,
    normalise_memory_items,
    make_memory_item,
    suggest_memory_from_session,
)
from expert_rules import (
    build_expert_context,
    decision_card_from_answer,
    farm_risk_score,
    rewrite_instruction,
    TECHNICAL_GLOSSARY,
    COMMODITY_TEMPLATES,
)
from enterprise_features import (
    ROLE_OPTIONS,
    ROLE_DESCRIPTIONS,
    DEFAULT_ENTERPRISE_STATE,
    normalise_enterprise_state,
    make_audit_event,
    kpi_standard_for,
    validate_record_data,
    early_warnings,
    executive_summary,
    finance_snapshot,
    knowledge_search,
    downstream_guidance,
    notification_messages,
    enterprise_context,
    enterprise_report_markdown,
)
from enterprise_storage import get_storage_config, save_payload as save_enterprise_payload, load_payload as load_enterprise_payload, test_connection as test_enterprise_database_connection

PROJECT_DIR = Path(__file__).resolve().parent
SESSION_BACKUP_DIR = Path(tempfile.gettempdir()) / "ai_pakar_ternak_sessions"

st.set_page_config(
    page_title="AI Pakar Ternak",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_accessible_theme()

client = OpenAIChatAPI()
AI_LOADING_TEXT = "Kami siapkan pertanyaan detail untuk Anda, tunggu sebentar ...."
model_catalog = load_model_catalog()
limits_config = client.config.get("limits", DEFAULT_CONFIG["limits"])
ui_config = client.config.get("ui", DEFAULT_CONFIG["ui"])

ADMIN_PLACEHOLDERS = {
    "",
    "ISI_KUNCI_ADMIN_ANDA",
    "ISI_ADMIN_PASSWORD_ANDA",
    "CHANGE_ME",
    "YOUR_ADMIN_PASSWORD",
    "ADMIN_PASSWORD_HERE",
}

APP_MODES = [
    "Beranda",
    "Input Data",
    "Konsultasi AI",
    "Insight & Keputusan",
    "Manajemen Enterprise",
    "Database Supabase",
    "Alat Hitung",
    "Edukasi & Laporan",
]

WORKFLOW_STEPS = [
    {
        "step": "1",
        "title": "Isi profil farm",
        "description": "Masukkan jenis ternak, populasi, fase, bobot, lokasi, pakan, dan masalah utama.",
        "menu": "Input Data",
    },
    {
        "step": "2",
        "title": "Catat data lapangan",
        "description": "Tambahkan bobot, pakan, mortalitas, biaya, produksi, dan jadwal manajemen.",
        "menu": "Input Data",
    },
    {
        "step": "3",
        "title": "Konsultasikan masalah",
        "description": "Gunakan konsultasi bertahap atau chat pakar agar AI bertanya sesuai data yang kurang.",
        "menu": "Konsultasi AI",
    },
    {
        "step": "4",
        "title": "Ambil keputusan",
        "description": "Baca insight, KPI, prediksi usaha, rekomendasi pakan, SOP, dan risiko biosecurity.",
        "menu": "Insight & Keputusan",
    },
    {
        "step": "5",
        "title": "Simpan backup XLSX",
        "description": "Unduh file XLSX agar data tetap bisa dibaca dan dipulihkan meskipun sesi Streamlit habis.",
        "menu": "Sidebar Backup",
    },
]


def init_state() -> None:
    defaults: Dict[str, Any] = {
        "session_id": uuid.uuid4().hex[:12],
        "last_autosave_path": "",
        "last_autosave_at": "",
        "last_autosave_error": "",
        "messages": [],
        "last_meta": {},
        "session_request_count": 0,
        "session_prompt_tokens": 0,
        "session_completion_tokens": 0,
        "session_total_tokens": 0,
        "session_estimated_cost_rp": 0.0,
        "admin_authenticated": False,
        "admin_login_error": "",
        "user_mode": "Peternak Rakyat",
        "explanation_level": "Normal",
        "guided_case": {},
        "guided_topic": "Kesehatan",
        "biosecurity_checked": [],
        "last_sop": {},
        "last_prediction": {},
        "last_risk_score": {},
        "decision_log": [],
        "education_progress": [],
        "expert_memory": [],
        "expert_memory_suggestions": [],
        "enterprise_state": dict(DEFAULT_ENTERPRISE_STATE),
        "farm_profile": dict(DEFAULT_PROFILE),
        "farm_records": [],
        "farm_calendar_events": [],
        "last_health_case": {},
        "last_ai_insight": {},
        "formula_selected": ["rumput odot", "dedak", "ampas tahu", "mineral mix"],
        "confirm_reset_chat_nonce": 0,
        "confirm_reset_farm_nonce": 0,
        "confirm_clear_log_nonce": 0,
        "reset_notice": "",
        "prepared_download_hash": "",
        "prepared_xlsx_bytes": b"",
        "prepared_pdf_bytes": b"",
        "prepared_xlsx_name": "",
        "prepared_pdf_name": "",
        "last_autosave_hash": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value



def safe_rerun() -> None:
    """Rerun wrapper that stays compatible across Streamlit versions."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def render_safe_error(section_name: str, error: Exception) -> None:
    """Show a user-safe error without stopping the whole app."""
    st.error(f"Bagian **{section_name}** mengalami kendala, tetapi aplikasi tetap berjalan.")
    st.info("Silakan download Backup XLSX sebelum refresh atau mencoba kembali. Data yang sudah tersimpan di sesi masih dapat diekspor.")
    try:
        payload = build_current_session_payload()
        st.download_button(
            "Download Backup XLSX Darurat",
            data=export_session_xlsx(payload),
            file_name=session_filename(payload),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            key=f"emergency_backup_{section_name.replace(' ', '_').lower()}",
        )
    except Exception:
        pass
    if st.session_state.get("admin_authenticated", False):
        with st.expander("Detail error admin", expanded=False):
            st.code("".join(traceback.format_exception_only(type(error), error)).strip())


def safe_render(section_name: str, render_func, *args, **kwargs) -> None:
    """Render a section in a protective wrapper so one component error does not crash the app."""
    try:
        render_func(*args, **kwargs)
    except Exception as error:
        render_safe_error(section_name, error)


def safe_build_bytes(label: str, builder, fallback: bytes = b"") -> bytes:
    try:
        return builder()
    except Exception as error:
        if st.session_state.get("admin_authenticated", False):
            st.warning(f"Gagal membuat {label}: {error}")
        return fallback


def stable_json_dumps(payload: Dict[str, Any]) -> str:
    """JSON stabil untuk cache/fingerprint; aman untuk date/datetime/bytes."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def payload_fingerprint(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(stable_json_dumps(payload).encode("utf-8")).hexdigest()[:16]


@st.cache_data(show_spinner=False, ttl=300, max_entries=12)
def cached_xlsx_bytes(payload_json: str) -> bytes:
    return export_session_xlsx(json.loads(payload_json))


@st.cache_data(show_spinner=False, ttl=300, max_entries=8)
def cached_pdf_bytes(payload_json: str, context_json: str) -> bytes:
    return generate_pdf_report(json.loads(payload_json), json.loads(context_json))


def prepare_download_files(include_pdf: bool = True) -> None:
    """Siapkan file download hanya saat diminta agar pindah dropdown/menu tetap ringan."""
    payload = build_current_session_payload()
    payload_json = stable_json_dumps(payload)
    current_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()[:16]
    st.session_state.prepared_xlsx_bytes = cached_xlsx_bytes(payload_json)
    st.session_state.prepared_xlsx_name = session_filename(payload)
    if include_pdf:
        context_json = stable_json_dumps(build_pdf_report_context())
        st.session_state.prepared_pdf_bytes = cached_pdf_bytes(payload_json, context_json)
        st.session_state.prepared_pdf_name = pdf_report_filename(payload)
    st.session_state.prepared_download_hash = current_hash


def clear_prepared_downloads_if_stale() -> None:
    """Jaga supaya tombol download tidak keliru saat data berubah, tanpa membuat file ulang otomatis."""
    try:
        payload = build_current_session_payload()
        current_hash = payload_fingerprint(payload)
        if st.session_state.get("prepared_download_hash") and st.session_state.prepared_download_hash != current_hash:
            st.session_state.prepared_download_hash = ""
    except Exception:
        pass

def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.last_meta = {}
    st.session_state.session_request_count = 0
    st.session_state.session_prompt_tokens = 0
    st.session_state.session_completion_tokens = 0
    st.session_state.session_total_tokens = 0
    st.session_state.session_estimated_cost_rp = 0.0


def reset_farm_data() -> None:
    st.session_state.farm_profile = dict(DEFAULT_PROFILE)
    st.session_state.farm_records = []
    st.session_state.farm_calendar_events = []
    st.session_state.last_health_case = {}


def update_usage(meta: Dict[str, Any]) -> None:
    if meta.get("source") != "ai":
        return
    usage = meta.get("usage", {}) or {}
    prompt_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
    completion_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
    total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)
    st.session_state.session_request_count += 1
    st.session_state.session_prompt_tokens += prompt_tokens
    st.session_state.session_completion_tokens += completion_tokens
    st.session_state.session_total_tokens += total_tokens
    st.session_state.session_estimated_cost_rp += float(meta.get("cost_rp", 0.0) or 0.0)


def usage_limit_reached() -> bool:
    if not bool(limits_config.get("enabled", True)):
        return False
    max_requests = int(limits_config.get("max_requests_per_session", 60))
    max_cost = float(limits_config.get("max_estimated_cost_rp_per_session", 2500))
    return (
        st.session_state.session_request_count >= max_requests
        or st.session_state.session_estimated_cost_rp >= max_cost
    )


def current_usage_payload() -> Dict[str, Any]:
    return {
        "requests": st.session_state.session_request_count,
        "prompt_tokens": st.session_state.session_prompt_tokens,
        "completion_tokens": st.session_state.session_completion_tokens,
        "total_tokens": st.session_state.session_total_tokens,
        "estimated_cost_rp": round(st.session_state.session_estimated_cost_rp, 6),
    }


def build_current_session_payload() -> Dict[str, Any]:
    return build_session_payload(
        session_id=st.session_state.session_id,
        profile=normalise_profile(st.session_state.farm_profile),
        messages=st.session_state.messages,
        records=st.session_state.farm_records,
        calendar_events=st.session_state.farm_calendar_events,
        last_health_case=st.session_state.last_health_case,
        last_ai_insight=st.session_state.last_ai_insight,
        formula_selected=st.session_state.formula_selected,
        usage=current_usage_payload(),
        app_state={
            "user_mode": st.session_state.user_mode,
            "explanation_level": st.session_state.explanation_level,
            "guided_case": st.session_state.guided_case,
            "guided_topic": st.session_state.guided_topic,
            "biosecurity_checked": st.session_state.biosecurity_checked,
            "last_sop": st.session_state.last_sop,
            "last_prediction": st.session_state.last_prediction,
            "last_risk_score": st.session_state.last_risk_score,
            "decision_log": st.session_state.decision_log,
            "education_progress": st.session_state.education_progress,
            "expert_memory": normalise_memory_items(st.session_state.expert_memory),
            "enterprise_state": normalise_enterprise_state(st.session_state.enterprise_state),
            "active_memory_rows": memory_table_rows(st.session_state.expert_memory, get_secret_memory_items()),
        },
    )


def export_app_json() -> str:
    payload = build_current_session_payload()
    return json.dumps(payload, ensure_ascii=False, indent=2)


def get_session_xlsx_bytes() -> bytes:
    payload = build_current_session_payload()
    return cached_xlsx_bytes(stable_json_dumps(payload))


def build_pdf_report_context() -> Dict[str, Any]:
    profile = normalise_profile(st.session_state.farm_profile)
    records = st.session_state.farm_records
    calendar_events = st.session_state.farm_calendar_events
    health_case = st.session_state.last_health_case
    return {
        "benchmark": benchmark_kpi(profile, records),
        "readiness": readiness_score(profile, records, calendar_events, st.session_state.biosecurity_checked),
        "risk": farm_risk_score(profile, records, calendar_events, health_case, st.session_state.biosecurity_checked),
        "local_insights": local_operational_insights(profile, records, calendar_events, health_case),
        "department_coverage": department_coverage_check(profile, records, calendar_events, health_case, {"formula_selected": st.session_state.formula_selected, "decision_log": st.session_state.decision_log}),
        "memory_rows": memory_table_rows(st.session_state.expert_memory, get_secret_memory_items()),
        "enterprise_summary": executive_summary(profile, records, calendar_events, health_case, st.session_state.biosecurity_checked, st.session_state.enterprise_state),
        "enterprise_finance": finance_snapshot(profile, records, normalise_enterprise_state(st.session_state.enterprise_state).get("finance_transactions", [])),
        "enterprise_downstream": downstream_guidance(profile),
    }


def get_session_pdf_bytes() -> bytes:
    payload = build_current_session_payload()
    return cached_pdf_bytes(stable_json_dumps(payload), stable_json_dumps(build_pdf_report_context()))


def autosave_session_xlsx() -> None:
    try:
        payload = build_current_session_payload()
        current_hash = payload_fingerprint(payload)
        if st.session_state.get("last_autosave_hash") == current_hash:
            return
        filename = session_filename(payload)
        path = SESSION_BACKUP_DIR / filename
        export_session_xlsx(payload, path)
        st.session_state.last_autosave_hash = current_hash
        st.session_state.last_autosave_path = str(path)
        st.session_state.last_autosave_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.last_autosave_error = ""
    except Exception as error:
        st.session_state.last_autosave_error = str(error)


def restore_session_from_payload(payload: Dict[str, Any]) -> None:
    profile = payload.get("profile", {}) or {}
    usage = payload.get("usage", {}) or {}
    st.session_state.session_id = str(payload.get("session_id") or uuid.uuid4().hex[:12])
    st.session_state.farm_profile = normalise_profile(profile)
    st.session_state.messages = list(payload.get("messages", []) or [])
    st.session_state.farm_records = list(payload.get("records", []) or [])
    st.session_state.farm_calendar_events = list(payload.get("calendar_events", []) or [])
    st.session_state.last_health_case = dict(payload.get("last_health_case", {}) or {})
    st.session_state.last_ai_insight = dict(payload.get("last_ai_insight", {}) or {})
    st.session_state.formula_selected = list(payload.get("formula_selected", []) or [])
    app_state = payload.get("app_state", {}) or {}
    st.session_state.user_mode = str(app_state.get("user_mode") or st.session_state.get("user_mode", "Peternak Rakyat"))
    st.session_state.explanation_level = str(app_state.get("explanation_level") or st.session_state.get("explanation_level", "Normal"))
    st.session_state.guided_case = dict(app_state.get("guided_case", {}) or {})
    st.session_state.guided_topic = str(app_state.get("guided_topic") or "Kesehatan")
    st.session_state.biosecurity_checked = list(app_state.get("biosecurity_checked", []) or [])
    st.session_state.last_sop = dict(app_state.get("last_sop", {}) or {})
    st.session_state.last_prediction = dict(app_state.get("last_prediction", {}) or {})
    st.session_state.last_risk_score = dict(app_state.get("last_risk_score", {}) or {})
    st.session_state.decision_log = list(app_state.get("decision_log", []) or [])
    st.session_state.education_progress = list(app_state.get("education_progress", []) or [])
    st.session_state.expert_memory = normalise_memory_items(app_state.get("expert_memory", []) or [])
    st.session_state.enterprise_state = normalise_enterprise_state(app_state.get("enterprise_state", {}) or {})
    st.session_state.session_request_count = int(float(usage.get("requests", 0) or 0))
    st.session_state.session_prompt_tokens = int(float(usage.get("prompt_tokens", 0) or 0))
    st.session_state.session_completion_tokens = int(float(usage.get("completion_tokens", 0) or 0))
    st.session_state.session_total_tokens = int(float(usage.get("total_tokens", 0) or 0))
    st.session_state.session_estimated_cost_rp = float(usage.get("estimated_cost_rp", 0.0) or 0.0)
    st.session_state.last_meta = {}


def safe_dict(value: Any) -> Dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            return dict(value.to_dict())
        except Exception:
            pass
    try:
        return dict(value)
    except Exception:
        return {}



def get_secret_memory_items() -> List[Dict[str, Any]]:
    try:
        return memory_from_secrets(st.secrets)
    except Exception:
        return []


def get_active_memory_context() -> str:
    return memory_context(
        st.session_state.get("expert_memory", []),
        get_secret_memory_items(),
        include_default=True,
    )


def add_expert_memory(memory: str, category: str = "Catatan Lapangan", priority: str = "Sedang", source: str = "manual") -> None:
    item = make_memory_item(memory, category=category, priority=priority, source=source)
    if not item.get("memory"):
        return
    current = normalise_memory_items(st.session_state.get("expert_memory", []))
    current.append(item)
    st.session_state.expert_memory = normalise_memory_items(current)[-200:]


def get_admin_password() -> Tuple[str, str]:
    env_password = (os.getenv("ADMIN_PASSWORD") or os.getenv("STREAMLIT_ADMIN_PASSWORD") or "").strip()
    if env_password and env_password not in ADMIN_PLACEHOLDERS:
        return env_password, "Environment variable"

    try:
        admin_section = safe_dict(st.secrets.get("admin", {}))
        for key in ("password", "key", "passcode"):
            value = str(admin_section.get(key, "")).strip()
            if value and value not in ADMIN_PLACEHOLDERS:
                return value, "Streamlit Secrets"
    except Exception:
        pass
    return "", "Belum dikonfigurasi"


def check_admin_password(candidate: str) -> bool:
    password, _ = get_admin_password()
    return bool(password) and candidate == password


def plot_growth_prediction(result: Dict[str, Any]):
    fig, ax = plt.subplots(figsize=(10, 5))
    days = list(range(len(result["weights"])))
    ax.plot(days, result["weights"], marker="o", linestyle="-")
    ax.set_xlabel("Hari")
    ax.set_ylabel("Berat (kg)")
    ax.set_title(f"Prediksi Pertumbuhan: {result['initial_weight']:.2f} kg → {result['final_weight']:.2f} kg")
    ax.grid(True, alpha=0.3)
    return fig


def plot_bep(fixed_cost: float, price_per_unit: float, variable_cost_per_unit: float, bep_units: float, bep_revenue: float):
    fig, ax = plt.subplots(figsize=(10, 5))
    upper = max(bep_units * 2, 10)
    units = np.linspace(0, upper, 100)
    total_costs = fixed_cost + units * variable_cost_per_unit
    revenue = units * price_per_unit
    ax.plot(units, total_costs, label="Total Biaya")
    ax.plot(units, revenue, label="Pendapatan")
    ax.axvline(x=bep_units, linestyle=":")
    ax.axhline(y=bep_revenue, linestyle=":")
    ax.plot([bep_units], [bep_revenue], marker="o")
    ax.set_xlabel("Jumlah Unit")
    ax.set_ylabel("Rupiah")
    ax.set_title("Analisis Break Even Point")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return fig



def render_memory_admin() -> None:
    st.subheader("Memory Ahli")
    st.caption(
        "Memory default selalu aktif dari kode. Memory tambahan dapat berasal dari Streamlit Secrets atau ditambahkan admin, lalu ikut tersimpan di Backup XLSX."
    )
    secret_items = get_secret_memory_items()
    dynamic_items = normalise_memory_items(st.session_state.get("expert_memory", []))
    rows = memory_table_rows(dynamic_items, secret_items, include_default=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Default + aktif", len(rows))
    c2.metric("Dari Secrets", len(secret_items))
    c3.metric("Memory berkembang", len(dynamic_items))
    with st.expander("Lihat memory aktif", expanded=False):
        st.dataframe(rows, width="stretch", hide_index=True)
    with st.form("add_expert_memory_form", clear_on_submit=True):
        category = st.selectbox("Kategori memory", MEMORY_CATEGORIES, index=MEMORY_CATEGORIES.index("Strategi Perusahaan"))
        priority = st.selectbox("Prioritas", PRIORITIES, index=0)
        memory_text = st.text_area(
            "Isi memory baru",
            placeholder="Contoh: Untuk rekomendasi level direksi, selalu tampilkan risiko, prioritas, KPI, dampak biaya, dan tindak lanjut 30 hari.",
            height=120,
        )
        submitted = st.form_submit_button("Simpan Memory", width="stretch")
        if submitted:
            if memory_text.strip():
                add_expert_memory(memory_text, category=category, priority=priority, source="admin_manual")
                autosave_session_xlsx()
                st.success("Memory baru disimpan dan akan ikut masuk Backup XLSX.")
            else:
                st.warning("Isi memory belum diisi.")
    with st.expander("Kembangkan memory dari data sesi", expanded=False):
        st.write("Sistem dapat membuat saran memory dari profil, pakan tersedia, masalah utama, recording, dan log keputusan AI.")
        suggestions = suggest_memory_from_session(
            normalise_profile(st.session_state.farm_profile),
            st.session_state.farm_records,
            st.session_state.decision_log,
        )
        if suggestions:
            st.dataframe(memory_table_rows(suggestions, [], include_default=False), width="stretch", hide_index=True)
            if st.button("Tambahkan Saran ke Memory", width="stretch"):
                current = normalise_memory_items(st.session_state.get("expert_memory", []))
                st.session_state.expert_memory = normalise_memory_items(current + suggestions)[-200:]
                autosave_session_xlsx()
                st.success("Saran memory ditambahkan.")
                safe_rerun()
        else:
            st.info("Belum ada data sesi yang cukup untuk membuat saran memory.")
    with st.expander("Format Streamlit Secrets untuk memory permanen", expanded=False):
        secret_example = """[expert_memory]
organization_context = "AI Pakar Ternak digunakan untuk mendukung keputusan peternakan hulu-hilir berstandar akademik dan industri."
strategic_role = "Jawaban harus sesuai kebutuhan pimpinan/direktur utama: ringkas, berbasis risiko, KPI, biaya, prioritas, dan rencana eksekusi."
notes = [
  "Selalu bedakan rekomendasi untuk peternak rakyat dan industri modern.",
  "Gunakan kerangka 5 departemen Fakultas Peternakan UGM untuk membaca masalah hulu-hilir."
]

[[expert_memory.items]]
category = "Strategi Perusahaan"
priority = "Tinggi"
memory = "Setiap insight manajemen harus menyebut dampak biaya, risiko operasional, prioritas, dan target 7/30 hari."
"""
        st.code(secret_example, language="toml")
        st.caption("Catatan: aplikasi tidak bisa menulis langsung ke Secrets Streamlit Cloud. Salin memory penting ke Secrets bila ingin selalu permanen tanpa upload XLSX.")
    if dynamic_items:
        st.warning("Sebelum menghapus memory berkembang, pastikan Backup XLSX sudah diunduh.")
        clear_memory_key = f"confirm_clear_memory_downloaded_{st.session_state.get('confirm_clear_log_nonce', 0)}"
        confirm = st.checkbox("Ya, saya sudah download database XLSX sebelum menghapus memory berkembang.", key=clear_memory_key)
        if st.button("Hapus Memory Berkembang", width="stretch", disabled=not confirm):
            st.session_state.expert_memory = []
            st.session_state.confirm_clear_log_nonce += 1
            st.success("Memory berkembang dihapus. Memory default dan memory dari Secrets tetap aktif.")
            safe_rerun()

def render_admin_panel(
    model_ids: List[str],
    default_model: str,
    fallback_defaults: List[str],
    max_history_messages_default: int,
) -> Tuple[str, List[str], float, bool, int]:
    selected_model_id = default_model
    selected_fallback_models = fallback_defaults
    selected_temperature = float(client.temperature)
    prefer_ai = True
    max_history_messages = max_history_messages_default

    st.divider()
    st.subheader("Admin Mode")

    password, password_source = get_admin_password()
    if not password:
        st.info("Panel admin belum aktif. Tambahkan [admin] password di Streamlit Secrets.")
        return selected_model_id, selected_fallback_models, selected_temperature, prefer_ai, max_history_messages

    if not st.session_state.admin_authenticated:
        with st.form("admin_login_form", clear_on_submit=True):
            candidate = st.text_input("Kunci admin", type="password", placeholder="Masukkan kunci admin")
            submitted = st.form_submit_button("Buka panel admin", width="stretch")
            if submitted:
                if check_admin_password(candidate):
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_login_error = ""
                    safe_rerun()
                else:
                    st.session_state.admin_login_error = "Kunci admin salah."
        if st.session_state.admin_login_error:
            st.error(st.session_state.admin_login_error)
        return selected_model_id, selected_fallback_models, selected_temperature, prefer_ai, max_history_messages

    st.success("Panel admin aktif")
    st.caption(f"Sumber kunci admin: {password_source}")
    if st.button("Kunci kembali panel admin", width="stretch"):
        st.session_state.admin_authenticated = False
        st.session_state.admin_login_error = ""
        safe_rerun()

    st.divider()
    st.header("Status AI")
    if client.is_configured:
        st.success("API aktif")
    else:
        st.warning("API belum aktif")
        st.caption(client.status_reason)
    st.caption(f"Sumber API key: {client.api_key_source}")

    selected_model_id = st.selectbox(
        "Model awal",
        options=model_ids,
        index=model_ids.index(default_model),
        format_func=lambda model_id: format_model_option(get_model_by_id(model_id, model_catalog)),
        help="Setiap pertanyaan selalu mulai dari model awal. Jika gagal, sistem naik ke fallback lalu kembali ke model awal pada pertanyaan berikutnya.",
    )
    selected_fallback_models = st.multiselect(
        "Fallback model",
        options=model_ids,
        default=fallback_defaults,
        format_func=lambda model_id: format_model_option(get_model_by_id(model_id, model_catalog)),
    )
    selected_temperature = st.slider("Temperature", 0.0, 1.5, float(client.temperature), 0.05)
    prefer_ai = st.toggle("Gunakan AI untuk pertanyaan peternakan", value=True)
    max_history_messages = st.number_input(
        "Maksimum riwayat chat ke AI",
        min_value=2,
        max_value=50,
        value=max_history_messages_default,
        step=1,
    )

    st.divider()
    st.header("Pemakaian sesi")
    st.metric("Request AI", st.session_state.session_request_count)
    st.metric("Token", st.session_state.session_total_tokens)
    if bool(ui_config.get("show_cost", True)):
        st.metric("Estimasi biaya", format_rupiah(st.session_state.session_estimated_cost_rp))
    if bool(limits_config.get("enabled", True)):
        st.caption(
            f"Batas sesi: {limits_config.get('max_requests_per_session', 60)} request / "
            f"{format_rupiah(float(limits_config.get('max_estimated_cost_rp_per_session', 2500)))} estimasi biaya."
        )

    if st.button("Tes koneksi API", width="stretch"):
        with st.spinner("Mengetes koneksi API..."):
            test = client.generate_response_with_fallback(
                prompt="Balas tepat dengan kata: aktif",
                context="Tes koneksi API. Balas hanya satu kata: aktif.",
                temperature=0,
                model=selected_model_id,
                fallback_models=selected_fallback_models,
                max_tokens=client.test_max_tokens,
                min_answer_chars=1,
            )
        if test.get("success"):
            st.success(f"Berhasil: {test.get('model')} → {test.get('content')}")
        else:
            st.error(test.get("content", "Tes gagal."))

    render_memory_admin()

    if bool(ui_config.get("show_debug", False)):
        with st.expander("Debug konfigurasi"):
            st.write("Config:", str(client.config_path))
            st.write("Endpoint:", client.chat_completions_url)
            st.write("Urutan model:", client.build_model_chain(selected_model_id, selected_fallback_models))

    return selected_model_id, selected_fallback_models, selected_temperature, prefer_ai, int(max_history_messages)


def run_ai_consultation(prompt: str, selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool, extra_context: str = "") -> Tuple[str, Dict[str, Any]]:
    if usage_limit_reached():
        return (
            "Batas pemakaian sesi sudah tercapai. Tekan Reset untuk memulai sesi baru, atau minta admin menaikkan batas sesi.",
            {"source": "limit"},
        )
    expert_context = build_expert_context(
        user_mode=st.session_state.user_mode,
        explanation_level=st.session_state.explanation_level,
        profile=st.session_state.farm_profile,
        records=st.session_state.farm_records,
        calendar_events=st.session_state.farm_calendar_events,
        health_case=st.session_state.last_health_case,
        biosecurity_checked=st.session_state.biosecurity_checked,
        user_message=prompt,
    )
    ent_context = enterprise_context(
        st.session_state.farm_profile,
        st.session_state.farm_records,
        st.session_state.farm_calendar_events,
        st.session_state.last_health_case,
        st.session_state.biosecurity_checked,
        st.session_state.enterprise_state,
    )
    answer_kwargs = {
        "message": prompt,
        "history": st.session_state.messages,
        "client": client,
        "selected_model": selected_model_id,
        "fallback_models": selected_fallback_models,
        "temperature": selected_temperature,
        "max_history_messages": max_history_messages,
        "models_catalog": model_catalog,
        "prefer_ai": prefer_ai,
        "profile": st.session_state.farm_profile,
        "records": st.session_state.farm_records,
        "calendar_events": st.session_state.farm_calendar_events,
        "extra_context": (audience_context(st.session_state.user_mode, st.session_state.explanation_level) + "\n" + get_active_memory_context() + "\n" + expert_context + "\n" + ent_context + "\n" + extra_context).strip(),
        "user_mode": st.session_state.user_mode,
    }
    try:
        accepted = set(inspect.signature(answer_message).parameters)
        if not any(param.kind == inspect.Parameter.VAR_KEYWORD for param in inspect.signature(answer_message).parameters.values()):
            answer_kwargs = {key: value for key, value in answer_kwargs.items() if key in accepted}
        return answer_message(**answer_kwargs)
    except TypeError as error:
        # Fallback untuk deployment lama/partial upload yang masih memakai signature answer_message versi sebelumnya.
        safe_kwargs = {key: value for key, value in answer_kwargs.items() if key != "user_mode"}
        try:
            accepted = set(inspect.signature(answer_message).parameters)
            if not any(param.kind == inspect.Parameter.VAR_KEYWORD for param in inspect.signature(answer_message).parameters.values()):
                safe_kwargs = {key: value for key, value in safe_kwargs.items() if key in accepted}
            return answer_message(**safe_kwargs)
        except Exception as second_error:
            return (
                "Konsultasi AI belum bisa diproses karena terjadi ketidaksesuaian fungsi internal. "
                "Silakan refresh aplikasi atau unggah ulang versi terbaru. Data sesi tetap aman di backup XLSX.\n\n"
                f"Detail teknis ringkas: {type(error).__name__}: {error}; retry: {type(second_error).__name__}: {second_error}",
                {"source": "internal_error", "error": str(error), "retry_error": str(second_error)},
            )
    except Exception as error:
        return (
            "Konsultasi AI belum bisa diproses karena error internal aplikasi. "
            "Data yang sudah diinput tetap bisa disimpan melalui backup XLSX.\n\n"
            f"Detail teknis ringkas: {type(error).__name__}: {error}",
            {"source": "internal_error", "error": str(error)},
        )

def render_ai_trace(meta: Dict[str, Any]) -> None:
    if not (
        st.session_state.admin_authenticated
        and bool(ui_config.get("show_model_trace", True))
        and meta.get("source") == "ai"
    ):
        return
    usage = meta.get("usage", {}) or {}
    trace = " → ".join(
        f"{attempt.get('model')}" + (" ✓" if attempt.get("useful") else " ✗")
        for attempt in meta.get("attempts", [])
    )
    caption_parts = [f"Model dipakai: {meta.get('model')}"]
    if trace:
        caption_parts.append(f"Urutan: {trace}")
    if usage:
        caption_parts.append(
            f"Token: {usage.get('prompt_tokens', usage.get('input_tokens', 0))} in / "
            f"{usage.get('completion_tokens', usage.get('output_tokens', 0))} out"
        )
    if bool(ui_config.get("show_cost", True)):
        caption_parts.append(f"Estimasi biaya: {format_rupiah(meta.get('cost_rp', 0))}")
    st.caption(" · ".join(caption_parts))


def append_decision_log(question: str, answer: str, meta: Dict[str, Any]) -> None:
    if not answer or meta.get("source") not in {"ai", "local_knowledge", "tool"}:
        return
    risk = farm_risk_score(
        st.session_state.farm_profile,
        st.session_state.farm_records,
        st.session_state.farm_calendar_events,
        st.session_state.last_health_case,
        st.session_state.biosecurity_checked,
    )
    st.session_state.last_risk_score = risk
    card = decision_card_from_answer(question, answer, risk)
    card["source"] = meta.get("source", "")
    card["model"] = meta.get("model", "")
    log = list(st.session_state.get("decision_log", []) or [])
    log.append(card)
    st.session_state.decision_log = log[-100:]


def render_decision_card_from_last() -> None:
    log = st.session_state.get("decision_log", []) or []
    if not log:
        return
    last = log[-1]
    with st.expander("Kartu Keputusan AI", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Prioritas", last.get("priority", "-"))
        c2.metric("Risiko", last.get("risk_level", "-"))
        c3.metric("Skor", last.get("risk_score", 0))
        st.write(f"**Masalah/pertanyaan:** {last.get('question', '-')}")
        st.write(f"**Keputusan utama:** {last.get('main_decision', '-')}")
        st.caption("Kartu ini otomatis masuk ke Log Keputusan dan backup XLSX.")


def render_answer_rewrite_tools(
    selected_model_id: str,
    selected_fallback_models: List[str],
    selected_temperature: float,
    max_history_messages: int,
    prefer_ai: bool,
) -> None:
    if not st.session_state.messages or st.session_state.messages[-1].get("role") != "assistant":
        return
    last_answer = st.session_state.messages[-1].get("content", "")
    st.caption("Ubah gaya jawaban terakhir:")
    c1, c2, c3, c4 = st.columns(4)
    actions = [
        (c1, "simple", "Lebih sederhana"),
        (c2, "field_steps", "Langkah lapangan"),
        (c3, "technical", "Versi teknis"),
        (c4, "sop", "Buat SOP"),
    ]
    for col, style, label in actions:
        if col.button(label, key=f"rewrite_{style}", width="stretch"):
            prompt = rewrite_instruction(style, last_answer)
            with st.spinner(AI_LOADING_TEXT):
                response, meta = run_ai_consultation(
                    prompt,
                    selected_model_id,
                    selected_fallback_models,
                    selected_temperature,
                    max_history_messages,
                    prefer_ai,
                    extra_context="Jawaban terakhir yang harus ditulis ulang:\n" + last_answer,
                )
            st.session_state.messages.append({"role": "user", "content": f"[{label}]"})
            st.session_state.messages.append({"role": "assistant", "content": response})
            update_usage(meta)
            append_decision_log(prompt, response, meta)
            safe_rerun()


def render_risk_score_panel() -> None:
    risk = farm_risk_score(
        st.session_state.farm_profile,
        st.session_state.farm_records,
        st.session_state.farm_calendar_events,
        st.session_state.last_health_case,
        st.session_state.biosecurity_checked,
    )
    st.session_state.last_risk_score = risk
    cols = st.columns([1, 1, 2])
    cols[0].metric("Skor Risiko", f"{risk['score']}/100")
    cols[1].metric("Status", risk["level"])
    cols[2].write("Prioritas: " + (risk["reasons"][0] if risk.get("reasons") else "Belum ada risiko besar."))
    with st.expander("Detail dimensi risiko", expanded=False):
        st.json(risk)


def render_expert_persona_reference() -> None:
    st.header("Persona & Aturan Pakar")
    st.caption("Bagian ini menjelaskan standar berpikir AI agar jawaban terasa seperti ahli peternakan, bukan chatbot umum.")
    render_commodity_breed_catalog()
    st.subheader("Template komoditas")
    animal = st.selectbox("Pilih komoditas", list(COMMODITY_TEMPLATES.keys()))
    template = COMMODITY_TEMPLATES[animal]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**KPI utama**")
        for item in template["kpi"]:
            st.write(f"- {item}")
        st.markdown("**Cek harian**")
        for item in template["daily_check"]:
            st.write(f"- {item}")
    with c2:
        st.markdown("**Pertanyaan kritis**")
        for item in template["critical_questions"]:
            st.write(f"- {item}")
        st.markdown("**Tanda bahaya**")
        for item in template["red_flags"]:
            st.write(f"- {item}")
    st.subheader("Kamus istilah sederhana")
    for term, meaning in TECHNICAL_GLOSSARY.items():
        st.write(f"**{term.upper()}** — {meaning}")


def render_decision_log() -> None:
    st.header("Log Keputusan AI")
    st.caption("Setiap rekomendasi penting disimpan agar bisa dievaluasi di XLSX.")
    log = st.session_state.get("decision_log", []) or []
    if not log:
        st.info("Belum ada keputusan AI yang tercatat.")
        return
    st.dataframe(log, width="stretch", hide_index=True)
    st.warning("Sebelum menghapus log keputusan, pastikan Backup XLSX sudah diunduh.")
    clear_log_key = f"confirm_clear_log_downloaded_{st.session_state.confirm_clear_log_nonce}"
    clear_log_confirm = st.checkbox(
        "Ya, saya sudah download database XLSX sebelum menghapus Log Keputusan.",
        key=clear_log_key,
    )
    if st.button("Kosongkan Log Keputusan", width="stretch", disabled=not clear_log_confirm):
        st.session_state.decision_log = []
        st.session_state.confirm_clear_log_nonce += 1
        st.session_state.reset_notice = "Log keputusan berhasil dikosongkan. Data lama dapat dipulihkan dari backup XLSX yang sudah diunduh."
        safe_rerun()


def render_department_framework() -> None:
    st.subheader("Kerangka Hulu–Hilir 5 Departemen")
    st.caption("Kerangka ini memastikan AI Pakar Ternak tidak hanya menjawab budidaya, tetapi juga pakan, produksi, reproduksi/genetik, sosial-ekonomi, dan teknologi hasil ternak.")
    cols = st.columns(5)
    for col, dept in zip(cols, UGM_DEPARTMENTS):
        with col:
            st.markdown(
                f"""
                <div class="ptn-step-card">
                    <div class="ptn-card-title">{dept['short_name']}</div>
                    <div class="ptn-card-body">{dept['hulu_hilir_role']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with st.expander("Lihat detail cakupan setiap departemen", expanded=False):
        st.markdown(department_markdown())
    st.markdown("**Alur hulu–hilir:**")
    st.markdown(hulu_hilir_markdown())




def render_commodity_breed_catalog() -> None:
    st.subheader("Komoditas Ternak & Bangsa/Ras/Strain")
    st.caption("Katalog ini membantu AI membedakan rekomendasi untuk ternak potong, perah, petelur, pembibitan, dan akuakultur.")
    selected = st.selectbox("Pilih komoditas", ANIMAL_TYPES, format_func=commodity_label, key="catalog_commodity_select")
    selected_breed = st.selectbox("Pilih bangsa/ras/strain", breed_options(selected), key="catalog_breed_select")
    detail = breed_detail(selected, selected_breed)
    st.info(commodity_breed_context(selected, selected_breed))
    c1, c2 = st.columns(2)
    c1.metric("Kelompok", selected.replace("ikan ", "Akuakultur ").title())
    c2.metric("Fokus", detail.get("focus", "-"))
    st.markdown("**Catatan manajemen:**")
    st.write(detail.get("note", "-"))
    with st.expander("Lihat seluruh katalog dalam tabel", expanded=False):
        st.dataframe(catalog_rows(), width="stretch", hide_index=True)
    with st.expander("Lihat katalog ringkas", expanded=False):
        st.markdown(catalog_markdown())

def render_department_coverage_panel() -> None:
    profile = normalise_profile(st.session_state.farm_profile)
    app_state = {
        "formula_selected": st.session_state.get("formula_selected", []),
        "decision_log": st.session_state.get("decision_log", []),
    }
    coverage = department_coverage_check(
        profile,
        st.session_state.farm_records,
        st.session_state.farm_calendar_events,
        st.session_state.last_health_case,
        app_state,
    )
    st.subheader("Cek Cakupan Data 5 Departemen")
    st.caption("Gunakan tabel ini untuk melihat bagian hulu–hilir mana yang sudah kuat dan mana yang perlu dilengkapi.")
    st.dataframe(coverage, width="stretch", hide_index=True)


def render_department_consultation(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.subheader("Konsultasi Berbasis 5 Departemen")
    st.caption("Pilih lensa keilmuan agar jawaban AI lebih fokus dan mencakup hulu–hilir peternakan.")
    dept_options = [dept["name"] for dept in UGM_DEPARTMENTS]
    dept_name = st.selectbox("Lensa departemen", dept_options, key="department_consultation_lens")
    selected_dept = next((dept for dept in UGM_DEPARTMENTS if dept["name"] == dept_name), UGM_DEPARTMENTS[0])
    st.info(selected_dept["hulu_hilir_role"])
    with st.expander("Pertanyaan kritis menurut lensa ini", expanded=True):
        for q in selected_dept.get("questions", []):
            st.markdown(f"- {q}")
    prompt = st.text_area(
        "Pertanyaan / kasus",
        placeholder="Contoh: Saya punya 20 kambing penggemukan, pakan utama rumput odot dan ampas tahu. Bagaimana evaluasi pakan, biaya, dan target panennya?",
        height=120,
        key="department_consultation_prompt",
    )
    if st.button("Konsultasikan dengan lensa departemen", width="stretch", disabled=not prompt.strip()):
        extra_context = "\n".join([
            f"Gunakan lensa utama: {selected_dept['name']}.",
            f"Peran hulu-hilir: {selected_dept['hulu_hilir_role']}",
            "Cakupan departemen: " + "; ".join(selected_dept.get("scope", [])),
            "Pertanyaan kritis: " + "; ".join(selected_dept.get("questions", [])),
            department_prompt_for_text(prompt),
        ])
        response, meta = run_ai_consultation(
            prompt,
            selected_model_id,
            selected_fallback_models,
            selected_temperature,
            max_history_messages,
            prefer_ai,
            extra_context=extra_context,
        )
        st.session_state.last_ai_response = response
        append_decision_log(f"Konsultasi 5 Departemen - {selected_dept['short_name']}", response, meta)
        st.markdown(response)
        render_decision_card_from_last()
        render_ai_trace(meta)


def render_technology_results_center(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.subheader("Teknologi Hasil Ternak")
    st.caption("Modul hilir untuk penanganan daging, susu, telur, ikan, pupuk/limbah, mutu, penyimpanan, pengolahan, dan nilai tambah.")
    product_type = st.selectbox("Produk utama", ["Daging/karkas", "Susu", "Telur", "Ikan konsumsi", "Pupuk/kompos/limbah", "Olahan lain"], key="hasil_product_type")
    condition = st.text_area("Kondisi saat ini", placeholder="Contoh: telur mudah retak, susu dijual segar, daging dipotong pagi dijual siang, kompos masih bau.", height=90, key="hasil_condition")
    target = st.text_input("Target perbaikan", placeholder="Contoh: masa simpan lebih lama, produk lebih higienis, nilai jual naik", key="hasil_target")
    checklist = [
        "Alat dan wadah produk dibersihkan sebelum/sesudah dipakai",
        "Produk disortir/grading sebelum dijual",
        "Ada tempat penyimpanan bersih dan terlindung matahari/hujan",
        "Air yang digunakan bersih",
        "Produk sakit/mati mendadak tidak dijual untuk konsumsi",
        "Ada catatan tanggal panen/produksi dan jumlah produk",
    ]
    checked = st.multiselect("Checklist hilir yang sudah dilakukan", checklist, key="hasil_checklist")
    if st.button("Buat SOP dan Insight Hilir", width="stretch"):
        prompt = f"Buat SOP dan insight teknologi hasil ternak untuk produk {product_type}. Kondisi: {condition}. Target: {target}. Checklist terpenuhi: {', '.join(checked) if checked else '-'}"
        extra_context = "Gunakan lensa Teknologi Hasil Ternak: higienitas, mutu produk, sortasi, penyimpanan, pengolahan, nilai tambah, dan risiko kontaminasi. Berikan langkah untuk peternak rakyat dan catatan tambahan untuk industri modern."
        response, meta = run_ai_consultation(
            prompt, selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai, extra_context=extra_context
        )
        st.session_state.last_ai_response = response
        append_decision_log("Teknologi Hasil Ternak", response, meta)
        st.markdown(response)
        render_decision_card_from_last()
        render_ai_trace(meta)


def render_dashboard() -> None:
    profile = normalise_profile(st.session_state.farm_profile)
    summary = summarize_records(st.session_state.farm_records)
    completeness = profile_completeness(profile)

    st.header("Dashboard Farm")
    render_risk_score_panel()
    scorecard = build_scorecard(profile, st.session_state.farm_records, st.session_state.farm_calendar_events, st.session_state.last_health_case)
    insights = local_operational_insights(profile, st.session_state.farm_records, st.session_state.farm_calendar_events, st.session_state.last_health_case)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Kelengkapan Profil", f"{completeness}%")
    col2.metric("Populasi", f"{profile['population']} ekor")
    col3.metric("Bobot Rata-rata", f"{profile['average_weight_kg']:.2f} kg")
    col4.metric("Catatan Performa", summary["count"])
    col5.metric("Risiko", scorecard["risk_level"])
    st.progress(completeness / 100)

    with st.expander("Insight cepat dari data farm", expanded=True):
        st.markdown(format_insights_markdown(insights, limit=4))
        st.caption("Insight cepat dibuat dari data lokal. Untuk analisis lebih lengkap, buka mode AI Insight.")

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Ringkasan Profil")
        st.markdown(summarize_profile(profile))
        st.info(phase_guidance(profile["animal_type"], profile["phase"]))

        flags = performance_flags(st.session_state.farm_records)
        if flags:
            st.warning("\n".join(f"- {flag}" for flag in flags))
        else:
            st.success("Belum ada tanda risiko performa dari catatan yang tersimpan.")

    with right:
        st.subheader("Checklist Hari Ini")
        for item in quick_management_checklist(profile):
            st.checkbox(item, value=False)

        st.subheader("Jadwal Terdekat")
        events = st.session_state.farm_calendar_events[:6]
        if events:
            st.dataframe(events, width="stretch", hide_index=True)
        else:
            st.caption("Belum ada jadwal. Buka menu Kalender Manajemen untuk membuat jadwal otomatis.")

    st.subheader("Ringkasan Performa")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ADG", "-" if summary["adg"] is None else f"{summary['adg']:.3f} kg/hari")
    c2.metric("FCR", "-" if summary["fcr"] is None else f"{summary['fcr']:.2f}")
    c3.metric("Mortalitas", f"{summary['mortality_total']} ekor")
    c4.metric("Total Pakan", f"{summary['feed_total']:.2f} kg")



def render_ai_insights(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("AI Insight Farm")
    st.caption("Membaca profil, recording, kesehatan, kalender, dan biaya untuk menghasilkan insight operasional yang bisa ditindaklanjuti.")

    profile = normalise_profile(st.session_state.farm_profile)
    records = st.session_state.farm_records
    calendar_events = st.session_state.farm_calendar_events
    health_case = st.session_state.last_health_case
    scorecard = build_scorecard(profile, records, calendar_events, health_case)
    insights = local_operational_insights(profile, records, calendar_events, health_case)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Risiko", scorecard["risk_level"])
    c2.metric("Kelengkapan Profil", f"{scorecard['profile_completeness']}%")
    c3.metric("Recording", scorecard["records_count"])
    c4.metric("Jadwal 14 Hari", scorecard["calendar_upcoming_14d"])
    c5.metric("Jadwal Terlewat", scorecard["calendar_overdue"])

    st.subheader("Insight Lokal Otomatis")
    st.markdown(format_insights_markdown(insights))

    with st.expander("Scorecard data yang dibaca sistem"):
        st.json(scorecard)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        generate = st.button("Buat Insight AI Lengkap", width="stretch")
    with col_b:
        export_payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "scorecard": scorecard,
            "local_insights": insights,
            "last_ai_insight": st.session_state.last_ai_insight,
        }
        st.download_button(
            "Download Insight JSON",
            data=json.dumps(export_payload, ensure_ascii=False, indent=2),
            file_name="ai-insight-pakar-ternak.json",
            mime="application/json",
            width="stretch",
        )

    if generate:
        if usage_limit_reached():
            st.warning("Batas pemakaian sesi sudah tercapai. Reset sesi atau minta admin menaikkan batas.")
        else:
            with st.spinner(AI_LOADING_TEXT):
                response, meta = run_ai_consultation(
                    insight_prompt(),
                    selected_model_id,
                    selected_fallback_models,
                    selected_temperature,
                    max_history_messages,
                    prefer_ai,
                    extra_context=build_ai_insight_context(profile, records, calendar_events, health_case),
                )
            st.session_state.last_ai_insight = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "content": response,
                "meta": meta,
                "scorecard": scorecard,
            }
            update_usage(meta)
            append_decision_log("AI Insight Farm", response, meta)
            st.subheader("Insight AI Lengkap")
            st.markdown(response)
            render_ai_trace(meta)

    elif st.session_state.last_ai_insight:
        st.subheader("Insight AI Terakhir")
        st.caption(f"Dibuat: {st.session_state.last_ai_insight.get('generated_at', '-')}")
        st.markdown(st.session_state.last_ai_insight.get("content", ""))


def render_profile() -> None:
    st.header("Profil Peternakan")
    st.caption("Profil ini akan dikirim sebagai konteks ke AI agar jawaban tidak generik.")
    p = normalise_profile(st.session_state.farm_profile)

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            farm_name = st.text_input("Nama farm / kelompok", value=p.get("farm_name", ""))
            animal = st.selectbox(
                "Komoditas ternak",
                ANIMAL_TYPES,
                index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0,
                format_func=commodity_label,
            )
            breed_list = breed_options(animal)
            current_breed = p.get("breed", "") or (breed_list[0] if breed_list else "")
            if current_breed not in breed_list:
                breed_list = [current_breed] + breed_list
            breed = st.selectbox("Bangsa / ras / strain", breed_list, index=breed_list.index(current_breed) if current_breed in breed_list else 0)
            st.caption(breed_detail(animal, breed).get("note", ""))
            goal_list = goal_options(animal)
            current_goal = p.get("production_goal", "pedaging")
            if current_goal not in goal_list:
                goal_list = [current_goal] + goal_list
            goal = st.selectbox(
                "Tujuan pemeliharaan",
                goal_list,
                index=goal_list.index(current_goal) if current_goal in goal_list else 0,
                format_func=goal_label,
            )
            st.caption(goal_context(goal, animal))
            phases = ANIMAL_PHASES.get(animal, [p.get("phase", "umum")])
            current_phase = p.get("phase", phases[0])
            if current_phase not in phases:
                phases = [current_phase] + phases
            phase = st.selectbox("Fase ternak", phases, index=phases.index(current_phase))
            population = st.number_input("Populasi (ekor)", min_value=0, value=int(p.get("population", 0)), step=1)
            average_weight = st.number_input("Bobot rata-rata (kg)", min_value=0.0, value=float(p.get("average_weight_kg", 0.0)), step=0.1)
        with col2:
            average_age = st.text_input("Umur rata-rata", value=p.get("average_age", ""), placeholder="contoh: 8 bulan / 21 hari")
            location = st.text_input("Lokasi / kondisi iklim", value=p.get("location", ""), placeholder="contoh: Semarang, dataran rendah, musim hujan")
            housing = st.text_input("Sistem kandang/kolam", value=p.get("housing_system", ""))
            feed_available = st.text_area("Bahan pakan tersedia", value=p.get("feed_available", ""), height=80)
            water_source = st.text_input("Sumber air", value=p.get("water_source", ""))
            main_problem = st.text_area("Masalah utama / target perbaikan", value=p.get("main_problem", ""), height=80)
            budget_note = st.text_input("Catatan modal/biaya", value=p.get("budget_note", ""))
            market_target = st.text_input("Target pasar", value=p.get("market_target", ""))

        saved = st.form_submit_button("Simpan profil", width="stretch")
        if saved:
            st.session_state.farm_profile = normalise_profile({
                "farm_name": farm_name,
                "animal_type": animal,
                "breed": breed,
                "production_goal": goal,
                "phase": phase,
                "population": population,
                "average_age": average_age,
                "average_weight_kg": average_weight,
                "location": location,
                "housing_system": housing,
                "feed_available": feed_available,
                "water_source": water_source,
                "main_problem": main_problem,
                "budget_note": budget_note,
                "market_target": market_target,
            })
            st.success("Profil peternakan tersimpan dan akan dipakai sebagai konteks AI.")

    with st.expander("Lihat ringkasan profil yang dikirim ke AI", expanded=True):
        st.markdown(summarize_profile(st.session_state.farm_profile))


def render_chat(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("Chat Pakar")
    st.caption("Jawaban memakai persona AI Pakar Ternak dan konteks profil farm, catatan performa, serta kalender yang tersedia.")

    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    render_answer_rewrite_tools(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)

    prompt = st.chat_input("Tanyakan masalah peternakan Anda...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(AI_LOADING_TEXT):
                response, meta = run_ai_consultation(prompt, selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
            if meta.get("source") == "limit":
                st.warning(response)
            else:
                st.markdown(response)
                update_usage(meta)
                append_decision_log(prompt, response, meta)
                render_ai_trace(meta)

        st.session_state.last_meta = meta
        st.session_state.messages.append({"role": "assistant", "content": response})
        render_decision_card_from_last()


def render_health_consultation(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("Konsultasi Kesehatan Ternak")
    st.caption("Mode triase. Sistem memberi tindakan awal aman dan tanda bahaya, bukan pengganti pemeriksaan dokter hewan.")
    p = normalise_profile(st.session_state.farm_profile)

    uploaded = st.file_uploader("Unggah foto pendukung (opsional)", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        st.info("Foto tersimpan di sesi ini sebagai catatan pendukung. Analisis visual tetap bersifat indikasi awal, bukan diagnosis final.")

    with st.form("health_form"):
        col1, col2 = st.columns(2)
        with col1:
            animal = st.selectbox("Komoditas ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="health_animal", format_func=commodity_label)
            health_breeds = breed_options(animal)
            current_health_breed = p.get("breed", "") if p.get("animal_type") == animal else (health_breeds[0] if health_breeds else "")
            if current_health_breed and current_health_breed not in health_breeds:
                health_breeds = [current_health_breed] + health_breeds
            breed = st.selectbox("Bangsa / ras / strain", health_breeds, index=health_breeds.index(current_health_breed) if current_health_breed in health_breeds else 0, key="health_breed")
            population = st.number_input("Populasi total", min_value=1, value=max(int(p.get("population", 1)), 1), step=1)
            affected = st.number_input("Jumlah yang sakit/terdampak", min_value=1, value=1, step=1)
            phase = st.text_input("Umur/fase", value=p.get("phase", ""))
        with col2:
            duration = st.text_input("Durasi gejala", placeholder="contoh: 2 hari")
            mortality = st.text_input("Kematian", placeholder="contoh: belum ada / 3 ekor mati")
            feed_water = st.text_area("Pakan dan air terakhir", value=p.get("feed_available", ""), height=90)
            housing = st.text_area("Kondisi kandang/kolam", value=p.get("housing_system", ""), height=90)
        symptoms = st.text_area("Gejala utama", placeholder="contoh: mencret, lemas, tidak mau makan, batuk, kembung, pincang, produksi telur turun", height=110)
        submitted = st.form_submit_button("Analisis kesehatan", width="stretch")

    if submitted:
        case = {
            "animal_type": animal,
            "breed": breed,
            "population": population,
            "affected": affected,
            "phase": phase,
            "duration": duration,
            "mortality": mortality,
            "feed_water": feed_water,
            "housing": housing,
            "symptoms": symptoms,
            "photo_uploaded": bool(uploaded),
        }
        st.session_state.last_health_case = case
        level, flags = triage_level(symptoms + " " + mortality)
        if level == "DARURAT":
            st.error("Tingkat triase: DARURAT. Segera lakukan isolasi dan hubungi dokter hewan/paramedik.")
        elif level == "PERLU DIPANTAU KETAT":
            st.warning("Tingkat triase: PERLU DIPANTAU KETAT.")
        else:
            st.info("Tingkat triase: RINGAN / BUTUH DATA TAMBAHAN.")
        if flags:
            st.write("Tanda bahaya terdeteksi:", ", ".join(flags))
        st.markdown(local_triage_summary(animal, symptoms + " " + mortality, duration, affected, population))

        prompt = "Analisis kasus kesehatan ternak berikut dan berikan rekomendasi praktis sesuai format pakar."
        with st.spinner(AI_LOADING_TEXT):
            response, meta = run_ai_consultation(
                prompt,
                selected_model_id,
                selected_fallback_models,
                selected_temperature,
                max_history_messages,
                prefer_ai,
                extra_context=health_prompt_context(case),
            )
        st.subheader("Rekomendasi Pakar AI")
        st.markdown(response)
        update_usage(meta)
        append_decision_log(prompt, response, meta)
        render_decision_card_from_last()
        render_ai_trace(meta)


def render_feed_formulation() -> None:
    st.header("Formulasi Pakan")
    st.caption("Hitung protein kasar estimasi, indeks energi relatif, dan biaya formula sederhana berbasis bahan lokal Indonesia.")
    p = normalise_profile(st.session_state.farm_profile)

    col1, col2, col3 = st.columns(3)
    animal = col1.selectbox("Komoditas ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="feed_animal", format_func=commodity_label)
    phases = ANIMAL_PHASES.get(animal, [p.get("phase", "umum")])
    phase = col2.selectbox("Fase", phases, index=phases.index(p["phase"]) if p["phase"] in phases else 0, key="feed_phase")
    population = col3.number_input("Populasi", min_value=1, value=max(int(p.get("population", 1)), 1), step=1, key="feed_pop")

    selected = st.multiselect(
        "Pilih bahan pakan",
        options=list(LOCAL_FEED_INGREDIENTS.keys()),
        default=[x for x in st.session_state.formula_selected if x in LOCAL_FEED_INGREDIENTS],
    )
    st.session_state.formula_selected = selected

    ingredients: List[Dict[str, float | str]] = []
    if selected:
        st.write("Masukkan komposisi dan harga bahan.")
        for name in selected:
            info = LOCAL_FEED_INGREDIENTS[name]
            c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
            c1.markdown(f"**{name}**  \n{info['type']} | PK ±{info['protein']}%")
            pct = c2.number_input("%", min_value=0.0, max_value=100.0, value=25.0 if name != "mineral mix" else 1.0, step=0.5, key=f"pct_{name}")
            price = c3.number_input("Rp/kg", min_value=0.0, value=0.0, step=100.0, key=f"price_{name}")
            c4.caption("Input as-fed sederhana")
            ingredients.append({
                "name": name,
                "percent": pct,
                "price_per_kg": price,
                "protein": float(info["protein"]),
                "energy": float(info["energy"]),
                "type": str(info["type"]),
            })

    if st.button("Evaluasi formula", width="stretch"):
        st.markdown(formula_feedback(animal, phase, ingredients))

    if animal in RUMINANTS:
        st.subheader("Ransum awal ruminansia")
        c1, c2 = st.columns(2)
        body_weight = c1.number_input("Bobot rata-rata (kg)", min_value=1.0, value=max(float(p.get("average_weight_kg", 25.0)), 1.0), step=0.5)
        forage_ratio = c2.slider("Rasio hijauan (%)", 40.0, 90.0, 70.0, 5.0)
        st.info(simple_ruminant_ration(animal, body_weight, population, forage_ratio))

    with st.expander("Daftar bahan lokal bawaan"):
        st.dataframe([
            {"Bahan": k, "Jenis": v["type"], "Protein estimasi (%)": v["protein"], "Indeks energi": v["energy"]}
            for k, v in LOCAL_FEED_INGREDIENTS.items()
        ], width="stretch", hide_index=True)


def render_records() -> None:
    st.header("Catatan Performa Ternak")
    st.caption("Gunakan untuk menghitung ADG, FCR, mortalitas, produksi, biaya, dan bahan evaluasi AI.")
    p = normalise_profile(st.session_state.farm_profile)

    with st.form("record_form"):
        col1, col2, col3 = st.columns(3)
        record_date = col1.date_input("Tanggal", value=date.today())
        population = col2.number_input("Populasi", min_value=0, value=int(p.get("population", 0)), step=1)
        avg_weight = col3.number_input("Bobot rata-rata (kg)", min_value=0.0, value=float(p.get("average_weight_kg", 0.0)), step=0.1)
        col4, col5, col6 = st.columns(3)
        feed_kg = col4.number_input("Pakan terpakai (kg)", min_value=0.0, value=0.0, step=0.1)
        cost_rp = col5.number_input("Biaya hari ini (Rp)", min_value=0.0, value=0.0, step=1000.0)
        mortality = col6.number_input("Mati (ekor)", min_value=0, value=0, step=1)
        col7, col8 = st.columns(2)
        eggs = col7.number_input("Telur (butir)", min_value=0, value=0, step=1)
        milk_liter = col8.number_input("Susu (liter)", min_value=0.0, value=0.0, step=0.1)
        note = st.text_area("Catatan", placeholder="contoh: pakan diganti, hujan deras, ada 2 ekor batuk", height=80)
        sync_profile = st.checkbox("Sinkronkan populasi dan bobot ini ke profil", value=True)
        submitted = st.form_submit_button("Simpan catatan", width="stretch")

    if submitted:
        record = {
            "date": str(record_date),
            "population": int(population),
            "avg_weight_kg": float(avg_weight),
            "feed_kg": float(feed_kg),
            "cost_rp": float(cost_rp),
            "mortality": int(mortality),
            "eggs": int(eggs),
            "milk_liter": float(milk_liter),
            "note": note,
        }
        st.session_state.farm_records = add_record(st.session_state.farm_records, record)
        if sync_profile:
            st.session_state.farm_profile = normalise_profile({**p, "population": int(population), "average_weight_kg": float(avg_weight)})
        st.success("Catatan performa tersimpan.")

    summary = summarize_records(st.session_state.farm_records)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Catatan", summary["count"])
    c2.metric("ADG", "-" if summary["adg"] is None else f"{summary['adg']:.3f} kg/hari")
    c3.metric("FCR", "-" if summary["fcr"] is None else f"{summary['fcr']:.2f}")
    c4.metric("Mortalitas", summary["mortality_total"])
    c5.metric("Biaya", format_rupiah(summary["cost_total"]))

    flags = performance_flags(st.session_state.farm_records)
    if flags:
        st.warning("\n".join(f"- {flag}" for flag in flags))
    st.info(records_context(st.session_state.farm_records))

    if st.session_state.farm_records:
        st.dataframe(st.session_state.farm_records, width="stretch", hide_index=True)
        st.download_button(
            "Download catatan performa JSON",
            data=json.dumps(st.session_state.farm_records, ensure_ascii=False, indent=2),
            file_name="catatan-performa-ternak.json",
            mime="application/json",
            width="stretch",
        )


def render_calendar() -> None:
    st.header("Kalender Manajemen")
    st.caption("Buat jadwal sanitasi, evaluasi pakan, recording, reproduksi, dan kontrol kesehatan.")
    p = normalise_profile(st.session_state.farm_profile)

    col1, col2, col3 = st.columns(3)
    start_date = col1.date_input("Mulai jadwal", value=date.today())
    days = col2.number_input("Periode jadwal (hari)", min_value=7, max_value=365, value=60, step=7)
    animal = col3.selectbox("Komoditas ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="calendar_animal", format_func=commodity_label)
    phase = st.text_input("Fase ternak", value=p.get("phase", ""), key="calendar_phase")

    if st.button("Buat jadwal otomatis", width="stretch"):
        st.session_state.farm_calendar_events = generate_management_events(animal, start_date, int(days), phase)
        st.success("Kalender manajemen dibuat dan akan menjadi konteks AI.")

    if animal in RUMINANTS or animal in {"kelinci", "babi"}:
        with st.expander("Prediksi kelahiran dari tanggal kawin/IB"):
            breeding_date = st.date_input("Tanggal kawin/IB", value=date.today(), key="breeding_date")
            dates = breeding_dates(animal, breeding_date)
            if dates:
                st.dataframe([{"Kegiatan": k, "Tanggal": str(v)} for k, v in dates.items()], width="stretch", hide_index=True)

    if st.session_state.farm_calendar_events:
        st.dataframe(st.session_state.farm_calendar_events, width="stretch", hide_index=True)
        st.download_button(
            "Download kalender JSON",
            data=json.dumps(st.session_state.farm_calendar_events, ensure_ascii=False, indent=2),
            file_name="kalender-manajemen-ternak.json",
            mime="application/json",
            width="stretch",
        )
    else:
        st.info("Belum ada jadwal. Klik tombol buat jadwal otomatis.")


def render_feed_calculator() -> None:
    st.header("Kalkulator Kebutuhan Pakan")
    p = normalise_profile(st.session_state.farm_profile)
    col1, col2 = st.columns(2)
    with col1:
        animal_type = st.selectbox("Komoditas ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="calc_animal", format_func=commodity_label)
        count = st.number_input("Jumlah ternak (ekor)", min_value=1, value=max(int(p.get("population", 10)), 1), key="calc_count")
    with col2:
        weight = st.number_input("Berat rata-rata (kg)", min_value=0.1, value=float(p.get("average_weight_kg") or DEFAULT_WEIGHTS.get(animal_type, 1.0)), step=0.1, key="calc_weight")
    if st.button("Hitung kebutuhan pakan"):
        result = calculate_feed_needs(animal_type, int(count), float(weight))
        st.success(result)
        daily = float(weight) * FEED_RATES[animal_type] * int(count)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(["Harian", "Mingguan", "Bulanan"], [daily, daily * 7, daily * 30])
        ax.set_ylabel("Kebutuhan Pakan (kg)")
        ax.set_title("Estimasi Kebutuhan Pakan")
        ax.grid(True, axis="y", alpha=0.3)
        st.pyplot(fig)


def render_growth_prediction() -> None:
    st.header("Prediksi Pertumbuhan Ternak")
    p = normalise_profile(st.session_state.farm_profile)
    col1, col2 = st.columns(2)
    with col1:
        animal_type = st.selectbox("Komoditas ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="growth_animal", format_func=commodity_label)
        initial_weight = st.number_input("Berat awal (kg)", min_value=0.1, value=max(float(p.get("average_weight_kg", 1.0)), 0.1), step=0.1)
    with col2:
        daily_gain = st.number_input("Pertambahan berat harian (kg/hari)", min_value=0.0, value=0.1, step=0.01)
        days = st.number_input("Periode (hari)", min_value=1, value=30)
    if st.button("Prediksi"):
        try:
            result = predict_growth(initial_weight, daily_gain, int(days))
            st.success(
                f"{animal_type.capitalize()}: {result['initial_weight']:.2f} kg → {result['final_weight']:.2f} kg dalam {result['days']} hari. "
                f"Kenaikan total {result['weight_gain']:.2f} kg."
            )
            st.pyplot(plot_growth_prediction(result))
        except Exception as error:
            st.error(str(error))


def render_bep() -> None:
    st.header("Analisis Break Even Point")
    col1, col2 = st.columns(2)
    with col1:
        fixed_cost = st.number_input("Biaya tetap (Rp)", min_value=0, value=10_000_000, step=100_000)
        price_per_unit = st.number_input("Harga jual per unit (Rp)", min_value=0, value=50_000, step=1_000)
    with col2:
        variable_cost_per_unit = st.number_input("Biaya variabel per unit (Rp)", min_value=0, value=30_000, step=1_000)
    if st.button("Hitung BEP"):
        st.success(calculate_bep(fixed_cost, price_per_unit, variable_cost_per_unit))
        margin = price_per_unit - variable_cost_per_unit
        if margin > 0:
            bep_units = fixed_cost / margin
            bep_revenue = bep_units * price_per_unit
            st.pyplot(plot_bep(fixed_cost, price_per_unit, variable_cost_per_unit, bep_units, bep_revenue))




def render_guided_consultation(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("Konsultasi Bertahap")
    st.caption("Untuk peternak yang belum tahu istilah teknis. Sistem akan mengecek data yang kurang sebelum memberi rekomendasi.")

    topic = st.selectbox(
        "Topik konsultasi",
        CONSULTATION_TOPICS,
        index=CONSULTATION_TOPICS.index(st.session_state.get("guided_topic", "Kesehatan")) if st.session_state.get("guided_topic", "Kesehatan") in CONSULTATION_TOPICS else 0,
    )
    st.session_state.guided_topic = topic
    case = dict(st.session_state.get("guided_case", {}) or {})

    field_groups = {
        "Kesehatan": [
            ("jenis_ternak", "Jenis ternak", "contoh: kambing / ayam broiler / lele"),
            ("jumlah_populasi", "Jumlah populasi", "contoh: 25 ekor"),
            ("umur_fase", "Umur/fase", "contoh: 3 bulan / starter / bunting"),
            ("jumlah_terdampak", "Jumlah terdampak", "contoh: 3 ekor"),
            ("gejala", "Gejala utama", "contoh: mencret, lemas, tidak mau makan"),
            ("durasi", "Durasi", "contoh: sejak kemarin"),
            ("kematian", "Kematian", "contoh: belum ada / 2 ekor mati"),
            ("pakan_air", "Pakan dan air terakhir", "contoh: dedak + rumput, air sumur"),
            ("kondisi_kandang", "Kondisi kandang/kolam", "contoh: lembap, bau amonia, padat"),
            ("target_masalah", "Target bantuan", "contoh: tindakan awal aman"),
        ],
        "Pakan": [
            ("jenis_ternak", "Jenis ternak", "contoh: sapi penggemukan"),
            ("jumlah_populasi", "Jumlah populasi", "contoh: 10 ekor"),
            ("umur_fase", "Fase", "contoh: finisher / laktasi"),
            ("bobot_rata_rata", "Bobot rata-rata", "contoh: 28 kg"),
            ("bahan_pakan", "Bahan pakan tersedia", "contoh: odot, dedak, ampas tahu"),
            ("harga_bahan", "Harga bahan", "contoh: dedak 3500/kg"),
            ("konsumsi_pakan", "Konsumsi pakan saat ini", "contoh: 40 kg/hari"),
            ("tujuan_formula", "Tujuan formula", "contoh: murah tapi aman"),
            ("target_masalah", "Masalah utama", "contoh: biaya pakan terlalu tinggi"),
        ],
        "Reproduksi": [
            ("jenis_ternak", "Jenis ternak", "contoh: sapi / kambing / kelinci"),
            ("jumlah_populasi", "Jumlah induk", "contoh: 8 induk"),
            ("umur_fase", "Umur/fase induk", "contoh: induk laktasi"),
            ("tanggal_kawin_ib", "Tanggal kawin/IB", "contoh: 2026-05-01"),
            ("riwayat_beranak", "Riwayat beranak", "contoh: sudah 2 kali"),
            ("tanda_birahi", "Tanda birahi", "contoh: gelisah, vulva merah"),
            ("kondisi_induk", "Kondisi induk", "contoh: kurus/sedang/gemuk"),
            ("target_masalah", "Masalah utama", "contoh: sulit bunting"),
        ],
        "Usaha/Biaya": [
            ("jenis_ternak", "Jenis ternak", "contoh: broiler / kambing"),
            ("jumlah_populasi", "Jumlah populasi", "contoh: 500 ekor"),
            ("umur_fase", "Fase", "contoh: umur 21 hari"),
            ("modal", "Modal/biaya berjalan", "contoh: Rp 15 juta"),
            ("biaya_pakan", "Biaya pakan", "contoh: Rp 250 ribu/hari"),
            ("harga_jual", "Harga jual target", "contoh: Rp 55 ribu/kg"),
            ("target_panen", "Target panen", "contoh: 30 hari lagi"),
            ("tenaga_kerja", "Tenaga kerja", "contoh: 2 orang"),
            ("target_masalah", "Masalah utama", "contoh: hitung untung/rugi"),
        ],
        "Kandang/Kolam": [
            ("jenis_ternak", "Jenis ternak", "contoh: kambing / lele"),
            ("jumlah_populasi", "Jumlah populasi", "contoh: 1000 ekor"),
            ("umur_fase", "Fase", "contoh: pembesaran"),
            ("tipe_kandang", "Tipe kandang/kolam", "contoh: kandang panggung / kolam terpal"),
            ("ukuran", "Ukuran", "contoh: 4x6 m"),
            ("kepadatan", "Kepadatan", "contoh: 15 ekor/kandang"),
            ("drainase_ventilasi", "Drainase/ventilasi/aerasi", "contoh: kurang lancar"),
            ("masalah_lingkungan", "Masalah lingkungan", "contoh: bau, becek, air keruh"),
            ("target_masalah", "Target bantuan", "contoh: susun perbaikan kandang"),
        ],
        "Produksi": [
            ("jenis_ternak", "Jenis ternak", "contoh: ayam layer / sapi perah"),
            ("jumlah_populasi", "Jumlah populasi", "contoh: 200 ekor"),
            ("umur_fase", "Fase", "contoh: awal produksi"),
            ("produksi_harian", "Produksi harian", "contoh: 150 telur/hari"),
            ("bobot_awal", "Bobot awal", "contoh: 20 kg"),
            ("bobot_sekarang", "Bobot sekarang", "contoh: 26 kg"),
            ("pakan_harian", "Pakan harian", "contoh: 30 kg"),
            ("mortalitas", "Mortalitas/sakit", "contoh: 2 ekor"),
            ("target_masalah", "Masalah utama", "contoh: produksi turun"),
        ],
    }

    with st.form("guided_consultation_form"):
        updated_case: Dict[str, Any] = {}
        for key, label, placeholder in field_groups.get(topic, field_groups["Kesehatan"]):
            if key in {"gejala", "pakan_air", "kondisi_kandang", "bahan_pakan", "harga_bahan", "target_masalah", "masalah_lingkungan"}:
                updated_case[key] = st.text_area(label, value=str(case.get(key, "")), placeholder=placeholder, height=80)
            else:
                updated_case[key] = st.text_input(label, value=str(case.get(key, "")), placeholder=placeholder)
        submitted = st.form_submit_button("Simpan & Analisis Bertahap", width="stretch")

    missing = guided_questions(topic, updated_case if submitted else case)
    if submitted:
        st.session_state.guided_case = updated_case
        case = updated_case
        st.success("Data konsultasi tersimpan.")

    if case:
        st.subheader("Data yang masih kurang")
        if missing:
            for question in missing[:8]:
                st.warning(question)
        else:
            st.success("Data utama sudah cukup untuk analisis awal.")

        if st.button("Minta Rekomendasi AI dari Data Ini", width="stretch"):
            prompt = "Beri konsultasi bertahap sesuai data kasus. Jika data masih kurang, jawab dengan asumsi sementara dan pertanyaan lanjutan paling penting."
            with st.spinner(AI_LOADING_TEXT):
                response, meta = run_ai_consultation(
                    prompt,
                    selected_model_id,
                    selected_fallback_models,
                    selected_temperature,
                    max_history_messages,
                    prefer_ai,
                    extra_context=guided_case_context(topic, case),
                )
            update_usage(meta)
            append_decision_log(prompt, response, meta)
            st.markdown(response)
            render_decision_card_from_last()
            render_ai_trace(meta)


def render_benchmark_kpi(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("Benchmark KPI Performa")
    st.caption("Membandingkan catatan farm dengan indikator dasar seperti ADG, FCR, mortalitas, dan kelengkapan recording.")
    benchmark = benchmark_kpi(st.session_state.farm_profile, st.session_state.farm_records)
    summary = benchmark["summary"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risiko KPI", benchmark["risk_level"])
    col2.metric("ADG", "-" if summary.get("adg") is None else f"{summary['adg']:.3f} kg/hari")
    col3.metric("FCR", "-" if summary.get("fcr") is None else f"{summary['fcr']:.2f}")
    col4.metric("Mortalitas", f"{summary.get('mortality_total', 0)} ekor")
    st.subheader("Temuan benchmark")
    for item in benchmark["findings"]:
        st.write(f"- {item}")
    if not st.session_state.farm_records:
        st.info("Tambahkan catatan performa minimal 2 tanggal agar ADG/FCR lebih bermakna.")
    if st.button("Minta Analisis AI KPI", width="stretch"):
        with st.spinner(AI_LOADING_TEXT):
            response, meta = run_ai_consultation(
                "Analisis KPI farm ini dan berikan keputusan manajerial untuk peternak.",
                selected_model_id,
                selected_fallback_models,
                selected_temperature,
                max_history_messages,
                prefer_ai,
                extra_context="Benchmark KPI:\n" + json.dumps(benchmark, ensure_ascii=False, indent=2),
            )
        update_usage(meta)
        append_decision_log("Analisis KPI farm", response, meta)
        st.markdown(response)
        render_decision_card_from_last()
        render_ai_trace(meta)


def render_sop_biosecurity(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("SOP & Biosecurity")
    st.caption("Membuat SOP sederhana/industri dan menilai risiko biosecurity farm.")
    st.subheader("Checklist Biosecurity")
    checked = st.multiselect(
        "Centang yang sudah diterapkan",
        BIOSECURITY_ITEMS,
        default=[item for item in st.session_state.get("biosecurity_checked", []) if item in BIOSECURITY_ITEMS],
    )
    st.session_state.biosecurity_checked = checked
    score = biosecurity_score(checked)
    col1, col2, col3 = st.columns(3)
    col1.metric("Skor", f"{score['score']}/100")
    col2.metric("Level", score["level"])
    col3.metric("Checklist", f"{score['checked']}/{score['total']}")
    if score["missing"]:
        st.warning("Prioritas perbaikan: " + "; ".join(score["missing"][:4]))

    st.subheader("Generator SOP")
    sop_type = st.selectbox("Jenis SOP", list(SOP_TEMPLATES.keys()))
    local_sop = generate_sop(st.session_state.farm_profile, sop_type, st.session_state.user_mode)
    st.markdown("```text\n" + local_sop + "\n```")
    st.download_button(
        "Download SOP TXT",
        data=local_sop,
        file_name=f"sop-{sop_type.lower().replace(' ', '-')}.txt",
        mime="text/plain",
        width="stretch",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Simpan SOP ke Sesi", width="stretch"):
            st.session_state.last_sop = {"type": sop_type, "content": local_sop, "created_at": datetime.now().isoformat(timespec="seconds"), "biosecurity": score}
            st.success("SOP tersimpan ke sesi dan backup XLSX.")
    with col_b:
        if st.button("Perbaiki SOP dengan AI", width="stretch"):
            with st.spinner(AI_LOADING_TEXT):
                response, meta = run_ai_consultation(
                    "Perbaiki SOP berikut agar sesuai profil farm, skala usaha, risiko, dan mode pengguna.",
                    selected_model_id,
                    selected_fallback_models,
                    selected_temperature,
                    max_history_messages,
                    prefer_ai,
                    extra_context=f"SOP awal:\n{local_sop}\n\nBiosecurity score:\n{json.dumps(score, ensure_ascii=False)}",
                )
            update_usage(meta)
            append_decision_log("Perbaiki SOP dengan AI", response, meta)
            st.session_state.last_sop = {"type": sop_type, "content": response, "created_at": datetime.now().isoformat(timespec="seconds"), "biosecurity": score}
            st.markdown(response)
            render_decision_card_from_last()
            render_ai_trace(meta)


def render_business_prediction(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("Prediksi Usaha, Panen, dan Stok Pakan")
    st.caption("Menghitung estimasi kebutuhan pakan, umur stok, target panen, dan gambaran pendapatan awal.")
    p = normalise_profile(st.session_state.farm_profile)
    col1, col2 = st.columns(2)
    with col1:
        feed_stock = st.number_input("Stok pakan saat ini (kg)", min_value=0.0, value=0.0, step=1.0)
        target_weight = st.number_input("Target bobot panen per ekor (kg)", min_value=0.0, value=max(float(p.get("average_weight_kg", 0.0)), 0.0), step=0.1)
    with col2:
        sale_price = st.number_input("Harga jual target per ekor/unit (Rp)", min_value=0.0, value=0.0, step=1000.0)
        extra_cost = st.number_input("Biaya tersisa sampai panen (Rp)", min_value=0.0, value=0.0, step=10000.0)
    if st.button("Hitung Prediksi", width="stretch"):
        result = predict_operations(st.session_state.farm_profile, st.session_state.farm_records, feed_stock, target_weight, sale_price, extra_cost)
        st.session_state.last_prediction = {"created_at": datetime.now().isoformat(timespec="seconds"), "input": {"feed_stock_kg": feed_stock, "target_weight_kg": target_weight, "sale_price_per_unit": sale_price, "extra_cost_rp": extra_cost}, "result": result}
        st.success("Prediksi tersimpan ke sesi.")
    result = st.session_state.get("last_prediction", {}).get("result", {})
    if result:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pakan/hari", f"{result['daily_feed_need_kg']:.2f} kg")
        c2.metric("Stok cukup", f"{result['feed_stock_days']:.1f} hari")
        c3.metric("Estimasi panen", result["harvest_date"])
        c4.metric("Margin kasar", f"Rp {result['estimated_margin_before_unrecorded_cost_rp']:,.0f}".replace(",", "."))
        st.json(result)
        if result["feed_stock_days"] < 7:
            st.warning("Stok pakan kurang dari 7 hari. Prioritaskan pengadaan agar konsumsi tidak turun.")
        if st.button("Minta Insight AI Prediksi", width="stretch"):
            with st.spinner(AI_LOADING_TEXT):
                response, meta = run_ai_consultation(
                    "Analisis prediksi usaha, panen, dan stok pakan ini. Berikan keputusan 24 jam, 7 hari, dan 30 hari.",
                    selected_model_id,
                    selected_fallback_models,
                    selected_temperature,
                    max_history_messages,
                    prefer_ai,
                    extra_context="Prediksi usaha:\n" + json.dumps(st.session_state.last_prediction, ensure_ascii=False, indent=2),
                )
            update_usage(meta)
            append_decision_log("Insight AI Prediksi Usaha", response, meta)
            st.markdown(response)
            render_decision_card_from_last()
            render_ai_trace(meta)


def render_local_library() -> None:
    st.header("Library Pengetahuan Lokal Indonesia")
    st.caption("Referensi cepat bahan pakan, sistem kandang, dan praktik lokal yang sering dipakai peternak.")
    query = st.text_input("Cari istilah", placeholder="contoh: odot, ampas tahu, bioflok")
    rows = []
    for name, data in LOCAL_LIBRARY.items():
        text = f"{name} {data.get('kategori','')} {data.get('ringkas','')} {data.get('catatan','')}".lower()
        if not query or query.lower() in text:
            rows.append({"Istilah": name, "Kategori": data.get("kategori", ""), "Ringkas": data.get("ringkas", ""), "Catatan": data.get("catatan", "")})
    st.dataframe(rows, width="stretch", hide_index=True)
    if rows:
        st.download_button("Download Library JSON", data=json.dumps(rows, ensure_ascii=False, indent=2), file_name="library-lokal-peternakan.json", mime="application/json", width="stretch")


def render_education() -> None:
    st.header("Edukasi Peternak")
    st.caption("Materi singkat dan kuis untuk peternak pemula maupun pengelola farm modern.")
    module = st.selectbox("Modul belajar", list(EDUCATION_MODULES.keys()))
    completed = set(st.session_state.get("education_progress", []) or [])
    for idx, lesson in enumerate(EDUCATION_MODULES[module], 1):
        lesson_id = f"{module}:{idx}"
        with st.expander(f"{idx}. {lesson['judul']}" + (" ✓" if lesson_id in completed else ""), expanded=lesson_id not in completed):
            st.write(lesson["materi"])
            answer = st.text_area("Jawab kuis singkat", key=f"quiz_{lesson_id}", placeholder=lesson["kuis"], height=70)
            if st.button("Tandai selesai", key=f"done_{lesson_id}"):
                if lesson_id not in completed:
                    st.session_state.education_progress.append(lesson_id)
                st.success("Materi ditandai selesai.")
                safe_rerun()
    total = sum(len(items) for items in EDUCATION_MODULES.values())
    st.metric("Progress belajar", f"{len(set(st.session_state.education_progress))}/{total} materi")


def render_management_report() -> None:
    st.header("Laporan Manajemen")
    st.caption("Ringkasan siap salin/unduh untuk peternak, kelompok ternak, atau manajer farm.")
    profile = normalise_profile(st.session_state.farm_profile)
    benchmark = benchmark_kpi(profile, st.session_state.farm_records)
    ready = readiness_score(profile, st.session_state.farm_records, st.session_state.farm_calendar_events, st.session_state.biosecurity_checked)
    dept_report = report_section_markdown(
        profile,
        st.session_state.farm_records,
        st.session_state.farm_calendar_events,
        st.session_state.last_health_case,
        {"formula_selected": st.session_state.get("formula_selected", []), "decision_log": st.session_state.get("decision_log", [])},
    )
    report = f"""
# Laporan Manajemen AI Pakar Ternak

Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Profil Farm
- Nama: {profile.get('farm_name') or '-'}
- Komoditas: {commodity_label(profile.get('animal_type'))} | Bangsa/strain: {profile.get('breed', '-')} | Tujuan pemeliharaan: {goal_label(profile.get('production_goal'))} | Fase: {profile.get('phase')}
- Populasi: {profile.get('population')} ekor | Bobot rata-rata: {profile.get('average_weight_kg')} kg
- Lokasi: {profile.get('location') or '-'}
- Masalah utama: {profile.get('main_problem') or '-'}

## Skor Kesiapan
- Skor: {ready['score']}/100
- Level: {ready['level']}
- Catatan prioritas: {'; '.join(ready['reasons']) if ready['reasons'] else 'Belum ada catatan risiko besar.'}

## KPI Performa
- Risiko KPI: {benchmark['risk_level']}
- Temuan: {' | '.join(benchmark['findings'])}

## Biosecurity
- Skor: {ready['biosecurity']['score']}/100 ({ready['biosecurity']['level']})
- Belum lengkap: {'; '.join(ready['biosecurity']['missing'][:5]) if ready['biosecurity']['missing'] else 'Checklist utama terpenuhi.'}

## Agenda Manajemen
- Jumlah jadwal tersimpan: {len(st.session_state.farm_calendar_events)}
- Jumlah catatan performa: {len(st.session_state.farm_records)}

{dept_report}

## Rekomendasi Singkat
1. Lengkapi profil dan recording jika masih kosong.
2. Timbang/estimasi pakan dan bobot secara berkala agar ADG dan FCR terbaca.
3. Prioritaskan biosecurity, isolasi ternak sakit, dan kebersihan tempat pakan-minum.
4. Gunakan backup XLSX setelah setiap sesi penting.

Developed by Galuh Adi Insani (Fakultas Peternakan UGM)
""".strip()
    st.markdown(report)
    report_payload = build_current_session_payload()
    col_pdf, col_md, col_xlsx = st.columns(3)
    with col_pdf:
        try:
            if st.button("Siapkan PDF", width="stretch", key="report_prepare_pdf"):
                with st.spinner("Menyiapkan laporan PDF..."):
                    prepare_download_files(include_pdf=True)
                st.success("PDF siap diunduh.")
            if st.session_state.get("prepared_download_hash") and st.session_state.get("prepared_pdf_bytes"):
                st.download_button(
                    "Download Laporan PDF",
                    data=st.session_state.prepared_pdf_bytes,
                    file_name=st.session_state.prepared_pdf_name or pdf_report_filename(report_payload),
                    mime="application/pdf",
                    width="stretch",
                    key="report_download_pdf",
                )
        except Exception as error:
            st.error(f"Gagal membuat PDF: {error}")
    with col_md:
        st.download_button("Download Laporan Markdown", data=report, file_name="laporan-manajemen-pakar-ternak.md", mime="text/markdown", width="stretch")
    with col_xlsx:
        try:
            if st.button("Siapkan XLSX", width="stretch", key="report_prepare_xlsx"):
                with st.spinner("Menyiapkan backup XLSX..."):
                    prepare_download_files(include_pdf=False)
                st.success("XLSX siap diunduh.")
            if st.session_state.get("prepared_download_hash") and st.session_state.get("prepared_xlsx_bytes"):
                st.download_button(
                    "Download Backup Lengkap XLSX",
                    data=st.session_state.prepared_xlsx_bytes,
                    file_name=st.session_state.prepared_xlsx_name or session_filename(report_payload),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                    key="report_download_xlsx",
                )
        except Exception as error:
            st.error(f"Gagal membuat XLSX: {error}")

def render_workflow_overview() -> None:
    st.subheader("Alur kerja sederhana")
    st.caption("Ikuti urutan ini agar peternak tidak bingung: isi data dulu, konsultasi, baca insight, lalu simpan backup.")
    columns = st.columns(len(WORKFLOW_STEPS))
    for col, item in zip(columns, WORKFLOW_STEPS):
        with col:
            st.markdown(
                f"""
                <div class="ptn-step-card">
                    <div class="ptn-step-number">{item['step']}</div>
                    <div class="ptn-card-title">{item['title']}</div>
                    <div class="ptn-card-body">{item['description']}</div>
                    <div class="ptn-card-meta">Menu: {item['menu']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_simple_home() -> None:
    render_dashboard()
    st.divider()
    render_department_framework()
    st.divider()
    render_workflow_overview()


def render_input_data_center() -> None:
    st.header("Input Data")
    st.caption("Semua data dasar dikumpulkan di sini. Data ini menjadi dasar jawaban AI, insight, laporan, dan backup XLSX.")
    tab_profile, tab_records, tab_calendar = st.tabs(["1. Profil Farm", "2. Catatan Performa", "3. Kalender"])
    with tab_profile:
        render_profile()
    with tab_records:
        render_records()
    with tab_calendar:
        render_calendar()


def render_consultation_center(
    selected_model_id: str,
    selected_fallback_models: List[str],
    selected_temperature: float,
    max_history_messages: int,
    prefer_ai: bool,
) -> None:
    st.header("Konsultasi AI")
    st.caption("Gunakan konsultasi bertahap untuk peternak pemula. Gunakan chat pakar untuk pertanyaan bebas. Gunakan triase untuk kasus kesehatan.")
    tab_guided, tab_dept, tab_chat, tab_health = st.tabs(["Konsultasi Bertahap", "5 Departemen", "Chat Pakar", "Triase Kesehatan"])
    with tab_guided:
        render_guided_consultation(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_dept:
        render_department_consultation(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_chat:
        render_chat(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_health:
        render_health_consultation(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)


def render_decision_center(
    selected_model_id: str,
    selected_fallback_models: List[str],
    selected_temperature: float,
    max_history_messages: int,
    prefer_ai: bool,
) -> None:
    st.header("Insight & Keputusan")
    st.caption("Bagian ini dipakai setelah data farm terisi. Fokusnya adalah rekomendasi tindakan, efisiensi pakan, KPI, SOP, dan prediksi usaha.")
    tab_insight, tab_feed, tab_kpi, tab_prediction, tab_sop, tab_hasil, tab_log = st.tabs([
        "AI Insight",
        "Formulasi Pakan",
        "Benchmark KPI",
        "Prediksi Usaha",
        "SOP & Biosecurity",
        "Teknologi Hasil",
        "Log Keputusan",
    ])
    with tab_insight:
        render_ai_insights(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_feed:
        render_feed_formulation()
    with tab_kpi:
        render_benchmark_kpi(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_prediction:
        render_business_prediction(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_sop:
        render_sop_biosecurity(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_hasil:
        render_technology_results_center(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
    with tab_log:
        render_decision_log()



def _enterprise_state() -> Dict[str, Any]:
    st.session_state.enterprise_state = normalise_enterprise_state(st.session_state.get("enterprise_state", {}))
    return st.session_state.enterprise_state


def _save_enterprise_state(state: Dict[str, Any], action: str = "Update", detail: str = "") -> None:
    state = normalise_enterprise_state(state)
    state.setdefault("audit_trail", [])
    if detail:
        state["audit_trail"].append(make_audit_event(action, state.get("current_role", ""), detail))
        state["audit_trail"] = state["audit_trail"][-500:]
    st.session_state.enterprise_state = state


def render_executive_dashboard() -> None:
    st.subheader("Dashboard Direktur Utama")
    profile = normalise_profile(st.session_state.farm_profile)
    state = _enterprise_state()
    summary = executive_summary(profile, st.session_state.farm_records, st.session_state.farm_calendar_events, st.session_state.last_health_case, st.session_state.biosecurity_checked, state)
    finance = finance_snapshot(profile, st.session_state.farm_records, state.get("finance_transactions", []))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skor Enterprise", f"{summary['score']}/100", summary["level"])
    c2.metric("Farm/Unit", summary.get("farms", 0))
    c3.metric("Batch", summary.get("batches", 0))
    c4.metric("Margin Kasar", format_rupiah(finance.get("gross_margin_rp", 0)))
    st.markdown("### Prioritas Direksi Minggu Ini")
    warnings = summary.get("warnings", [])
    if warnings:
        for idx, warn in enumerate(warnings[:5], 1):
            st.markdown(f"**{idx}. {warn['level']} | {warn['area']}** — {warn['finding']}  ")
            st.caption(f"Tindakan: {warn['action']}")
    else:
        st.success("Belum ada peringatan utama. Pertahankan recording dan review KPI mingguan.")
    st.markdown("### Ringkasan Eksekutif")
    st.info(summary.get("priority", "Pertahankan kontrol operasional."))


def render_multi_farm_batch() -> None:
    st.subheader("Multi-Farm, Unit, dan Batch")
    state = _enterprise_state()
    with st.form("enterprise_company_form"):
        company_name = st.text_input("Nama perusahaan / holding / kelompok", value=state.get("company_name", ""))
        feed_stock = st.number_input("Stok pakan total saat ini (kg)", min_value=0.0, value=float(state.get("feed_stock_kg", 0.0) or 0.0), step=10.0)
        submitted = st.form_submit_button("Simpan konteks perusahaan", width="stretch")
        if submitted:
            state["company_name"] = company_name
            state["feed_stock_kg"] = feed_stock
            _save_enterprise_state(state, "Update perusahaan", f"Konteks perusahaan diperbarui: {company_name}")
            st.success("Konteks perusahaan tersimpan.")

    st.markdown("#### Tambah Farm/Unit")
    with st.form("add_farm_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Nama farm/unit", placeholder="Farm Sleman / Kandang Broiler A / Unit Lele 1")
        location = col2.text_input("Lokasi")
        manager = col1.text_input("Penanggung jawab")
        commodity = col2.text_input("Komoditas utama", value=normalise_profile(st.session_state.farm_profile).get("animal_type", ""))
        if st.form_submit_button("Tambah Farm/Unit", width="stretch"):
            if name.strip():
                item = {"id": make_audit_event("id", "system", name)["created_at"].replace(":", "").replace("-", ""), "name": name, "location": location, "manager": manager, "commodity": commodity, "created_at": datetime.now().isoformat(timespec="seconds")}
                state.setdefault("farms", []).append(item)
                state["active_farm_id"] = item["id"]
                _save_enterprise_state(state, "Tambah farm", f"Menambahkan farm/unit {name}")
                st.success("Farm/unit ditambahkan.")
            else:
                st.warning("Nama farm/unit wajib diisi.")

    farms = state.get("farms", [])
    if farms:
        st.dataframe(farms, width="stretch", hide_index=True)
    else:
        st.info("Belum ada farm/unit tambahan. Profil utama tetap digunakan sebagai unit default.")

    st.markdown("#### Tambah Batch / Siklus Produksi")
    with st.form("add_batch_form"):
        col1, col2, col3 = st.columns(3)
        batch_name = col1.text_input("Nama batch", placeholder="Batch Broiler Mei 2026")
        start_date = col2.date_input("Tanggal mulai", value=date.today())
        target_date = col3.date_input("Target panen / evaluasi", value=date.today() + timedelta(days=35))
        target_population = col1.number_input("Populasi target", min_value=0, value=int(normalise_profile(st.session_state.farm_profile).get("population", 0)), step=1)
        target_weight = col2.number_input("Target bobot/produksi", min_value=0.0, value=0.0, step=0.1)
        market = col3.text_input("Target pasar")
        if st.form_submit_button("Tambah Batch", width="stretch"):
            if batch_name.strip():
                item = {"id": f"batch-{datetime.now().strftime('%Y%m%d%H%M%S')}", "name": batch_name, "farm_id": state.get("active_farm_id", ""), "start_date": start_date.isoformat(), "target_date": target_date.isoformat(), "target_population": target_population, "target_weight_or_output": target_weight, "market": market, "status": "Aktif"}
                state.setdefault("batches", []).append(item)
                state["active_batch_id"] = item["id"]
                _save_enterprise_state(state, "Tambah batch", f"Menambahkan batch {batch_name}")
                st.success("Batch ditambahkan.")
            else:
                st.warning("Nama batch wajib diisi.")
    if state.get("batches"):
        st.dataframe(state.get("batches", []), width="stretch", hide_index=True)


def render_quick_daily_input() -> None:
    st.subheader("Input Harian Cepat")
    st.caption("Untuk petugas kandang/peternak rakyat: isi data minimal, sistem memvalidasi dan memasukkannya ke Catatan Performa.")
    p = normalise_profile(st.session_state.farm_profile)
    with st.form("quick_daily_input"):
        col1, col2, col3 = st.columns(3)
        rec_date = col1.date_input("Tanggal", value=date.today())
        population = col2.number_input("Populasi hari ini", min_value=0, value=int(p.get("population", 0)), step=1)
        sick = col3.number_input("Sakit/terindikasi", min_value=0, value=0, step=1)
        mortality = col1.number_input("Mati", min_value=0, value=0, step=1)
        feed_kg = col2.number_input("Pakan terpakai (kg)", min_value=0.0, value=0.0, step=0.1)
        avg_weight = col3.number_input("Bobot rata-rata (kg)", min_value=0.0, value=float(p.get("average_weight_kg", 0.0)), step=0.1)
        cost = col1.number_input("Biaya hari ini (Rp)", min_value=0.0, value=0.0, step=1000.0)
        eggs = col2.number_input("Telur (butir)", min_value=0, value=0, step=1)
        milk = col3.number_input("Susu (liter)", min_value=0.0, value=0.0, step=0.1)
        note = st.text_area("Catatan lapangan", placeholder="contoh: nafsu makan turun, litter basah, pakan baru, suhu kandang panas")
        submitted = st.form_submit_button("Simpan Input Harian", width="stretch")
    if submitted:
        record = {"date": rec_date.isoformat(), "population": population, "avg_weight_kg": avg_weight, "feed_kg": feed_kg, "cost_rp": cost, "mortality": mortality, "eggs": eggs, "milk_liter": milk, "note": f"Sakit: {sick}. {note}".strip()}
        issues = validate_record_data(record, p)
        if issues:
            for issue in issues:
                st.warning(f"{issue['level']} - {issue['field']}: {issue['message']}")
        st.session_state.farm_records = add_record(st.session_state.farm_records, record)
        state = _enterprise_state()
        state.setdefault("quick_inputs", []).append({**record, "sick": sick})
        _save_enterprise_state(state, "Input harian", f"Input harian {rec_date.isoformat()} disimpan")
        st.success("Input harian tersimpan ke Catatan Performa dan Backup XLSX.")


def render_kpi_early_warning() -> None:
    st.subheader("KPI Standar dan Early Warning")
    p = normalise_profile(st.session_state.farm_profile)
    state = _enterprise_state()
    standard = kpi_standard_for(p.get("animal_type", ""), p.get("production_goal", ""))
    st.markdown("#### Standar KPI Komoditas")
    st.json(standard)
    warnings = early_warnings(p, st.session_state.farm_records, st.session_state.farm_calendar_events, st.session_state.last_health_case, st.session_state.biosecurity_checked, state)
    st.markdown("#### Early Warning")
    if warnings:
        for warn in warnings:
            if warn["level"] == "Merah":
                st.error(f"{warn['area']}: {warn['finding']}\n\nTindakan: {warn['action']}")
            else:
                st.warning(f"{warn['area']}: {warn['finding']}\n\nTindakan: {warn['action']}")
    else:
        st.success("Belum ada early warning utama.")


def render_finance_center() -> None:
    st.subheader("Keuangan, HPP, ROI, dan Cashflow")
    state = _enterprise_state()
    with st.form("finance_form"):
        col1, col2, col3 = st.columns(3)
        tx_date = col1.date_input("Tanggal transaksi", value=date.today())
        tx_type = col2.selectbox("Jenis", ["Biaya", "Pendapatan", "Investasi", "Pakan", "Obat/Vaksin", "Tenaga Kerja", "Transportasi", "Lainnya"])
        amount = col3.number_input("Nominal (Rp)", min_value=0.0, value=0.0, step=10000.0)
        desc = st.text_input("Keterangan")
        if st.form_submit_button("Tambah Transaksi", width="stretch"):
            state.setdefault("finance_transactions", []).append({"date": tx_date.isoformat(), "type": tx_type, "amount_rp": amount, "description": desc})
            _save_enterprise_state(state, "Tambah transaksi", f"{tx_type} Rp {amount:,.0f}: {desc}")
            st.success("Transaksi ditambahkan.")
    snap = finance_snapshot(normalise_profile(st.session_state.farm_profile), st.session_state.farm_records, state.get("finance_transactions", []))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pendapatan", format_rupiah(snap["revenue_rp"]))
    c2.metric("Total Biaya", format_rupiah(snap["total_cost_rp"]))
    c3.metric("Margin Kasar", format_rupiah(snap["gross_margin_rp"]))
    c4.metric("HPP / ekor-unit", format_rupiah(snap["hpp_per_head_rp"]))
    if snap.get("roi_pct") is not None:
        st.caption(f"ROI estimasi: {snap['roi_pct']:.2f}%")
    if state.get("finance_transactions"):
        st.dataframe(state["finance_transactions"], width="stretch", hide_index=True)


def render_knowledge_base_center() -> None:
    st.subheader("Knowledge Base / RAG Ringan")
    st.caption("Tambahkan SOP, standar perusahaan, atau catatan teknis. AI akan memakai memory/konteks ini melalui sesi dan backup XLSX.")
    state = _enterprise_state()
    with st.form("kb_form"):
        title = st.text_input("Judul dokumen/catatan")
        tags = st.text_input("Tag", placeholder="pakan, broiler, SOP, susu")
        content = st.text_area("Isi ringkas", height=120)
        if st.form_submit_button("Tambah Knowledge", width="stretch"):
            if title.strip() and content.strip():
                state.setdefault("knowledge_docs", []).append({"created_at": datetime.now().isoformat(timespec="seconds"), "title": title, "tags": tags, "content": content})
                _save_enterprise_state(state, "Tambah knowledge", title)
                add_expert_memory(f"Knowledge internal: {title} — {content[:500]}", category="Knowledge Base", priority="Tinggi", source="enterprise")
                st.success("Knowledge ditambahkan dan diringkas ke Memory Ahli.")
            else:
                st.warning("Judul dan isi wajib diisi.")
    query = st.text_input("Cari knowledge", placeholder="contoh: SOP vaksin broiler")
    if query:
        results = knowledge_search(query, state.get("knowledge_docs", []))
        if results:
            for doc in results:
                with st.expander(doc.get("title", "Knowledge")):
                    st.caption(doc.get("tags", ""))
                    st.write(doc.get("content", ""))
        else:
            st.info("Belum ada dokumen yang cocok.")
    if state.get("knowledge_docs"):
        st.dataframe([{k: v for k, v in d.items() if k != "content"} for d in state["knowledge_docs"]], width="stretch", hide_index=True)


def render_downstream_center() -> None:
    st.subheader("Hilirisasi dan Teknologi Hasil")
    guide = downstream_guidance(normalise_profile(st.session_state.farm_profile))
    st.markdown(f"Fokus produk: **{guide['category'].title()}**")
    for item in guide.get("checklist", []):
        st.checkbox(item, value=False, key=f"downstream_{guide['category']}_{item[:18]}")
    st.info("Untuk perusahaan, catat susut, grade mutu, cold chain, reject, dan nilai tambah produk pada transaksi/knowledge base.")


def render_database_sync_center() -> None:
    st.subheader("Database Permanen Opsional")
    st.caption("Streamlit Cloud bisa restart. Untuk permanen sungguhan, hubungkan ke Supabase PostgreSQL melalui Secrets. XLSX tetap menjadi backup offline.")
    state = _enterprise_state()
    cfg = get_storage_config(st.secrets)
    status_label = cfg.get("configured")
    mode_label = cfg.get("mode")
    st.write(f"Provider: **{cfg.get('provider')}** | Mode: **{mode_label}** | Status: **{status_label}**")
    if cfg.get("mode") == "postgres":
        st.caption(f"Host: {cfg.get('host') or 'via DATABASE_URL'} | Database: {cfg.get('database')} | Table: {cfg.get('table')}")

    with st.expander("Contoh Secrets Supabase PostgreSQL", expanded=False):
        st.code("""[database]
provider = "postgres"
host = "db.huhezxjjnypthgbafmdv.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "ISI_PASSWORD_DATABASE_SUPABASE"
sslmode = "require"
table = "ai_pakar_ternak_sessions""".strip(), language="toml")
        st.caption("Masukkan di Streamlit App settings → Secrets. Jangan simpan password database di repository publik.")

    with st.expander("Alternatif: DATABASE_URL", expanded=False):
        st.code("""[database]
provider = "postgres"
database_url = "postgresql://postgres:ISI_PASSWORD@db.huhezxjjnypthgbafmdv.supabase.co:5432/postgres?sslmode=require"
table = "ai_pakar_ternak_sessions""".strip(), language="toml")

    if st.button("Tes Koneksi Database", width="stretch"):
        try:
            result = test_enterprise_database_connection(st.secrets)
            if result.get("ok"):
                st.success(result.get("message", "Koneksi berhasil."))
            else:
                st.warning(result.get("message", "Koneksi belum siap."))
        except Exception as error:
            st.error(f"Tes koneksi database gagal: {error}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Simpan ke Database", width="stretch"):
            try:
                result = save_enterprise_payload(build_current_session_payload(), st.secrets)
                state["last_sync_status"] = result
                _save_enterprise_state(state, "Sync database", result.get("message", ""))
                st.success(result.get("message", "Berhasil disimpan."))
            except Exception as error:
                st.error(f"Gagal sync database: {error}")
    with col2:
        session_id = st.text_input("Session ID untuk dimuat", value=st.session_state.session_id)
        if st.button("Muat dari Database", width="stretch"):
            ok, payload, msg = load_enterprise_payload(session_id, st.secrets)
            if ok:
                restore_session_from_payload(payload)
                st.success(msg)
                safe_rerun()
            else:
                st.warning(msg)
    if state.get("last_sync_status"):
        safe_status = dict(state["last_sync_status"])
        for secret_key in ("password", "supabase_key", "database_url"):
            safe_status.pop(secret_key, None)
        st.json(safe_status)


def render_database_admin_gate() -> bool:
    """Show a dedicated admin gate for the Database Supabase page."""
    password, password_source = get_admin_password()
    if not password:
        st.warning("Admin Mode belum aktif. Tambahkan [admin] password di Streamlit Secrets terlebih dahulu.")
        st.code(
            """[admin]
password = "ISI_KUNCI_ADMIN_ANDA"

[database]
provider = "postgres"
host = "db.huhezxjjnypthgbafmdv.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "ISI_PASSWORD_DATABASE_SUPABASE"
sslmode = "require"
table = "ai_pakar_ternak_sessions""".strip(),
            language="toml",
        )
        return False

    if st.session_state.get("admin_authenticated", False):
        st.success(f"Admin Mode aktif · sumber kunci: {password_source}")
        return True

    st.info("Database Supabase hanya dapat dibuka oleh admin agar data peternak dan konfigurasi database tetap aman.")
    with st.form("database_page_admin_login_form", clear_on_submit=True):
        candidate = st.text_input("Kunci admin", type="password", placeholder="Masukkan kunci admin")
        submitted = st.form_submit_button("Buka Database Supabase", width="stretch")
        if submitted:
            if check_admin_password(candidate):
                st.session_state.admin_authenticated = True
                st.session_state.admin_login_error = ""
                st.success("Admin Mode aktif. Halaman database akan dimuat ulang.")
                safe_rerun()
            else:
                st.session_state.admin_login_error = "Kunci admin salah."
    if st.session_state.get("admin_login_error"):
        st.error(st.session_state.admin_login_error)
    return False


def render_database_supabase_page() -> None:
    st.header("Database Supabase")
    st.caption("Tes koneksi, simpan sesi, dan pulihkan data AI Pakar Ternak dari Supabase PostgreSQL.")

    st.info(
        "Urutan penggunaan: 1) isi Secrets di Streamlit, 2) reboot app, 3) masuk Admin Mode, "
        "4) klik Tes Koneksi Database, 5) simpan atau pulihkan data."
    )

    if not render_database_admin_gate():
        return

    render_database_sync_center()

    with st.expander("SQL tabel Supabase jika ingin dibuat manual", expanded=False):
        st.code(
            """-- Skema baru yang dipakai aplikasi.
CREATE TABLE IF NOT EXISTS ai_pakar_ternak_sessions (
    session_id TEXT PRIMARY KEY,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ai_pakar_ternak_sessions_updated_at
ON ai_pakar_ternak_sessions (updated_at DESC);

-- Jika Anda sudah pernah membuat tabel versi lama, jalankan migrasi ini sekali:
ALTER TABLE ai_pakar_ternak_sessions ADD COLUMN IF NOT EXISTS session_id TEXT;
ALTER TABLE ai_pakar_ternak_sessions ADD COLUMN IF NOT EXISTS payload JSONB;
UPDATE ai_pakar_ternak_sessions SET session_id = session_key WHERE session_id IS NULL AND session_key IS NOT NULL;
UPDATE ai_pakar_ternak_sessions SET payload = data WHERE payload IS NULL AND data IS NOT NULL;""".strip(),
            language="sql",
        )

def _normalise_whatsapp_number(value: str) -> str:
    """Return a WhatsApp-ready international phone number without symbols."""
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if raw.startswith("0"):
        raw = "62" + raw[1:]
    return raw


def _build_email_url(email: str, subject: str, body: str) -> str:
    return f"mailto:{email.strip()}?subject={quote(subject)}&body={quote(body)}"


def _build_whatsapp_url(phone: str, body: str) -> str:
    number = _normalise_whatsapp_number(phone)
    if number:
        return f"https://wa.me/{number}?text={quote(body)}"
    return f"https://wa.me/?text={quote(body)}"


def _render_external_action_button(label: str, url: str, help_text: str | None = None) -> None:
    """Render link-style action safely across Streamlit versions."""
    if hasattr(st, "link_button"):
        st.link_button(label, url, width="stretch", help=help_text)
    else:
        st.markdown(f"[{label}]({url})")


def render_notification_center() -> None:
    st.subheader("Notifikasi Email & WhatsApp")
    st.caption("Klik tombol Email atau WhatsApp untuk membuka aplikasi yang tersedia di perangkat pengguna dengan pesan yang sudah terisi otomatis.")

    summary = executive_summary(
        normalise_profile(st.session_state.farm_profile),
        st.session_state.farm_records,
        st.session_state.farm_calendar_events,
        st.session_state.last_health_case,
        st.session_state.biosecurity_checked,
        _enterprise_state(),
    )
    messages = notification_messages(summary)
    default_subject = "Laporan / Peringatan AI Pakar Ternak"
    default_body = "AI Pakar Ternak - Ringkasan Notifikasi\n\n" + "\n".join(f"- {msg}" for msg in messages)

    with st.expander("Preview pesan yang akan dikirim", expanded=True):
        st.text_area("Isi pesan", value=default_body, height=180, key="notification_message_body")
        st.text_input("Subjek email", value=default_subject, key="notification_email_subject")

    state = _enterprise_state()
    with st.form("notif_contacts"):
        st.markdown("**Tambah kontak penerima**")
        contact_name = st.text_input("Nama kontak / unit", placeholder="Manager Farm A / Grup Kandang 1")
        col_email, col_wa = st.columns(2)
        with col_email:
            email = st.text_input("Email", placeholder="nama@perusahaan.com")
        with col_wa:
            whatsapp = st.text_input("WhatsApp", placeholder="62812xxxxxxx atau 0812xxxxxxx")
        if st.form_submit_button("Simpan Kontak", width="stretch"):
            if contact_name.strip() or email.strip() or whatsapp.strip():
                state.setdefault("notification_contacts", []).append({
                    "name": contact_name.strip() or "Kontak",
                    "email": email.strip(),
                    "whatsapp": whatsapp.strip(),
                    "channel": "Email/WhatsApp",
                })
                _save_enterprise_state(state, "Tambah kontak notifikasi", contact_name.strip() or email.strip() or whatsapp.strip())
                st.success("Kontak notifikasi disimpan.")
            else:
                st.warning("Isi minimal nama, email, atau nomor WhatsApp.")

    contacts = state.get("notification_contacts", [])
    if contacts:
        st.markdown("### Kontak tersimpan")
        body = st.session_state.get("notification_message_body", default_body)
        subject = st.session_state.get("notification_email_subject", default_subject)
        for idx, item in enumerate(contacts):
            name = item.get("name") or item.get("contact") or f"Kontak {idx + 1}"
            email = item.get("email") or (item.get("contact") if str(item.get("channel", "")).lower() == "email" and "@" in str(item.get("contact", "")) else "")
            whatsapp = item.get("whatsapp") or (item.get("contact") if str(item.get("channel", "")).lower() == "whatsapp" else "")
            with st.container(border=True):
                st.markdown(f"**{name}**")
                meta = []
                if email:
                    meta.append(f"Email: `{email}`")
                if whatsapp:
                    meta.append(f"WhatsApp: `{whatsapp}`")
                if meta:
                    st.caption(" | ".join(meta))
                else:
                    st.caption("Kontak lama belum memiliki email/nomor WhatsApp. Edit dengan menambahkan kontak baru.")
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    if email:
                        _render_external_action_button("Kirim Email", _build_email_url(email, subject, body), "Membuka aplikasi email default.")
                    else:
                        st.button("Kirim Email", disabled=True, key=f"email_disabled_{idx}", width="stretch")
                with c2:
                    if whatsapp:
                        _render_external_action_button("Kirim WhatsApp", _build_whatsapp_url(whatsapp, body), "Membuka WhatsApp/Web WhatsApp.")
                    else:
                        st.button("Kirim WhatsApp", disabled=True, key=f"wa_disabled_{idx}", width="stretch")
                with c3:
                    if st.button("Hapus Kontak", key=f"delete_notif_contact_{idx}", width="stretch"):
                        contacts.pop(idx)
                        state["notification_contacts"] = contacts
                        _save_enterprise_state(state, "Hapus kontak notifikasi", name)
                        st.rerun()
    else:
        st.info("Belum ada kontak. Tambahkan email dan/atau nomor WhatsApp penerima terlebih dahulu.")


def render_audit_trail_center() -> None:
    st.subheader("Audit Trail Keputusan dan Data")
    state = _enterprise_state()
    if state.get("audit_trail"):
        st.dataframe(list(reversed(state["audit_trail"][-200:])), width="stretch", hide_index=True)
    else:
        st.info("Belum ada audit trail enterprise.")
    st.download_button("Download Laporan Enterprise Markdown", data=enterprise_report_markdown(normalise_profile(st.session_state.farm_profile), st.session_state.farm_records, st.session_state.farm_calendar_events, st.session_state.last_health_case, st.session_state.biosecurity_checked, state), file_name="laporan-enterprise-ai-pakar-ternak.md", mime="text/markdown", width="stretch")


def render_enterprise_center(selected_model_id: str, selected_fallback_models: List[str], selected_temperature: float, max_history_messages: int, prefer_ai: bool) -> None:
    st.header("Manajemen Enterprise")
    st.caption("Lapisan profesional untuk multi-farm, KPI, early warning, database permanen opsional, keuangan, knowledge base, hilirisasi, notifikasi, dan audit trail.")
    tabs = st.tabs(["Dashboard Direksi", "Multi-Farm", "Input Cepat", "KPI & Warning", "Keuangan", "Knowledge Base", "Hilirisasi", "Database", "Notifikasi", "Audit Trail"])
    with tabs[0]:
        render_executive_dashboard()
    with tabs[1]:
        render_multi_farm_batch()
    with tabs[2]:
        render_quick_daily_input()
    with tabs[3]:
        render_kpi_early_warning()
    with tabs[4]:
        render_finance_center()
    with tabs[5]:
        render_knowledge_base_center()
    with tabs[6]:
        render_downstream_center()
    with tabs[7]:
        render_database_sync_center()
    with tabs[8]:
        render_notification_center()
    with tabs[9]:
        render_audit_trail_center()

def render_tools_center() -> None:
    st.header("Alat Hitung")
    st.caption("Kalkulator sederhana untuk kebutuhan harian. Hasilnya dapat dipakai sebagai bahan konsultasi dan pencatatan.")
    tab_feed, tab_growth, tab_bep = st.tabs(["Kebutuhan Pakan", "Prediksi Pertumbuhan", "BEP"])
    with tab_feed:
        render_feed_calculator()
    with tab_growth:
        render_growth_prediction()
    with tab_bep:
        render_bep()


def render_learning_report_center() -> None:
    st.header("Edukasi & Laporan")
    st.caption("Bagian ini untuk membaca pengetahuan lokal, belajar bertahap, dan menyiapkan laporan yang dapat dibagikan.")
    tab_library, tab_breeds, tab_framework, tab_education, tab_report, tab_persona = st.tabs(["Library Lokal", "Komoditas & Bangsa", "5 Departemen", "Edukasi", "Laporan", "Aturan Pakar"])
    with tab_library:
        render_local_library()
    with tab_breeds:
        render_commodity_breed_catalog()
    with tab_framework:
        render_department_framework()
        render_department_coverage_panel()
    with tab_education:
        render_education()
    with tab_report:
        render_management_report()
    with tab_persona:
        render_expert_persona_reference()


def render_footer() -> None:
    st.markdown("---")
    st.markdown(
        "<div class='ptn-footer-card'>Developed by Galuh Adi Insani (Fakultas Peternakan UGM)</div>",
        unsafe_allow_html=True,
    )


init_state()

model_ids = [model["id"] for model in model_catalog]
default_model = client.model if client.model in model_ids else model_ids[0]
fallback_defaults = [model for model in client.fallback_models if model in model_ids]
if not fallback_defaults:
    fallback_defaults = [model_id for model_id in model_ids if model_id != default_model][:3]
max_history_messages_default = int(limits_config.get("max_history_messages", 16))

selected_model_id = default_model
selected_fallback_models = fallback_defaults
selected_temperature = float(client.temperature)
prefer_ai = True
max_history_messages = max_history_messages_default

st.title("🐄 AI Pakar Ternak")
st.caption("Asisten keputusan peternakan hulu–hilir: nutrisi, produksi, sosial-ekonomi, teknologi hasil, pemuliaan-reproduksi, insight, dan backup data.")
clear_prepared_downloads_if_stale()

with st.sidebar:
    st.header("Menu Utama")
    tool_option = st.selectbox(
        "Pilih alur kerja",
        APP_MODES,
        help="Menu dibuat ringkas agar peternak tidak bingung. Fitur detail ada di dalam tab setiap menu.",
    )

    p = normalise_profile(st.session_state.farm_profile)
    completeness = profile_completeness(p)
    st.caption(f"Profil: {p['population']} ekor {commodity_label(p['animal_type'])} · {p.get('breed', '-')} · {completeness}% lengkap")
    st.progress(completeness / 100)

    with st.expander("Preferensi Jawaban", expanded=False):
        st.session_state.user_mode = st.selectbox(
            "Tipe pengguna",
            USER_MODES,
            index=USER_MODES.index(st.session_state.user_mode) if st.session_state.user_mode in USER_MODES else 0,
            help="Peternak Rakyat memakai bahasa lebih sederhana. Industri Modern memakai KPI, SOP, dan istilah manajerial.",
        )
        st.session_state.explanation_level = st.selectbox(
            "Kedalaman penjelasan",
            EXPLANATION_LEVELS,
            index=EXPLANATION_LEVELS.index(st.session_state.explanation_level) if st.session_state.explanation_level in EXPLANATION_LEVELS else 1,
        )
        ent_state = normalise_enterprise_state(st.session_state.enterprise_state)
        selected_role = st.selectbox(
            "Role operasional",
            ROLE_OPTIONS,
            index=ROLE_OPTIONS.index(ent_state.get("current_role")) if ent_state.get("current_role") in ROLE_OPTIONS else 0,
            help="Role ini mengubah gaya insight: direksi lebih strategis, petugas lebih instruksi lapangan.",
        )
        ent_state["current_role"] = selected_role
        st.session_state.enterprise_state = ent_state
        st.caption(ROLE_DESCRIPTIONS.get(selected_role, ""))

    with st.expander("Backup XLSX", expanded=False):
        st.caption("Unduh XLSX agar data tetap bisa dibaca tanpa aplikasi dan bisa dipulihkan lagi.")
        st.info("Agar perpindahan dropdown/menu lebih responsif, file backup dibuat hanya saat tombol di bawah ditekan.")
        try:
            if st.button("Siapkan / Perbarui File Backup", width="stretch", key="prepare_sidebar_backup"):
                with st.spinner("Menyiapkan XLSX dan PDF..."):
                    prepare_download_files(include_pdf=True)
                st.success("File backup siap diunduh.")
            if st.session_state.get("prepared_download_hash") and st.session_state.get("prepared_xlsx_bytes"):
                st.download_button(
                    "Download Backup XLSX",
                    data=st.session_state.prepared_xlsx_bytes,
                    file_name=st.session_state.prepared_xlsx_name or "ai-pakar-ternak-backup.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                    key="sidebar_download_xlsx_prepared",
                )
                if st.session_state.get("prepared_pdf_bytes"):
                    st.download_button(
                        "Download Laporan PDF",
                        data=st.session_state.prepared_pdf_bytes,
                        file_name=st.session_state.prepared_pdf_name or "ai-pakar-ternak-laporan.pdf",
                        mime="application/pdf",
                        width="stretch",
                        key="sidebar_download_pdf_report",
                    )
            elif st.session_state.get("prepared_xlsx_bytes"):
                st.warning("Data berubah setelah backup disiapkan. Klik 'Siapkan / Perbarui File Backup' agar file terbaru dibuat.")
        except Exception as error:
            st.error(f"Gagal membuat backup/laporan: {error}")

        restore_file = st.file_uploader("Pulihkan dari XLSX", type=["xlsx"], key="restore_xlsx_file")
        if st.button("Pulihkan Data", width="stretch", disabled=restore_file is None):
            try:
                restored = import_session_xlsx(restore_file)
                restore_session_from_payload(restored)
                autosave_session_xlsx()
                st.success("Data berhasil dipulihkan dari XLSX.")
                safe_rerun()
            except Exception as error:
                st.error(f"Gagal memulihkan XLSX: {error}")

        if st.session_state.last_autosave_at:
            st.caption(f"Autosave terakhir: {st.session_state.last_autosave_at}")
        if st.session_state.last_autosave_error:
            st.warning(f"Autosave gagal: {st.session_state.last_autosave_error}")
        st.caption("Di Streamlit Online, backup utama tetap file XLSX yang diunduh peternak.")

    with st.expander("Data & Admin", expanded=False):
        st.warning(
            "Sebelum menghapus/reset data, pastikan database sesi sudah di-download sebagai Backup XLSX. "
            "Tanpa file backup, data dapat hilang ketika session Streamlit habis atau app restart."
        )
        try:
            if st.button("Siapkan Database XLSX Sebelum Hapus", width="stretch", key="prepare_before_delete_xlsx"):
                with st.spinner("Menyiapkan database XLSX..."):
                    prepare_download_files(include_pdf=False)
                st.success("Database XLSX siap diunduh. Download sebelum melakukan reset/hapus.")
            if st.session_state.get("prepared_download_hash") and st.session_state.get("prepared_xlsx_bytes"):
                st.download_button(
                    "Download Database XLSX Sebelum Hapus",
                    data=st.session_state.prepared_xlsx_bytes,
                    file_name=st.session_state.prepared_xlsx_name or "ai-pakar-ternak-backup.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                    key="download_before_delete_xlsx",
                )
            else:
                st.caption("Klik tombol siapkan database terlebih dahulu. File tidak dibuat otomatis supaya dropdown/menu lebih cepat.")
        except Exception as error:
            st.error(f"Gagal membuat backup sebelum hapus: {error}")

        if st.session_state.reset_notice:
            st.success(st.session_state.reset_notice)

        st.markdown("**Apakah database sudah Anda download?**")
        reset_chat_key = f"confirm_reset_chat_downloaded_{st.session_state.confirm_reset_chat_nonce}"
        reset_chat_confirm = st.checkbox(
            "Ya, saya sudah download database XLSX sebelum Reset Chat.",
            key=reset_chat_key,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Reset Chat", width="stretch", disabled=not reset_chat_confirm):
                reset_chat()
                st.session_state.confirm_reset_chat_nonce += 1
                st.session_state.reset_notice = "Chat berhasil direset. Data dapat dipulihkan dari backup XLSX yang sudah diunduh."
                safe_rerun()
        with col_b:
            st.download_button(
                "Download JSON",
                data=export_app_json(),
                file_name="ai-pakar-ternak-data.json",
                mime="application/json",
                width="stretch",
            )

        if st.session_state.admin_authenticated:
            st.divider()
            st.markdown("**Hapus/reset data farm hanya untuk admin.**")
            reset_farm_key = f"confirm_reset_farm_downloaded_{st.session_state.confirm_reset_farm_nonce}"
            reset_farm_confirm = st.checkbox(
                "Ya, saya sudah download database XLSX sebelum Reset Data Farm.",
                key=reset_farm_key,
            )
            if st.button("Reset Data Farm", width="stretch", disabled=not reset_farm_confirm):
                reset_farm_data()
                st.session_state.confirm_reset_farm_nonce += 1
                st.session_state.reset_notice = "Data farm berhasil direset. Gunakan file XLSX untuk memulihkan data lama bila diperlukan."
                safe_rerun()

        (
            selected_model_id,
            selected_fallback_models,
            selected_temperature,
            prefer_ai,
            max_history_messages,
        ) = render_admin_panel(model_ids, default_model, fallback_defaults, max_history_messages_default)

if tool_option == "Beranda":
    safe_render("Beranda", render_simple_home)
elif tool_option == "Input Data":
    safe_render("Input Data", render_input_data_center)
elif tool_option == "Konsultasi AI":
    safe_render("Konsultasi AI", render_consultation_center, selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
elif tool_option == "Insight & Keputusan":
    safe_render("Insight & Keputusan", render_decision_center, selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
elif tool_option == "Manajemen Enterprise":
    safe_render("Manajemen Enterprise", render_enterprise_center, selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
elif tool_option == "Database Supabase":
    safe_render("Database Supabase", render_database_supabase_page)
elif tool_option == "Alat Hitung":
    safe_render("Alat Hitung", render_tools_center)
elif tool_option == "Edukasi & Laporan":
    safe_render("Edukasi & Laporan", render_learning_report_center)

try:
    autosave_session_xlsx()
except Exception as error:
    if st.session_state.get("admin_authenticated", False):
        st.warning(f"Autosave tidak berhasil: {error}")

try:
    render_footer()
except Exception:
    st.caption("Developed by Galuh Adi Insani (Fakultas Peternakan UGM)")
