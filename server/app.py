from __future__ import annotations

import inspect
import json
import os
import tempfile
import traceback
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
from expert_rules import (
    build_expert_context,
    decision_card_from_answer,
    farm_risk_score,
    rewrite_instruction,
    TECHNICAL_GLOSSARY,
    COMMODITY_TEMPLATES,
)

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
        },
    )


def export_app_json() -> str:
    payload = build_current_session_payload()
    return json.dumps(payload, ensure_ascii=False, indent=2)


def get_session_xlsx_bytes() -> bytes:
    return export_session_xlsx(build_current_session_payload())


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
    }


def get_session_pdf_bytes() -> bytes:
    return generate_pdf_report(build_current_session_payload(), build_pdf_report_context())


def autosave_session_xlsx() -> None:
    try:
        payload = build_current_session_payload()
        filename = session_filename(payload)
        path = SESSION_BACKUP_DIR / filename
        export_session_xlsx(payload, path)
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
        "extra_context": (audience_context(st.session_state.user_mode, st.session_state.explanation_level) + "\n" + expert_context + "\n" + extra_context).strip(),
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
            with st.spinner("Menyusun ulang jawaban..."):
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
            with st.spinner("AI sedang menyusun insight manajemen farm..."):
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
            animal = st.selectbox("Jenis ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0)
            goal = st.selectbox("Tujuan usaha", PRODUCTION_GOALS, index=PRODUCTION_GOALS.index(p["production_goal"]) if p["production_goal"] in PRODUCTION_GOALS else 0)
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
            with st.spinner("AI Pakar Ternak sedang menganalisis..."):
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
            animal = st.selectbox("Jenis ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="health_animal")
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
        with st.spinner("Meminta analisis AI pakar kesehatan ternak..."):
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
    animal = col1.selectbox("Jenis ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="feed_animal")
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

    if animal in {"sapi", "kambing"}:
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
    animal = col3.selectbox("Jenis ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="calendar_animal")
    phase = st.text_input("Fase ternak", value=p.get("phase", ""), key="calendar_phase")

    if st.button("Buat jadwal otomatis", width="stretch"):
        st.session_state.farm_calendar_events = generate_management_events(animal, start_date, int(days), phase)
        st.success("Kalender manajemen dibuat dan akan menjadi konteks AI.")

    if animal in {"sapi", "kambing", "kelinci"}:
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
        animal_type = st.selectbox("Jenis ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="calc_animal")
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
        animal_type = st.selectbox("Jenis ternak", ANIMAL_TYPES, index=ANIMAL_TYPES.index(p["animal_type"]) if p["animal_type"] in ANIMAL_TYPES else 0, key="growth_animal")
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
            with st.spinner("AI menyusun konsultasi bertahap..."):
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
        with st.spinner("AI menganalisis KPI farm..."):
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
            with st.spinner("AI menyesuaikan SOP dengan profil farm..."):
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
            with st.spinner("AI membuat rekomendasi dari prediksi..."):
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
    report = f"""
# Laporan Manajemen AI Pakar Ternak

Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Profil Farm
- Nama: {profile.get('farm_name') or '-'}
- Komoditas: {profile.get('animal_type')} | Tujuan: {profile.get('production_goal')} | Fase: {profile.get('phase')}
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

## Rekomendasi Singkat
1. Lengkapi profil dan recording jika masih kosong.
2. Timbang/estimasi pakan dan bobot secara berkala agar ADG dan FCR terbaca.
3. Prioritaskan biosecurity, isolasi ternak sakit, dan kebersihan tempat pakan-minum.
4. Gunakan backup XLSX setelah setiap sesi penting.

Developed by Galuh Adi Insani
""".strip()
    st.markdown(report)
    report_payload = build_current_session_payload()
    report_context = build_pdf_report_context()
    col_pdf, col_md, col_xlsx = st.columns(3)
    with col_pdf:
        try:
            st.download_button(
                "Download Laporan PDF",
                data=generate_pdf_report(report_payload, report_context),
                file_name=pdf_report_filename(report_payload),
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
            st.download_button(
                "Download Backup Lengkap XLSX",
                data=get_session_xlsx_bytes(),
                file_name=session_filename(report_payload),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
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
    tab_guided, tab_chat, tab_health = st.tabs(["Konsultasi Bertahap", "Chat Pakar", "Triase Kesehatan"])
    with tab_guided:
        render_guided_consultation(selected_model_id, selected_fallback_models, selected_temperature, max_history_messages, prefer_ai)
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
    tab_insight, tab_feed, tab_kpi, tab_prediction, tab_sop, tab_log = st.tabs([
        "AI Insight",
        "Formulasi Pakan",
        "Benchmark KPI",
        "Prediksi Usaha",
        "SOP & Biosecurity",
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
    with tab_log:
        render_decision_log()


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
    tab_library, tab_education, tab_report, tab_persona = st.tabs(["Library Lokal", "Edukasi", "Laporan", "Aturan Pakar"])
    with tab_library:
        render_local_library()
    with tab_education:
        render_education()
    with tab_report:
        render_management_report()
    with tab_persona:
        render_expert_persona_reference()


def render_footer() -> None:
    st.markdown("---")
    st.markdown(
        "<div class='ptn-footer-card'>Developed by Galuh Adi Insani</div>",
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
st.caption("Asisten keputusan peternakan: isi data, konsultasi, baca insight, lalu simpan backup XLSX.")

with st.sidebar:
    st.header("Menu Utama")
    tool_option = st.selectbox(
        "Pilih alur kerja",
        APP_MODES,
        help="Menu dibuat ringkas agar peternak tidak bingung. Fitur detail ada di dalam tab setiap menu.",
    )

    p = normalise_profile(st.session_state.farm_profile)
    completeness = profile_completeness(p)
    st.caption(f"Profil: {p['population']} ekor {p['animal_type']} · {completeness}% lengkap")
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

    with st.expander("Backup XLSX", expanded=False):
        st.caption("Unduh XLSX agar data tetap bisa dibaca tanpa aplikasi dan bisa dipulihkan lagi.")
        try:
            xlsx_payload = build_current_session_payload()
            st.download_button(
                "Download Backup XLSX",
                data=export_session_xlsx(xlsx_payload),
                file_name=session_filename(xlsx_payload),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
            st.download_button(
                "Download Laporan PDF",
                data=generate_pdf_report(xlsx_payload, build_pdf_report_context()),
                file_name=pdf_report_filename(xlsx_payload),
                mime="application/pdf",
                width="stretch",
                key="sidebar_download_pdf_report",
            )
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
            confirm_payload = build_current_session_payload()
            st.download_button(
                "Download Database XLSX Sebelum Hapus",
                data=export_session_xlsx(confirm_payload),
                file_name=session_filename(confirm_payload),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                key="download_before_delete_xlsx",
            )
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
    st.caption("Developed by Galuh Adi Insani")
