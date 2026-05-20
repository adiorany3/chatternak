from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
import random

from calculators import detect_tool_response
from domain_data import DOMAIN_TERMS, FARMING_KNOWLEDGE, INTENTS
from persona import SHORT_CONTEXT, SYSTEM_PROMPT, OFF_DOMAIN_RESPONSE
from expert_rules import validate_ai_answer, repair_prompt
from openai_integration import OpenAIChatAPI
from model_catalog import estimate_cost_rp
from farm_profile import make_profile_context
from farm_records import records_context
from farm_calendar import calendar_context
from ugm_departments import department_context, department_prompt_for_text


def is_domain_related(message: str) -> bool:
    text = message.lower()
    return any(term in text for term in DOMAIN_TERMS)


def get_intent_response(message: str) -> str | None:
    text = message.lower().strip()
    for intent in ("greeting", "thanks", "bye"):
        for pattern in INTENTS[intent]["patterns"]:
            if pattern in text:
                return random.choice(INTENTS[intent]["responses"])
    return None


def get_local_knowledge_response(message: str) -> str | None:
    text = message.lower().strip()
    for topic, data in FARMING_KNOWLEDGE.items():
        if topic not in text:
            continue
        if any(word in text for word in ("jenis", "tipe", "macam", "populer", "jenis-jenis")):
            return data.get("jenis") or data.get("info")
        if any(word in text for word in ("perawatan", "merawat", "cara merawat", "manajemen")):
            return data.get("perawatan") or data.get("info")
        if any(word in text for word in ("pakan", "makan", "ransum", "hijauan", "konsentrat")):
            return data.get("pakan") or data.get("info")
        if any(word in text for word in ("reproduksi", "beranak", "kawin", "bunting", "birahi", "ib", "inseminasi")):
            return data.get("reproduksi") or data.get("info")
        if any(word in text for word in ("penyakit", "sakit", "virus", "bakteri", "diare", "cacing")):
            return data.get("penyakit") or data.get("info")
        if any(word in text for word in ("produksi", "hasil", "produktivitas", "panen")):
            return data.get("produksi") or data.get("info")
        if any(word in text for word in ("kolam", "kandang", "habitat")):
            return data.get("kolam") or data.get("kandang") or data.get("perawatan") or data.get("info")
        if len(text.split()) <= 4:
            return data.get("info")
    return None


def get_utility_response(message: str) -> str | None:
    text = message.lower()
    if any(kw in text for kw in ("tanggal", "hari ini", "waktu", "jam")):
        now = datetime.now()
        return f"Sekarang {now.strftime('%d-%m-%Y')} pukul {now.strftime('%H:%M:%S')}. Untuk manajemen ternak, gunakan tanggal ini sebagai patokan recording harian."
    if any(kw in text for kw in ("siapa pembuatmu", "siapa yang membuatmu", "siapa creator", "dibuat oleh")):
        return "Chatbot ini dikembangkan oleh Galuh Adi Insani (Fakultas Peternakan UGM) sebagai asisten peternakan berbasis AI."
    return None


def build_messages(
    user_message: str,
    history: List[Dict[str, str]],
    max_history_messages: int = 16,
    profile: Dict[str, Any] | None = None,
    records: List[Dict[str, Any]] | None = None,
    calendar_events: List[Dict[str, Any]] | None = None,
    extra_context: str = "",
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": SHORT_CONTEXT},
        {"role": "system", "content": department_context()},
        {"role": "system", "content": department_prompt_for_text(user_message)},
    ]
    if profile:
        messages.append({"role": "system", "content": make_profile_context(profile)})
    if records is not None:
        messages.append({"role": "system", "content": records_context(records)})
    if calendar_events is not None:
        messages.append({"role": "system", "content": calendar_context(calendar_events)})
    if extra_context.strip():
        messages.append({"role": "system", "content": extra_context.strip()})
    cleaned_history = [
        {"role": item.get("role", "user"), "content": str(item.get("content", ""))}
        for item in history[-max_history_messages:]
        if item.get("role") in {"user", "assistant"} and str(item.get("content", "")).strip()
    ]
    messages.extend(cleaned_history)
    messages.append({"role": "user", "content": user_message})
    return messages


def answer_message(
    message: str,
    history: List[Dict[str, str]],
    client: OpenAIChatAPI,
    selected_model: str,
    fallback_models: List[str],
    temperature: float,
    max_history_messages: int,
    models_catalog: List[Dict[str, Any]],
    prefer_ai: bool = True,
    profile: Dict[str, Any] | None = None,
    records: List[Dict[str, Any]] | None = None,
    calendar_events: List[Dict[str, Any]] | None = None,
    extra_context: str = "",
    user_mode: str = "Peternak Rakyat",
    **_: Any,
) -> Tuple[str, Dict[str, Any]]:
    """Router utama chat.

    Prinsip:
    - Greeting/thanks/bye dan hitung eksplisit dijawab lokal agar cepat dan hemat.
    - Semua pertanyaan domain peternakan diarahkan ke AI jika API aktif, dengan riwayat chat.
    - Jika API gagal, fallback ke basis pengetahuan lokal.
    """
    meta: Dict[str, Any] = {"source": "local", "attempts": [], "model": "", "usage": {}, "cost_rp": 0.0}

    intent = get_intent_response(message)
    if intent:
        return intent, meta

    tool_response = detect_tool_response(message)
    if tool_response:
        meta["source"] = "tool"
        return tool_response, meta

    utility = get_utility_response(message)
    if utility:
        return utility, meta

    should_use_ai = prefer_ai and client.is_configured
    if should_use_ai:
        messages = build_messages(
            message,
            history,
            max_history_messages=max_history_messages,
            profile=profile,
            records=records,
            calendar_events=calendar_events,
            extra_context=extra_context,
        )
        result = client.generate_chat_completion_with_fallback(
            messages=messages,
            temperature=temperature,
            model=selected_model,
            max_tokens=client.max_tokens,
            fallback_models=fallback_models,
        )
        meta["attempts"] = result.get("attempts", [])
        meta["model"] = result.get("model", "")
        api_result = result.get("result")
        if api_result:
            meta["usage"] = api_result.usage
            meta["cost_rp"] = estimate_cost_rp(
                meta["model"],
                prompt_tokens=api_result.prompt_tokens,
                completion_tokens=api_result.completion_tokens,
                models=models_catalog,
            )
        if result.get("success") and result.get("content"):
            content = result["content"]
            ok, issues = validate_ai_answer(content, message, user_mode)
            meta["validation"] = {"ok": ok, "issues": issues, "repaired": False}
            if not ok and len(content) < 6000:
                repair_messages = build_messages(
                    repair_prompt(message, content, issues, user_mode),
                    history,
                    max_history_messages=max_history_messages,
                    profile=profile,
                    records=records,
                    calendar_events=calendar_events,
                    extra_context=extra_context,
                )
                repair_result = client.generate_chat_completion_with_fallback(
                    messages=repair_messages,
                    temperature=temperature,
                    model=selected_model,
                    max_tokens=client.max_tokens,
                    fallback_models=fallback_models,
                )
                meta["repair_attempts"] = repair_result.get("attempts", [])
                repair_api_result = repair_result.get("result")
                if repair_result.get("success") and repair_result.get("content"):
                    content = repair_result["content"]
                    meta["validation"] = {"ok": True, "issues": issues, "repaired": True}
                    if repair_api_result:
                        # Add repair tokens to the displayed usage/cost approximation.
                        base_usage = dict(meta.get("usage", {}) or {})
                        base_usage["prompt_tokens"] = int(base_usage.get("prompt_tokens", 0) or 0) + int(repair_api_result.prompt_tokens or 0)
                        base_usage["completion_tokens"] = int(base_usage.get("completion_tokens", 0) or 0) + int(repair_api_result.completion_tokens or 0)
                        base_usage["total_tokens"] = int(base_usage.get("total_tokens", 0) or 0) + int(repair_api_result.total_tokens or 0)
                        meta["usage"] = base_usage
                        meta["cost_rp"] = estimate_cost_rp(
                            meta["model"],
                            prompt_tokens=int(base_usage.get("prompt_tokens", 0) or 0),
                            completion_tokens=int(base_usage.get("completion_tokens", 0) or 0),
                            models=models_catalog,
                        )
            meta["source"] = "ai"
            return content, meta
        meta["api_error"] = result.get("content", "API tidak berhasil memberikan jawaban.")

    local = get_local_knowledge_response(message)
    if local:
        meta["source"] = "local_knowledge"
        if should_use_ai:
            local += "\n\nCatatan: AI tidak berhasil menjawab, sehingga sistem memakai basis pengetahuan lokal."
        return local, meta

    if not client.is_configured:
        return (
            "API belum aktif. Saya tetap bisa membantu secara terbatas dari basis pengetahuan lokal. "
            "Silakan tanya tentang sapi, kambing, ayam, bebek, ikan, kelinci, pakan, kandang, penyakit, reproduksi, pupuk, atau analisis usaha.",
            meta,
        )

    if not is_domain_related(message):
        return OFF_DOMAIN_RESPONSE, meta

    return (
        "Pertanyaan belum cukup jelas untuk saya jawab sebagai konsultan peternakan. "
        "Sebutkan jenis ternak, umur/bobot, jumlah populasi, kondisi kandang/kolam, pakan yang diberikan, dan gejala/target usaha.",
        meta,
    )
