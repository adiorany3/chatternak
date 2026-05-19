from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


DEFAULT_MODEL = {
    "id": "slashai/gpt-5-mini",
    "provider": "slashai",
    "input_per_1m_rp": 50,
    "output_per_1m_rp": 200,
}


def load_model_catalog(path: str | Path = "models.toml") -> List[Dict[str, Any]]:
    """Membaca daftar model dari models.toml.

    Mengembalikan minimal satu model agar aplikasi tetap bisa berjalan
    meskipun file models.toml belum ada atau formatnya salah.
    """
    catalog_path = Path(path)
    if not catalog_path.exists():
        return [DEFAULT_MODEL.copy()]

    try:
        with catalog_path.open("rb") as file:
            loaded = tomllib.load(file)
        models = loaded.get("models", [])
        cleaned: List[Dict[str, Any]] = []
        for model in models:
            model_id = str(model.get("id", "")).strip()
            if not model_id:
                continue
            cleaned.append({
                "id": model_id,
                "provider": str(model.get("provider", model_id.split("/")[0])).strip(),
                "input_per_1m_rp": int(model.get("input_per_1m_rp", 0)),
                "output_per_1m_rp": int(model.get("output_per_1m_rp", 0)),
            })
        return cleaned or [DEFAULT_MODEL.copy()]
    except Exception:
        return [DEFAULT_MODEL.copy()]


def get_model_by_id(model_id: str, models: List[Dict[str, Any]]) -> Dict[str, Any]:
    for model in models:
        if model["id"] == model_id:
            return model
    return models[0] if models else DEFAULT_MODEL.copy()


def format_rupiah(value: int) -> str:
    return f"Rp {value:,}".replace(",", ".")


def format_model_option(model: Dict[str, Any]) -> str:
    input_price = format_rupiah(int(model.get("input_per_1m_rp", 0)))
    output_price = format_rupiah(int(model.get("output_per_1m_rp", 0)))
    return f"{model['id']} — In {input_price}/1M | Out {output_price}/1M"
