from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from calculators import calculate_bep, calculate_feed_needs, predict_growth, rupiah
from chat_router import answer_message
from domain_data import ANIMAL_TYPES, DEFAULT_WEIGHTS, FEED_RATES
from model_catalog import format_model_option, format_rupiah, get_model_by_id, load_model_catalog
from openai_integration import DEFAULT_CONFIG, OpenAIChatAPI

PROJECT_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Pakar Ternak Nusantara",
    page_icon="🐄",
    layout="centered",
    initial_sidebar_state="expanded",
)

client = OpenAIChatAPI()
model_catalog = load_model_catalog()
limits_config = client.config.get("limits", DEFAULT_CONFIG["limits"])
ui_config = client.config.get("ui", DEFAULT_CONFIG["ui"])


def init_state() -> None:
    defaults = {
        "messages": [],
        "last_meta": {},
        "session_request_count": 0,
        "session_prompt_tokens": 0,
        "session_completion_tokens": 0,
        "session_total_tokens": 0,
        "session_estimated_cost_rp": 0.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.last_meta = {}
    st.session_state.session_request_count = 0
    st.session_state.session_prompt_tokens = 0
    st.session_state.session_completion_tokens = 0
    st.session_state.session_total_tokens = 0
    st.session_state.session_estimated_cost_rp = 0.0


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


def export_chat_json() -> str:
    payload = {
        "app": "Pakar Ternak Nusantara",
        "messages": st.session_state.messages,
        "usage": {
            "requests": st.session_state.session_request_count,
            "prompt_tokens": st.session_state.session_prompt_tokens,
            "completion_tokens": st.session_state.session_completion_tokens,
            "total_tokens": st.session_state.session_total_tokens,
            "estimated_cost_rp": round(st.session_state.session_estimated_cost_rp, 6),
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


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


init_state()

st.title("🐄 Pakar Ternak Nusantara")
st.caption("Asisten AI peternakan dengan persona konsultan kandang: pakan, kesehatan, reproduksi, produksi, limbah, dan analisis usaha.")

with st.sidebar:
    st.header("Status AI")
    if client.is_configured:
        st.success("API aktif")
    else:
        st.warning("API belum aktif")
        st.caption(client.status_reason)
    st.caption(f"Sumber API key: {client.api_key_source}")

    model_ids = [model["id"] for model in model_catalog]
    default_model = client.model if client.model in model_ids else model_ids[0]
    selected_model_id = st.selectbox(
        "Model awal",
        options=model_ids,
        index=model_ids.index(default_model),
        format_func=lambda model_id: format_model_option(get_model_by_id(model_id, model_catalog)),
        help="Setiap pertanyaan selalu mulai dari model awal ini. Jika gagal, sistem naik ke fallback lalu kembali lagi ke model awal pada pertanyaan berikutnya.",
    )
    fallback_defaults = [model for model in client.fallback_models if model in model_ids]
    selected_fallback_models = st.multiselect(
        "Fallback model",
        options=model_ids,
        default=fallback_defaults,
        format_func=lambda model_id: format_model_option(get_model_by_id(model_id, model_catalog)),
    )
    st.session_state.selected_model_id = selected_model_id
    st.session_state.selected_fallback_models = selected_fallback_models
    st.session_state.selected_temperature = st.slider("Temperature", 0.0, 1.5, float(client.temperature), 0.05)
    prefer_ai = st.toggle("Gunakan AI untuk pertanyaan peternakan", value=True)
    max_history_messages = int(limits_config.get("max_history_messages", 16))

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

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Reset chat", use_container_width=True):
            reset_chat()
            st.rerun()
    with col_b:
        st.download_button(
            "Ekspor JSON",
            data=export_chat_json(),
            file_name="riwayat-chat-ternak.json",
            mime="application/json",
            use_container_width=True,
        )

    if st.button("Tes koneksi API", use_container_width=True):
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

    st.divider()
    tool_option = st.selectbox("Mode", ["Chat Pakar", "Kalkulator Pakan", "Prediksi Pertumbuhan", "Analisis BEP"])

if tool_option == "Chat Pakar":
    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input("Tanyakan masalah peternakan Anda...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if usage_limit_reached():
                response = (
                    "Batas pemakaian sesi sudah tercapai. Tekan Reset chat untuk memulai sesi baru, "
                    "atau naikkan batas di config.toml bagian [limits]."
                )
                meta: Dict[str, Any] = {"source": "limit"}
                st.warning(response)
            else:
                with st.spinner("Pakar Ternak Nusantara sedang menganalisis..."):
                    response, meta = answer_message(
                        message=prompt,
                        history=st.session_state.messages[:-1],
                        client=client,
                        selected_model=selected_model_id,
                        fallback_models=selected_fallback_models,
                        temperature=st.session_state.selected_temperature,
                        max_history_messages=max_history_messages,
                        models_catalog=model_catalog,
                        prefer_ai=prefer_ai,
                    )
                st.markdown(response)
                update_usage(meta)

                if bool(ui_config.get("show_model_trace", True)) and meta.get("source") == "ai":
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

        st.session_state.last_meta = meta
        st.session_state.messages.append({"role": "assistant", "content": response})

elif tool_option == "Kalkulator Pakan":
    st.header("Kalkulator Kebutuhan Pakan")
    col1, col2 = st.columns(2)
    with col1:
        animal_type = st.selectbox("Jenis ternak", ANIMAL_TYPES)
        count = st.number_input("Jumlah ternak (ekor)", min_value=1, value=10)
    with col2:
        weight = st.number_input("Berat rata-rata (kg)", min_value=0.1, value=float(DEFAULT_WEIGHTS.get(animal_type, 1.0)), step=0.1)
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

elif tool_option == "Prediksi Pertumbuhan":
    st.header("Prediksi Pertumbuhan Ternak")
    col1, col2 = st.columns(2)
    with col1:
        animal_type = st.selectbox("Jenis ternak", ANIMAL_TYPES)
        initial_weight = st.number_input("Berat awal (kg)", min_value=0.1, value=1.0, step=0.1)
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

elif tool_option == "Analisis BEP":
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

st.markdown("---")
st.caption("© 2026 Pakar Ternak Nusantara — AI peternakan untuk edukasi, manajemen, dan analisis usaha. Untuk penyakit berat, tetap konsultasikan dokter hewan/tenaga kesehatan hewan setempat.")
