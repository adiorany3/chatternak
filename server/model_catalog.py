from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

PROJECT_DIR = Path(__file__).resolve().parent

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

DEFAULT_MODEL: Dict[str, Any] = {
    "id": "slashai/gpt-5-nano",
    "provider": "slashai",
    "input_per_1m_rp": 50,
    "output_per_1m_rp": 200,
}


def load_model_catalog(path: str | Path = "models.toml") -> List[Dict[str, Any]]:
    catalog_path = Path(path)
    if not catalog_path.is_absolute():
        catalog_path = PROJECT_DIR / catalog_path
    if not catalog_path.exists():
        return [DEFAULT_MODEL.copy()]
    try:
        with catalog_path.open("rb") as file:
            loaded = tomllib.load(file)
        models = loaded.get("models", [])
        cleaned: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for model in models:
            model_id = str(model.get("id", "")).strip()
            if not model_id or model_id in seen:
                continue
            seen.add(model_id)
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
        if model.get("id") == model_id:
            return model
    return models[0] if models else DEFAULT_MODEL.copy()


def format_rupiah(value: float | int) -> str:
    amount = float(value)
    if amount == 0:
        return "Rp 0"
    if abs(amount) < 1:
        formatted = f"{amount:,.2f}"
    else:
        formatted = f"{amount:,.0f}" if amount.is_integer() else f"{amount:,.2f}"
    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"Rp {formatted}"


def format_model_option(model: Dict[str, Any]) -> str:
    return (
        f"{model['id']} — In {format_rupiah(model.get('input_per_1m_rp', 0))}/1M | "
        f"Out {format_rupiah(model.get('output_per_1m_rp', 0))}/1M"
    )


def estimate_cost_rp(model_id: str, prompt_tokens: int = 0, completion_tokens: int = 0, models: List[Dict[str, Any]] | None = None) -> float:
    catalog = models or load_model_catalog()
    model = get_model_by_id(model_id, catalog)
    input_cost = prompt_tokens / 1_000_000 * float(model.get("input_per_1m_rp", 0))
    output_cost = completion_tokens / 1_000_000 * float(model.get("output_per_1m_rp", 0))
    return input_cost + output_cost
