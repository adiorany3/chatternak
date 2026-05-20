from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple
import json
import os
import re
from pathlib import Path
import tempfile
from urllib.parse import quote_plus

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

LOCAL_DB_DIR = Path(tempfile.gettempdir()) / "ai_pakar_ternak_enterprise_db"
LOCAL_DB_FILE = LOCAL_DB_DIR / "latest_payload.json"


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _secret_section(secrets: Any, name: str) -> Dict[str, Any]:
    try:
        section = secrets.get(name, {}) if secrets is not None else {}
        return dict(section) if section is not None else {}
    except Exception:
        return {}


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _normalise_provider(provider: str, cfg: Dict[str, str]) -> str:
    provider = (provider or "local").strip().lower()
    if provider in {"postgresql", "pgsql", "supabase_postgres", "supabase-db", "supabase_db"}:
        return "postgres"
    if provider in {"supabase_rest", "rest"}:
        return "supabase_rest"
    if provider == "supabase":
        # Backward-compatible: older versions used provider="supabase" for REST.
        # Newer Supabase database settings can use the same provider when DATABASE_URL/host is supplied.
        if cfg.get("database_url") or (cfg.get("host") and cfg.get("password")):
            return "postgres"
        if cfg.get("supabase_url") and cfg.get("supabase_key"):
            return "supabase_rest"
    return provider


def _has_postgres_config(cfg: Dict[str, str]) -> bool:
    if cfg.get("database_url"):
        return True
    required = ["host", "port", "database", "user", "password"]
    return all(cfg.get(item) for item in required)


def _safe_table_name(table: str) -> str:
    table = table or "ai_pakar_ternak_sessions"
    # Allow optional schema.table, but validate each identifier strictly.
    parts = table.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError("Nama tabel database tidak valid.")
    for part in parts:
        if not _IDENTIFIER_RE.match(part):
            raise ValueError("Nama tabel database hanya boleh huruf, angka, dan underscore; diawali huruf/underscore.")
    return ".".join(f'"{part}"' for part in parts)


def get_storage_config(secrets: Any = None) -> Dict[str, str]:
    section = _secret_section(secrets, "database")
    cfg: Dict[str, str] = {
        "provider": _as_str(section.get("provider", _env_first("DATABASE_PROVIDER", default="local")), "local").lower(),
        "mode": "local",
        "configured": "local",
        # Supabase REST / PostgREST fallback compatibility
        "supabase_url": _as_str(section.get("supabase_url", _env_first("SUPABASE_URL")), "").rstrip("/"),
        "supabase_key": _as_str(section.get("supabase_key", _env_first("SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY")), ""),
        # Supabase PostgreSQL / direct DB connection
        "database_url": _as_str(section.get("database_url", _env_first("DATABASE_URL")), ""),
        "host": _as_str(section.get("host", _env_first("PGHOST", "SUPABASE_DB_HOST")), ""),
        "port": _as_str(section.get("port", _env_first("PGPORT", "SUPABASE_DB_PORT", default="5432")), "5432"),
        "database": _as_str(section.get("database", _env_first("PGDATABASE", "SUPABASE_DB_NAME", default="postgres")), "postgres"),
        "user": _as_str(section.get("user", _env_first("PGUSER", "SUPABASE_DB_USER", default="postgres")), "postgres"),
        "password": _as_str(section.get("password", _env_first("PGPASSWORD", "SUPABASE_DB_PASSWORD")), ""),
        "sslmode": _as_str(section.get("sslmode", _env_first("PGSSLMODE", default="require")), "require"),
        "table": _as_str(section.get("table", _env_first("DATABASE_TABLE", default="ai_pakar_ternak_sessions")), "ai_pakar_ternak_sessions"),
    }
    cfg["mode"] = _normalise_provider(cfg["provider"], cfg)

    if cfg["mode"] == "postgres" and _has_postgres_config(cfg):
        cfg["configured"] = "true"
    elif cfg["mode"] == "supabase_rest" and cfg["supabase_url"] and cfg["supabase_key"]:
        cfg["configured"] = "true"
    elif cfg["mode"] == "local":
        cfg["configured"] = "local"
    else:
        cfg["configured"] = "false"

    # Do not expose password/key values through UI JSON accidentally.
    cfg["password_masked"] = "***" if cfg.get("password") else ""
    cfg["supabase_key_masked"] = "***" if cfg.get("supabase_key") else ""
    cfg["database_url_masked"] = _mask_database_url(cfg.get("database_url", ""))
    return cfg


def _mask_database_url(url: str) -> str:
    if not url:
        return ""
    # Keep enough detail for debugging without exposing credentials.
    return re.sub(r"//([^:/?#]+):([^@]+)@", r"//\1:***@", url)


def _postgres_dsn(cfg: Dict[str, str]) -> str:
    if cfg.get("database_url"):
        return cfg["database_url"]
    user = quote_plus(cfg.get("user", "postgres"))
    password = quote_plus(cfg.get("password", ""))
    host = cfg.get("host", "")
    port = cfg.get("port", "5432")
    database = cfg.get("database", "postgres")
    sslmode = cfg.get("sslmode", "require") or "require"
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={quote_plus(sslmode)}"


def _connect_postgres(cfg: Dict[str, str]):
    try:
        import psycopg2
    except Exception as error:
        raise RuntimeError("Dependency PostgreSQL belum tersedia. Pastikan requirements.txt berisi psycopg2-binary dan redeploy aplikasi.") from error
    return psycopg2.connect(_postgres_dsn(cfg), connect_timeout=15)


def _ensure_postgres_table(conn: Any, table: str) -> None:
    safe_table = _safe_table_name(table)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {safe_table} (
                session_id text PRIMARY KEY,
                updated_at timestamptz NOT NULL DEFAULT now(),
                payload jsonb NOT NULL
            )
            """
        )
    conn.commit()


def save_local(payload: Dict[str, Any]) -> Dict[str, Any]:
    LOCAL_DB_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_DB_FILE.write_text(json.dumps(payload, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
    return {"ok": True, "provider": "local", "mode": "local", "message": f"Tersimpan lokal sementara: {LOCAL_DB_FILE}", "synced_at": datetime.now().isoformat(timespec="seconds")}


def load_local() -> Tuple[bool, Dict[str, Any], str]:
    if not LOCAL_DB_FILE.exists():
        return False, {}, "Belum ada data lokal sementara."
    try:
        return True, json.loads(LOCAL_DB_FILE.read_text(encoding="utf-8")), f"Dimuat dari {LOCAL_DB_FILE}"
    except Exception as error:
        return False, {}, f"Gagal membaca local db: {error}"


def save_supabase_rest(payload: Dict[str, Any], cfg: Dict[str, str]) -> Dict[str, Any]:
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
        raise RuntimeError(f"Supabase REST status {response.status_code}: {response.text[:300]}")
    return {"ok": True, "provider": "supabase", "mode": "supabase_rest", "message": "Payload berhasil disimpan ke Supabase REST.", "synced_at": datetime.now().isoformat(timespec="seconds")}


def load_supabase_rest(session_id: str, cfg: Dict[str, str]) -> Tuple[bool, Dict[str, Any], str]:
    if not session_id:
        return False, {}, "Session ID kosong."
    url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}?session_id=eq.{session_id}&select=payload&limit=1"
    headers = {"apikey": cfg["supabase_key"], "Authorization": f"Bearer {cfg['supabase_key']}"}
    response = requests.get(url, headers=headers, timeout=25)
    if response.status_code >= 300:
        return False, {}, f"Supabase REST status {response.status_code}: {response.text[:300]}"
    rows = response.json() or []
    if not rows:
        return False, {}, "Session ID tidak ditemukan di Supabase."
    return True, rows[0].get("payload") or {}, "Payload berhasil dimuat dari Supabase REST."


# Backward-compatible aliases used by older code/docs.
save_supabase = save_supabase_rest
load_supabase = load_supabase_rest


def save_postgres(payload: Dict[str, Any], cfg: Dict[str, str]) -> Dict[str, Any]:
    session_id = str(payload.get("session_id") or "default")
    table = cfg.get("table", "ai_pakar_ternak_sessions")
    safe_table = _safe_table_name(table)
    try:
        from psycopg2.extras import Json
    except Exception as error:
        raise RuntimeError("Dependency psycopg2.extras tidak tersedia. Pastikan psycopg2-binary terpasang.") from error

    with _connect_postgres(cfg) as conn:
        _ensure_postgres_table(conn, table)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {safe_table} (session_id, updated_at, payload)
                VALUES (%s, now(), %s)
                ON CONFLICT (session_id)
                DO UPDATE SET updated_at = EXCLUDED.updated_at, payload = EXCLUDED.payload
                """,
                (session_id, Json(payload)),
            )
        conn.commit()
    return {"ok": True, "provider": "supabase", "mode": "postgres", "message": "Payload berhasil disimpan ke Supabase PostgreSQL.", "session_id": session_id, "synced_at": datetime.now().isoformat(timespec="seconds")}


def load_postgres(session_id: str, cfg: Dict[str, str]) -> Tuple[bool, Dict[str, Any], str]:
    if not session_id:
        return False, {}, "Session ID kosong."
    table = cfg.get("table", "ai_pakar_ternak_sessions")
    safe_table = _safe_table_name(table)
    with _connect_postgres(cfg) as conn:
        _ensure_postgres_table(conn, table)
        with conn.cursor() as cur:
            cur.execute(f"SELECT payload FROM {safe_table} WHERE session_id = %s LIMIT 1", (session_id,))
            row = cur.fetchone()
    if not row:
        return False, {}, "Session ID tidak ditemukan di Supabase PostgreSQL."
    payload = row[0]
    if isinstance(payload, str):
        payload = json.loads(payload)
    return True, payload or {}, "Payload berhasil dimuat dari Supabase PostgreSQL."


def test_connection(secrets: Any = None) -> Dict[str, Any]:
    cfg = get_storage_config(secrets)
    if cfg.get("configured") != "true":
        return {"ok": False, "provider": cfg.get("provider"), "mode": cfg.get("mode"), "message": "Database belum dikonfigurasi. Gunakan Streamlit Secrets atau environment variable."}
    if cfg.get("mode") == "postgres":
        with _connect_postgres(cfg) as conn:
            _ensure_postgres_table(conn, cfg.get("table", "ai_pakar_ternak_sessions"))
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"ok": True, "provider": "supabase", "mode": "postgres", "message": "Koneksi Supabase PostgreSQL berhasil."}
    if cfg.get("mode") == "supabase_rest":
        url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}?select=session_id&limit=1"
        headers = {"apikey": cfg["supabase_key"], "Authorization": f"Bearer {cfg['supabase_key']}"}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code >= 300:
            return {"ok": False, "provider": "supabase", "mode": "supabase_rest", "message": f"Supabase REST status {response.status_code}: {response.text[:250]}"}
        return {"ok": True, "provider": "supabase", "mode": "supabase_rest", "message": "Koneksi Supabase REST berhasil."}
    return {"ok": True, "provider": "local", "mode": "local", "message": "Mode lokal aktif."}


def save_payload(payload: Dict[str, Any], secrets: Any = None) -> Dict[str, Any]:
    cfg = get_storage_config(secrets)
    if cfg.get("configured") == "true" and cfg.get("mode") == "postgres":
        return save_postgres(payload, cfg)
    if cfg.get("configured") == "true" and cfg.get("mode") == "supabase_rest":
        return save_supabase_rest(payload, cfg)
    return save_local(payload)


def load_payload(session_id: str = "", secrets: Any = None) -> Tuple[bool, Dict[str, Any], str]:
    cfg = get_storage_config(secrets)
    if cfg.get("configured") == "true" and cfg.get("mode") == "postgres":
        return load_postgres(session_id, cfg)
    if cfg.get("configured") == "true" and cfg.get("mode") == "supabase_rest":
        return load_supabase_rest(session_id, cfg)
    return load_local()
