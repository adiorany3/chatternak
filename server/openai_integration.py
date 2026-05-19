from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import os
import requests

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for Python 3.10
    import tomli as tomllib


DEFAULT_CONFIG: Dict[str, Any] = {
    "openai": {
        "enabled": True,
        "api_key": "",
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
}


class OpenAIChatAPI:
    """Client sederhana untuk endpoint OpenAI-compatible Chat Completions.

    Konfigurasi dibaca dari config.toml. API key juga bisa dioverride melalui
    environment variable OPENAI_API_KEY agar aman saat deployment.
    """

    def __init__(self, config_path: str | Path = "config.toml") -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()
        settings = self.config.get("openai", {})

        self.enabled: bool = bool(settings.get("enabled", True))
        self.api_key: str = os.getenv("OPENAI_API_KEY", str(settings.get("api_key", "")).strip())
        self.chat_completions_url: str = str(
            settings.get("chat_completions_url", DEFAULT_CONFIG["openai"]["chat_completions_url"])
        ).strip()
        self.model: str = str(settings.get("model", DEFAULT_CONFIG["openai"]["model"])).strip()
        self.temperature: float = float(settings.get("temperature", DEFAULT_CONFIG["openai"]["temperature"]))
        self.max_tokens: int = int(settings.get("max_tokens", DEFAULT_CONFIG["openai"]["max_tokens"]))
        self.timeout: int = int(settings.get("timeout", DEFAULT_CONFIG["openai"]["timeout"]))

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return DEFAULT_CONFIG.copy()

        with self.config_path.open("rb") as file:
            loaded = tomllib.load(file)

        merged = DEFAULT_CONFIG.copy()
        merged["openai"] = {**DEFAULT_CONFIG["openai"], **loaded.get("openai", {})}
        return merged

    @property
    def is_configured(self) -> bool:
        return self.enabled and self.api_key not in PLACEHOLDER_KEYS and bool(self.chat_completions_url) and bool(self.model)

    def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> str:
        if not self.enabled:
            return "Error: Integrasi OpenAI-compatible API sedang dinonaktifkan di config.toml."
        if self.api_key in PLACEHOLDER_KEYS:
            return "Error: API key belum diisi di config.toml."

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else float(temperature),
            "max_tokens": self.max_tokens,
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
            return f"Error: API mengembalikan status {error.response.status_code if error.response is not None else 'unknown'} - {detail}"
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
