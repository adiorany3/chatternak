from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple
import json
from pathlib import Path
import tempfile

import requests

LOCAL_DB_DIR = Path(tempfile.gettempdir()) / "ai_pakar_ternak_enterprise_db"
LOCAL_DB_FILE = LOCAL_DB_DIR / "latest_payload.json"


def get_storage_config(secrets: Any = None) -> Dict[str, str]:
    cfg = {"provider": "local", "supabase_url": "", "supabase_key": "", "table": "ai_pakar_ternak_sessions", "configured": "false"}
    try:
        section = secrets.get("database", {}) if secrets is not None else {}
        cfg["provider"] = str(section.get("provider", "local") or "local").lower()
        cfg["supabase_url"] = str(section.get("supabase_url", "") or "").rstrip("/")
        cfg["supabase_key"] = str(section.get("supabase_key", "") or "")
        cfg["table"] = str(section.get("table", "ai_pakar_ternak_sessions") or "ai_pakar_ternak_sessions")
    except Exception:
        pass
    cfg["configured"] = "true" if cfg["provider"] == "supabase" and cfg["supabase_url"] and cfg["supabase_key"] else ("local" if cfg["provider"] == "local" else "false")
    return cfg


def save_local(payload: Dict[str, Any]) -> Dict[str, Any]:
    LOCAL_DB_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_DB_FILE.write_text(json.dumps(payload, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
    return {"ok": True, "provider": "local", "message": f"Tersimpan lokal sementara: {LOCAL_DB_FILE}", "synced_at": datetime.now().isoformat(timespec="seconds")}


def load_local() -> Tuple[bool, Dict[str, Any], str]:
    if not LOCAL_DB_FILE.exists():
        return False, {}, "Belum ada data lokal sementara."
    try:
        return True, json.loads(LOCAL_DB_FILE.read_text(encoding="utf-8")), f"Dimuat dari {LOCAL_DB_FILE}"
    except Exception as error:
        return False, {}, f"Gagal membaca local db: {error}"


def save_supabase(payload: Dict[str, Any], cfg: Dict[str, str]) -> Dict[str, Any]:
    session_id = str(payload.get("session_id") or "default")
    url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}"
    headers = {
        "apikey": cfg["supabase_key"],
        "Authorization": f"Bearer {cfg['supabase_key']}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    body = {
        "session_id": session_id,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }
    response = requests.post(url, headers=headers, json=body, timeout=25)
    if response.status_code >= 300:
        raise RuntimeError(f"Supabase status {response.status_code}: {response.text[:300]}")
    return {"ok": True, "provider": "supabase", "message": "Payload berhasil disimpan ke Supabase.", "synced_at": datetime.now().isoformat(timespec="seconds")}


def load_supabase(session_id: str, cfg: Dict[str, str]) -> Tuple[bool, Dict[str, Any], str]:
    if not session_id:
        return False, {}, "Session ID kosong."
    url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}?session_id=eq.{session_id}&select=payload&limit=1"
    headers = {"apikey": cfg["supabase_key"], "Authorization": f"Bearer {cfg['supabase_key']}"}
    response = requests.get(url, headers=headers, timeout=25)
    if response.status_code >= 300:
        return False, {}, f"Supabase status {response.status_code}: {response.text[:300]}"
    rows = response.json() or []
    if not rows:
        return False, {}, "Session ID tidak ditemukan di Supabase."
    return True, rows[0].get("payload") or {}, "Payload berhasil dimuat dari Supabase."


def save_payload(payload: Dict[str, Any], secrets: Any = None) -> Dict[str, Any]:
    cfg = get_storage_config(secrets)
    if cfg.get("provider") == "supabase" and cfg.get("configured") == "true":
        return save_supabase(payload, cfg)
    return save_local(payload)


def load_payload(session_id: str = "", secrets: Any = None) -> Tuple[bool, Dict[str, Any], str]:
    cfg = get_storage_config(secrets)
    if cfg.get("provider") == "supabase" and cfg.get("configured") == "true":
        return load_supabase(session_id, cfg)
    return load_local()
