from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import os

import requests

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

PROJECT_DIR = Path(__file__).resolve().parent

DEFAULT_CONFIG: Dict[str, Any] = {
    "openai": {
        "enabled": True,
        "api_key": "",
        "chat_completions_url": "https://api.slashai.my.id/v1/chat/completions",
        "model": "slashai/gpt-5-nano",
        "fallback_models": [
            "slashai/gpt-5-mini",
            "slashai/claude-haiku-4.5",
            "slashai/gemini-3-flash",
            "slashai/deepseek-v3.2",
        ],
        "smart_fallback_enabled": True,
        "temperature": 0.45,
        "max_tokens": 2200,
        "test_max_tokens": 250,
        "timeout": 75,
        "min_answer_chars": 45,
    },
    "limits": {
        "enabled": True,
        "max_requests_per_session": 60,
        "max_estimated_cost_rp_per_session": 2500,
        "max_history_messages": 16,
    },
    "ui": {
        "show_debug": False,
        "show_cost": True,
        "show_model_trace": True,
    },
}

PLACEHOLDER_KEYS = {
    "",
    "ISI_API_KEY_ANDA",
    "ISI_API_KEY_ANDA_DI_SINI",
    "PASTE_API_KEY_HERE",
    "YOUR_API_KEY_HERE",
    "YOUR_SLASHAI_API_KEY_HERE",
}

ROOT_SECRET_ALIASES = {
    "api_key": ("OPENAI_API_KEY", "SLASHAI_API_KEY"),
    "chat_completions_url": ("OPENAI_CHAT_COMPLETIONS_URL", "SLASHAI_CHAT_COMPLETIONS_URL"),
    "model": ("OPENAI_MODEL", "SLASHAI_MODEL"),
}

ENV_FALLBACK_KEYS = ("OPENAI_FALLBACK_MODELS", "SLASHAI_FALLBACK_MODELS")

UNHELPFUL_PATTERNS = (
    "maaf, saya tidak dapat",
    "maaf saya tidak dapat",
    "saya tidak dapat membantu",
    "saya tidak bisa membantu",
    "i can't help",
    "i cannot help",
    "as an ai",
    "sebagai ai",
    "tidak memiliki informasi",
    "tidak punya informasi",
    "di luar konteks",
    "outside the context",
    "i don't have access",
)

DOMAIN_TERMS = (
    "ternak", "peternakan", "sapi", "kambing", "domba", "ayam", "bebek", "itik", "ikan", "kelinci",
    "pakan", "kandang", "kolam", "vaksin", "penyakit", "reproduksi", "bunting", "birahi",
    "inseminasi", "pupuk", "kompos", "biogas", "bep", "modal", "produksi", "ransum", "hijauan",
)


@dataclass
class ChatResult:
    success: bool
    content: str = ""
    model: str = ""
    finish_reason: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    raw_preview: str = ""
    error: str = ""

    @property
    def prompt_tokens(self) -> int:
        return int(self.usage.get("prompt_tokens", 0) or self.usage.get("input_tokens", 0) or 0)

    @property
    def completion_tokens(self) -> int:
        return int(self.usage.get("completion_tokens", 0) or self.usage.get("output_tokens", 0) or 0)

    @property
    def total_tokens(self) -> int:
        return int(self.usage.get("total_tokens", self.prompt_tokens + self.completion_tokens) or 0)


class OpenAIChatAPI:
    """Client untuk endpoint OpenAI-compatible Chat Completions.

    Prioritas API key:
    1. Environment variable OPENAI_API_KEY / SLASHAI_API_KEY
    2. Streamlit Secrets [openai] api_key
    3. config.toml api_key hanya fallback legacy
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = self._resolve_config_path(config_path)
        self.config_error: Optional[str] = None
        self.config = self._load_config()
        self.streamlit_secrets = self._load_streamlit_secrets()

        settings = self.config.get("openai", {})
        secret_settings = self.streamlit_secrets.get("openai", {})

        env_api_key = (os.getenv("OPENAI_API_KEY") or os.getenv("SLASHAI_API_KEY") or "").strip()
        secret_api_key = str(secret_settings.get("api_key", "")).strip()
        config_api_key = str(settings.get("api_key", "")).strip()

        self.enabled = self._get_bool_setting("enabled", settings, secret_settings)
        self.api_key = env_api_key or secret_api_key or config_api_key
        self.api_key_source = self._detect_api_key_source(env_api_key, secret_api_key, config_api_key)
        self.chat_completions_url = str(self._get_setting("chat_completions_url", settings, secret_settings)).strip()
        self.model = str(self._get_setting("model", settings, secret_settings)).strip()
        self.fallback_models = self._get_fallback_models(settings, secret_settings)
        self.smart_fallback_enabled = self._get_bool_setting("smart_fallback_enabled", settings, secret_settings)
        self.temperature = float(self._get_setting("temperature", settings, secret_settings))
        self.max_tokens = int(self._get_setting("max_tokens", settings, secret_settings))
        self.test_max_tokens = int(self._get_setting("test_max_tokens", settings, secret_settings))
        self.timeout = int(self._get_setting("timeout", settings, secret_settings))
        self.min_answer_chars = int(self._get_setting("min_answer_chars", settings, secret_settings))

    @staticmethod
    def _resolve_config_path(config_path: str | Path | None) -> Path:
        if config_path is None:
            return PROJECT_DIR / "config.toml"
        path = Path(config_path)
        return path if path.is_absolute() else PROJECT_DIR / path

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return deepcopy(DEFAULT_CONFIG)
        try:
            with self.config_path.open("rb") as file:
                loaded = tomllib.load(file)
        except Exception as error:
            self.config_error = f"Gagal membaca config.toml: {error}"
            return deepcopy(DEFAULT_CONFIG)

        merged = deepcopy(DEFAULT_CONFIG)
        for section in ("openai", "limits", "ui"):
            merged[section] = {**DEFAULT_CONFIG.get(section, {}), **loaded.get(section, {})}
        return merged

    @staticmethod
    def _safe_dict(value: Any) -> Dict[str, Any]:
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

    def _load_streamlit_secrets(self) -> Dict[str, Any]:
        try:
            import streamlit as st
        except Exception:
            return {"openai": {}}
        try:
            openai_section = self._safe_dict(st.secrets.get("openai", {}))
            for canonical_key, aliases in ROOT_SECRET_ALIASES.items():
                if canonical_key in openai_section and str(openai_section[canonical_key]).strip():
                    continue
                for alias in aliases:
                    try:
                        alias_value = st.secrets.get(alias, "")
                    except Exception:
                        alias_value = ""
                    if str(alias_value).strip():
                        openai_section[canonical_key] = alias_value
                        break
            return {"openai": openai_section}
        except Exception:
            return {"openai": {}}

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value).strip().lower() not in {"false", "0", "no", "off", "tidak"}

    def _get_setting(self, key: str, config_settings: Dict[str, Any], secret_settings: Dict[str, Any]) -> Any:
        if key in secret_settings and str(secret_settings.get(key, "")).strip() != "":
            return secret_settings[key]
        return config_settings.get(key, DEFAULT_CONFIG["openai"].get(key))

    def _get_bool_setting(self, key: str, config_settings: Dict[str, Any], secret_settings: Dict[str, Any]) -> bool:
        return self._coerce_bool(self._get_setting(key, config_settings, secret_settings))

    @staticmethod
    def _split_models(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.replace("\n", ",").split(",") if item.strip()]
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    def _get_fallback_models(self, config_settings: Dict[str, Any], secret_settings: Dict[str, Any]) -> List[str]:
        env_value = ""
        for key in ENV_FALLBACK_KEYS:
            if os.getenv(key):
                env_value = os.getenv(key, "")
                break
        models = self._split_models(env_value) or self._split_models(secret_settings.get("fallback_models")) or self._split_models(config_settings.get("fallback_models"))
        cleaned: List[str] = []
        for model in models:
            if model and model not in cleaned:
                cleaned.append(model)
        return cleaned

    @staticmethod
    def _detect_api_key_source(env_api_key: str, secret_api_key: str, config_api_key: str) -> str:
        if env_api_key and env_api_key not in PLACEHOLDER_KEYS:
            return "Environment variable"
        if secret_api_key and secret_api_key not in PLACEHOLDER_KEYS:
            return "Streamlit Secrets"
        if config_api_key and config_api_key not in PLACEHOLDER_KEYS:
            return "config.toml (legacy)"
        return "Belum terbaca"

    @property
    def is_configured(self) -> bool:
        return (
            self.config_error is None
            and self.enabled
            and self.api_key.strip() not in PLACEHOLDER_KEYS
            and bool(self.chat_completions_url)
            and bool(self.model)
        )

    @property
    def status_reason(self) -> str:
        if self.config_error:
            return self.config_error
        if not self.enabled:
            return "Integrasi API dinonaktifkan karena enabled = false."
        if self.api_key.strip() in PLACEHOLDER_KEYS:
            return "API key belum terbaca. Untuk Streamlit Online, isi [openai] api_key di App settings → Secrets."
        if not self.chat_completions_url:
            return "chat_completions_url kosong."
        if not self.model:
            return "model kosong."
        return f"Konfigurasi API terbaca dari {self.api_key_source}."

    def build_model_chain(self, primary_model: Optional[str] = None, fallback_models: Optional[List[str]] = None) -> List[str]:
        chain: List[str] = []
        for model in [primary_model or self.model, *(fallback_models if fallback_models is not None else self.fallback_models)]:
            model = str(model).strip()
            if model and model not in chain:
                chain.append(model)
        return chain

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResult:
        if self.config_error:
            return ChatResult(False, error=self.config_error, content=f"Error: {self.config_error}")
        if not self.enabled:
            return ChatResult(False, error="Integrasi API dinonaktifkan", content="Error: Integrasi API dinonaktifkan.")
        if self.api_key.strip() in PLACEHOLDER_KEYS:
            msg = "API key belum terbaca dari Streamlit Secrets, environment variable, atau config.toml."
            return ChatResult(False, error=msg, content=f"Error: {msg}")

        selected_model = model or self.model
        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else float(temperature),
            "max_tokens": self.max_tokens if max_tokens is None else int(max_tokens),
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post(self.chat_completions_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            content, finish_reason, usage, response_model = self._extract_response(response.text)
            return ChatResult(
                success=True,
                content=content,
                model=response_model or selected_model,
                finish_reason=finish_reason,
                usage=usage,
                raw_preview=response.text[:500],
            )
        except requests.exceptions.HTTPError as error:
            status = error.response.status_code if error.response is not None else "unknown"
            detail = error.response.text[:700] if error.response is not None else str(error)
            msg = f"API mengembalikan status {status} - {detail}"
            return ChatResult(False, model=selected_model, error=msg, content=f"Error: {msg}")
        except requests.exceptions.RequestException as error:
            msg = f"Gagal terhubung ke API - {error}"
            return ChatResult(False, model=selected_model, error=msg, content=f"Error: {msg}")
        except Exception as error:
            msg = f"Gagal membaca respons API - {error}"
            return ChatResult(False, model=selected_model, error=msg, content=f"Error: {msg}")

    def generate_response(self, prompt: str, context: Optional[str] = None, temperature: Optional[float] = None, model: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        return self.generate_chat_completion(messages, temperature=temperature, model=model, max_tokens=max_tokens).content

    def generate_chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        fallback_models: Optional[List[str]] = None,
        min_answer_chars: Optional[int] = None,
    ) -> Dict[str, Any]:
        chain = self.build_model_chain(model or self.model, fallback_models)
        attempts: List[Dict[str, Any]] = []
        last_result = ChatResult(False, content="Error: Tidak ada respons dari model fallback.")

        for index, model_id in enumerate(chain, start=1):
            result = self.generate_chat_completion(messages, temperature=temperature, model=model_id, max_tokens=max_tokens)
            last_result = result
            useful, reason = self.is_useful_response(result, messages, min_answer_chars=min_answer_chars)
            attempts.append({
                "attempt": index,
                "model": model_id,
                "useful": useful,
                "reason": reason,
                "finish_reason": result.finish_reason,
                "usage": result.usage,
                "error": result.error,
            })
            if useful:
                return {"success": True, "content": result.content, "model": model_id, "result": result, "attempts": attempts}
            if not self.smart_fallback_enabled:
                break

        return {"success": False, "content": last_result.content, "model": last_result.model or (model or self.model), "result": last_result, "attempts": attempts}

    def generate_response_with_fallback(self, prompt: str, context: Optional[str] = None, temperature: Optional[float] = None, model: Optional[str] = None, max_tokens: Optional[int] = None, fallback_models: Optional[List[str]] = None, min_answer_chars: Optional[int] = None) -> Dict[str, Any]:
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        return self.generate_chat_completion_with_fallback(messages, temperature=temperature, model=model, max_tokens=max_tokens, fallback_models=fallback_models, min_answer_chars=min_answer_chars)

    def is_useful_response(self, result: ChatResult, messages: List[Dict[str, str]], min_answer_chars: Optional[int] = None) -> Tuple[bool, str]:
        text = (result.content or "").strip()
        if not result.success or result.error:
            return False, result.error[:180] if result.error else "request gagal"
        if not text:
            return False, "respons kosong"
        lowered = text.lower()
        if any(pattern in lowered for pattern in UNHELPFUL_PATTERNS):
            return False, "respons terdeteksi tidak menjawab"
        if result.finish_reason == "length":
            return False, "respons kepotong karena max_tokens"
        min_chars = self.min_answer_chars if min_answer_chars is None else int(min_answer_chars)
        if len(text) < min_chars:
            return False, f"respons terlalu pendek ({len(text)} karakter)"
        user_text = " ".join(msg.get("content", "") for msg in messages if msg.get("role") == "user").lower()
        domain_requested = any(term in user_text for term in DOMAIN_TERMS)
        if domain_requested and len(text) < 180 and not any(term in lowered for term in DOMAIN_TERMS):
            return False, "respons pendek dan tidak memuat konteks peternakan"
        return True, "ok"

    @classmethod
    def _extract_response(cls, raw_text: str) -> Tuple[str, str, Dict[str, int], str]:
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("respons API kosong")
        try:
            data = json.loads(text)
            return cls._extract_from_data(data)
        except json.JSONDecodeError:
            pass

        sse_payloads = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(":"):
                continue
            if stripped.startswith("data:"):
                payload = stripped[5:].strip()
                if payload and payload != "[DONE]":
                    sse_payloads.append(payload)
        if sse_payloads:
            return cls._extract_from_fragments(sse_payloads)

        line_payloads = [line.strip() for line in text.splitlines() if line.strip()]
        if len(line_payloads) > 1:
            try:
                return cls._extract_from_fragments(line_payloads)
            except Exception:
                pass

        decoder = json.JSONDecoder()
        idx = 0
        fragments: List[str] = []
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text):
                break
            try:
                obj, idx = decoder.raw_decode(text, idx)
                fragments.append(json.dumps(obj, ensure_ascii=False))
            except json.JSONDecodeError:
                break
        if fragments:
            return cls._extract_from_fragments(fragments)
        raise ValueError(f"format respons API tidak dikenali. Awal respons: {text[:300].replace(chr(10), ' ')}")

    @classmethod
    def _extract_from_fragments(cls, fragments: List[str]) -> Tuple[str, str, Dict[str, int], str]:
        parts: List[str] = []
        last_full = ""
        finish_reason = ""
        usage: Dict[str, int] = {}
        model = ""
        for fragment in fragments:
            try:
                data = json.loads(fragment)
            except json.JSONDecodeError:
                continue
            chunk = cls._extract_delta_text(data)
            if chunk:
                parts.append(chunk)
            try:
                full, finish, use, mod = cls._extract_from_data(data)
                if full:
                    last_full = full
                finish_reason = finish or finish_reason
                usage = use or usage
                model = mod or model
            except Exception:
                if isinstance(data, dict):
                    model = str(data.get("model", model) or model)
                    usage = cls._normalise_usage(data.get("usage", usage))
        content = "".join(parts).strip() or last_full.strip()
        if not content:
            raise ValueError("tidak menemukan content/text pada fragmen respons API")
        return content, finish_reason, usage, model

    @classmethod
    def _extract_from_data(cls, data: Dict[str, Any]) -> Tuple[str, str, Dict[str, int], str]:
        if not isinstance(data, dict):
            raise ValueError("respons API bukan objek JSON")
        model = str(data.get("model", "") or "")
        usage = cls._normalise_usage(data.get("usage", {}))
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip(), str(data.get("finish_reason", "") or ""), usage, model
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("field choices kosong pada respons API")
        choice = choices[0]
        if not isinstance(choice, dict):
            raise ValueError("format choices tidak valid pada respons API")
        finish_reason = str(choice.get("finish_reason", "") or "")
        message = choice.get("message", {})
        if isinstance(message, dict):
            content = cls._extract_content_value(message.get("content"))
            if content.strip():
                return content.strip(), finish_reason, usage, model
        text_value = choice.get("text")
        if isinstance(text_value, str) and text_value.strip():
            return text_value.strip(), finish_reason, usage, model
        delta_text = cls._extract_delta_text(data)
        if delta_text.strip():
            return delta_text.strip(), finish_reason, usage, model
        if finish_reason == "length":
            raise ValueError("respons API valid tetapi content kosong karena finish_reason=length. Naikkan max_tokens atau gunakan fallback model.")
        raise ValueError("tidak menemukan content/text pada respons API")

    @staticmethod
    def _normalise_usage(usage: Any) -> Dict[str, int]:
        if not isinstance(usage, dict):
            return {}
        result: Dict[str, int] = {}
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"):
            try:
                if usage.get(key) is not None:
                    result[key] = int(usage.get(key, 0) or 0)
            except Exception:
                pass
        return result

    @staticmethod
    def _extract_content_value(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            collected: List[str] = []
            for item in content:
                if isinstance(item, str):
                    collected.append(item)
                elif isinstance(item, dict):
                    value = item.get("text") or item.get("content")
                    if isinstance(value, str):
                        collected.append(value)
                    elif isinstance(value, dict):
                        nested = value.get("text") or value.get("content")
                        if isinstance(nested, str):
                            collected.append(nested)
            return "".join(collected)
        if isinstance(content, dict):
            value = content.get("text") or content.get("content")
            if isinstance(value, str):
                return value
        return ""

    @classmethod
    def _extract_delta_text(cls, data: Dict[str, Any]) -> str:
        choices = data.get("choices", []) if isinstance(data, dict) else []
        if not choices:
            return ""
        choice = choices[0]
        if not isinstance(choice, dict):
            return ""
        delta = choice.get("delta", {})
        if isinstance(delta, dict):
            content = cls._extract_content_value(delta.get("content"))
            if content:
                return content
        message = choice.get("message", {})
        if isinstance(message, dict):
            content = cls._extract_content_value(message.get("content"))
            if content:
                return content
        text_value = choice.get("text")
        return text_value if isinstance(text_value, str) else ""
