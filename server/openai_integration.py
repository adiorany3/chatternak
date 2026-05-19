from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional
import os
import requests

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for Python 3.10
    import tomli as tomllib


PROJECT_DIR = Path(__file__).resolve().parent

DEFAULT_CONFIG: Dict[str, Any] = {
    "openai": {
        "enabled": True,
        "api_key": "",  # legacy fallback; jangan dipakai untuk deployment publik
        "chat_completions_url": "https://api.slashai.my.id/v1/chat/completions",
        "model": "slashai/gpt-5-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
        "timeout": 60,
    }
}

PLACEHOLDER_KEYS = {
    "",
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


class OpenAIChatAPI:
    """Client sederhana untuk endpoint OpenAI-compatible Chat Completions.

    Prioritas pembacaan API key:
    1. Environment variable: OPENAI_API_KEY atau SLASHAI_API_KEY
    2. Streamlit Secrets: [openai] api_key = "..."
    3. config.toml api_key sebagai fallback legacy saja

    Untuk Streamlit Community Cloud / Streamlit Online, gunakan menu Secrets
    dan jangan menyimpan API key asli di repository.
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

        self.enabled: bool = self._get_bool_setting("enabled", settings, secret_settings)
        self.api_key: str = env_api_key or secret_api_key or config_api_key
        self.api_key_source: str = self._detect_api_key_source(env_api_key, secret_api_key, config_api_key)
        self.chat_completions_url: str = str(
            self._get_setting("chat_completions_url", settings, secret_settings)
        ).strip()
        self.model: str = str(self._get_setting("model", settings, secret_settings)).strip()
        self.temperature: float = float(self._get_setting("temperature", settings, secret_settings))
        self.max_tokens: int = int(self._get_setting("max_tokens", settings, secret_settings))
        self.timeout: int = int(self._get_setting("timeout", settings, secret_settings))

    @staticmethod
    def _resolve_config_path(config_path: str | Path | None) -> Path:
        if config_path is None:
            return PROJECT_DIR / "config.toml"
        path = Path(config_path)
        if path.is_absolute():
            return path
        return PROJECT_DIR / path

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            # config.toml tidak dibuat fatal agar deployment tetap bisa berjalan
            # hanya dengan Streamlit Secrets / environment variable.
            return deepcopy(DEFAULT_CONFIG)

        try:
            with self.config_path.open("rb") as file:
                loaded = tomllib.load(file)
        except Exception as error:
            self.config_error = f"Gagal membaca config.toml: {error}"
            return deepcopy(DEFAULT_CONFIG)

        merged = deepcopy(DEFAULT_CONFIG)
        merged["openai"] = {**DEFAULT_CONFIG["openai"], **loaded.get("openai", {})}
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
        """Membaca Streamlit Secrets tanpa membuat aplikasi gagal bila secrets belum ada."""
        try:
            import streamlit as st
        except Exception:
            return {"openai": {}}

        try:
            openai_section = self._safe_dict(st.secrets.get("openai", {}))
            # Dukungan tambahan jika user menaruh key di root secrets:
            # OPENAI_API_KEY = "..." atau SLASHAI_API_KEY = "..."
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
            return "API key belum terbaca. Untuk Streamlit Online, isi [openai] api_key di menu App settings → Secrets."
        if not self.chat_completions_url:
            return "chat_completions_url kosong. Isi di config.toml atau Streamlit Secrets."
        if not self.model:
            return "model kosong. Isi di config.toml atau Streamlit Secrets."
        return f"Konfigurasi API terbaca dari {self.api_key_source}."

    def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if self.config_error:
            return f"Error: {self.config_error}"
        if not self.enabled:
            return "Error: Integrasi OpenAI-compatible API sedang dinonaktifkan."
        if self.api_key.strip() in PLACEHOLDER_KEYS:
            return "Error: API key belum terbaca dari Streamlit Secrets, environment variable, atau config.toml."

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else float(temperature),
            "max_tokens": self.max_tokens if max_tokens is None else int(max_tokens),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.chat_completions_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return self._extract_text(data)
        except requests.exceptions.HTTPError as error:
            detail = error.response.text[:500] if error.response is not None else str(error)
            status = error.response.status_code if error.response is not None else "unknown"
            return f"Error: API mengembalikan status {status} - {detail}"
        except requests.exceptions.RequestException as error:
            return f"Error: Gagal terhubung ke API - {error}"
        except Exception as error:
            return f"Error: Gagal membaca respons API - {error}"

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("field choices kosong pada respons API")

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        # Fallback untuk beberapa endpoint kompatibel yang memakai field text.
        text = choices[0].get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        raise ValueError("tidak menemukan content/text pada respons API")
