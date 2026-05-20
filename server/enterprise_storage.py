from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple, Set, List
import hashlib
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


def _table_parts(table: str) -> Tuple[str, str]:
    table = table or "ai_pakar_ternak_sessions"
    parts = table.split(".")
    if len(parts) == 1:
        schema, name = "public", parts[0]
    elif len(parts) == 2:
        schema, name = parts[0], parts[1]
    else:
        raise ValueError("Nama tabel database tidak valid.")
    for part in (schema, name):
        if not _IDENTIFIER_RE.match(part):
            raise ValueError("Nama tabel database hanya boleh huruf, angka, dan underscore; diawali huruf/underscore.")
    return schema, name


def _safe_table_name(table: str) -> str:
    schema, name = _table_parts(table)
    # Keep old behavior: if user supplied no schema, render only the table name.
    if "." in (table or ""):
        return f'"{schema}"."{name}"'
    return f'"{name}"'


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
        "core_memory_table": _as_str(section.get("core_memory_table", _env_first("AI_CORE_MEMORY_TABLE", "CORE_MEMORY_TABLE", default="ai_pakar_ternak_core_memory")), "ai_pakar_ternak_core_memory"),
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


def _get_postgres_columns(conn: Any, table: str) -> Set[str]:
    schema, name = _table_parts(table)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, name),
        )
        return {str(row[0]) for row in cur.fetchall()}


def _postgres_table_exists(conn: Any, table: str) -> bool:
    schema, name = _table_parts(table)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            )
            """,
            (schema, name),
        )
        return bool(cur.fetchone()[0])


def _ensure_postgres_table(conn: Any, table: str) -> None:
    """Create a new table when absent, and keep old tables compatible when present.

    Supported schemas:
    - New schema: session_id, payload, updated_at
    - Old schema: session_key, data, updated_at, optional user_label

    If the database user has ALTER permission, old tables are upgraded by adding
    session_id and payload columns while keeping the old columns. If ALTER is not
    allowed, the read/write functions still fall back to session_key/data.
    """
    safe_table = _safe_table_name(table)
    if not _postgres_table_exists(conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {safe_table} (
                    session_id text PRIMARY KEY,
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    payload jsonb NOT NULL DEFAULT '{{}}'::jsonb
                )
                """
            )
        conn.commit()
        return

    columns = _get_postgres_columns(conn, table)
    # Best-effort migration for databases that were created using the earlier SQL.
    try:
        with conn.cursor() as cur:
            if "payload" not in columns and "data" in columns:
                cur.execute(f"ALTER TABLE {safe_table} ADD COLUMN IF NOT EXISTS payload jsonb")
                cur.execute(f"UPDATE {safe_table} SET payload = data WHERE payload IS NULL")
            if "session_id" not in columns and "session_key" in columns:
                cur.execute(f"ALTER TABLE {safe_table} ADD COLUMN IF NOT EXISTS session_id text")
                cur.execute(f"UPDATE {safe_table} SET session_id = session_key WHERE session_id IS NULL")
            if "updated_at" not in columns:
                cur.execute(f"ALTER TABLE {safe_table} ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()")
        conn.commit()
    except Exception:
        # Roll back and continue with old schema compatibility.
        conn.rollback()


def _postgres_schema_mode(conn: Any, table: str) -> Tuple[str, str, Set[str]]:
    columns = _get_postgres_columns(conn, table)
    # Prefer the old session_key/data path when those columns exist because older
    # tables usually have UNIQUE(session_key), while a best-effort added
    # session_id column may not yet have a unique constraint.
    if "session_key" in columns and "data" in columns:
        return "session_key", "data", columns
    if "session_id" in columns and "payload" in columns:
        return "session_id", "payload", columns
    raise RuntimeError(
        "Struktur tabel Supabase belum sesuai. Buat kolom session_id+payload atau session_key+data. "
        "Lihat contoh SQL di menu Database Supabase."
    )


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

    # Prefer new REST schema; if Supabase returns a column error, try old schema.
    body = {"session_id": session_id, "updated_at": datetime.now().isoformat(timespec="seconds"), "payload": payload}
    response = requests.post(url, headers=headers, json=body, timeout=25)
    if response.status_code >= 300 and ("payload" in response.text or "session_id" in response.text):
        body = {"session_key": session_id, "updated_at": datetime.now().isoformat(timespec="seconds"), "data": payload}
        response = requests.post(url, headers=headers, json=body, timeout=25)
    if response.status_code >= 300:
        raise RuntimeError(f"Supabase REST status {response.status_code}: {response.text[:300]}")
    return {"ok": True, "provider": "supabase", "mode": "supabase_rest", "message": "Payload berhasil disimpan ke Supabase REST.", "synced_at": datetime.now().isoformat(timespec="seconds")}


def load_supabase_rest(session_id: str, cfg: Dict[str, str]) -> Tuple[bool, Dict[str, Any], str]:
    if not session_id:
        return False, {}, "Session ID kosong."
    headers = {"apikey": cfg["supabase_key"], "Authorization": f"Bearer {cfg['supabase_key']}"}

    url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}?session_id=eq.{session_id}&select=payload&limit=1"
    response = requests.get(url, headers=headers, timeout=25)
    if response.status_code >= 300 and ("payload" in response.text or "session_id" in response.text):
        url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}?session_key=eq.{session_id}&select=data&limit=1"
        response = requests.get(url, headers=headers, timeout=25)
    if response.status_code >= 300:
        return False, {}, f"Supabase REST status {response.status_code}: {response.text[:300]}"
    rows = response.json() or []
    if not rows:
        return False, {}, "Session ID tidak ditemukan di Supabase."
    row = rows[0]
    return True, row.get("payload") or row.get("data") or {}, "Payload berhasil dimuat dari Supabase REST."


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
        key_col, payload_col, columns = _postgres_schema_mode(conn, table)
        set_updated = "updated_at = EXCLUDED.updated_at, " if "updated_at" in columns else ""
        updated_insert_cols = ", updated_at" if "updated_at" in columns else ""
        updated_values = ", now()" if "updated_at" in columns else ""
        user_label_cols = ", user_label" if "user_label" in columns else ""
        user_label_values = ", %s" if "user_label" in columns else ""
        user_label_update = ", user_label = EXCLUDED.user_label" if "user_label" in columns else ""
        user_label = str((payload.get("profile") or {}).get("farm_name") or payload.get("app") or "AI Pakar Ternak")

        params = [session_id]
        if "user_label" in columns:
            params.append(user_label)
        params.append(Json(payload))

        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {safe_table} ({key_col}{user_label_cols}{updated_insert_cols}, {payload_col})
                VALUES (%s{user_label_values}{updated_values}, %s)
                ON CONFLICT ({key_col})
                DO UPDATE SET {set_updated}{payload_col} = EXCLUDED.{payload_col}{user_label_update}
                """,
                tuple(params),
            )
        conn.commit()
    return {"ok": True, "provider": "supabase", "mode": "postgres", "schema": f"{key_col}/{payload_col}", "message": "Payload berhasil disimpan ke Supabase PostgreSQL.", "session_id": session_id, "synced_at": datetime.now().isoformat(timespec="seconds")}


def load_postgres(session_id: str, cfg: Dict[str, str]) -> Tuple[bool, Dict[str, Any], str]:
    if not session_id:
        return False, {}, "Session ID kosong."
    table = cfg.get("table", "ai_pakar_ternak_sessions")
    safe_table = _safe_table_name(table)
    with _connect_postgres(cfg) as conn:
        _ensure_postgres_table(conn, table)
        key_col, payload_col, _columns = _postgres_schema_mode(conn, table)
        with conn.cursor() as cur:
            cur.execute(f"SELECT {payload_col} FROM {safe_table} WHERE {key_col} = %s LIMIT 1", (session_id,))
            row = cur.fetchone()
    if not row:
        return False, {}, "Session ID tidak ditemukan di Supabase PostgreSQL."
    payload = row[0]
    if isinstance(payload, str):
        payload = json.loads(payload)
    return True, payload or {}, f"Payload berhasil dimuat dari Supabase PostgreSQL ({key_col}/{payload_col})."


def test_connection(secrets: Any = None) -> Dict[str, Any]:
    cfg = get_storage_config(secrets)
    if cfg.get("configured") != "true":
        return {"ok": False, "provider": cfg.get("provider"), "mode": cfg.get("mode"), "message": "Database belum dikonfigurasi. Gunakan Streamlit Secrets atau environment variable."}
    if cfg.get("mode") == "postgres":
        with _connect_postgres(cfg) as conn:
            _ensure_postgres_table(conn, cfg.get("table", "ai_pakar_ternak_sessions"))
            key_col, payload_col, columns = _postgres_schema_mode(conn, cfg.get("table", "ai_pakar_ternak_sessions"))
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"ok": True, "provider": "supabase", "mode": "postgres", "schema": f"{key_col}/{payload_col}", "columns": sorted(columns), "message": f"Koneksi Supabase PostgreSQL berhasil. Skema aktif: {key_col}/{payload_col}."}
    if cfg.get("mode") == "supabase_rest":
        url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}?select=session_id&limit=1"
        headers = {"apikey": cfg["supabase_key"], "Authorization": f"Bearer {cfg['supabase_key']}"}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code >= 300:
            # Try old schema select before declaring failure.
            url = f"{cfg['supabase_url']}/rest/v1/{cfg['table']}?select=session_key&limit=1"
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


# ---------------------------------------------------------------------------
# AI Core Memory: persistent persona, skill, role, and learned operational memory
# ---------------------------------------------------------------------------

CORE_MEMORY_KINDS = {"persona", "skill", "role", "policy", "strategy", "learning"}
CORE_MEMORY_DEFAULT_TABLE = "ai_pakar_ternak_core_memory"


def _core_memory_table(cfg: Dict[str, str]) -> str:
    return cfg.get("core_memory_table") or CORE_MEMORY_DEFAULT_TABLE


def _memory_id(item: Dict[str, Any]) -> str:
    explicit = str(item.get("memory_id") or item.get("id") or "").strip()
    if explicit:
        return explicit[:96]
    raw = "|".join([
        str(item.get("kind") or "learning"),
        str(item.get("category") or "Catatan Lapangan"),
        str(item.get("memory") or ""),
    ]).lower().strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


def _normalise_core_memory_item(item: Dict[str, Any]) -> Dict[str, Any]:
    kind = str(item.get("kind") or item.get("type") or "learning").strip().lower()
    if kind not in CORE_MEMORY_KINDS:
        kind = "learning"
    priority = str(item.get("priority") or item.get("prioritas") or "Sedang").strip().title()
    if priority not in {"Tinggi", "Sedang", "Rendah"}:
        priority = "Sedang"
    memory = str(item.get("memory") or item.get("content") or item.get("catatan") or "").strip()
    category = str(item.get("category") or item.get("kategori") or kind.title()).strip() or kind.title()
    source = str(item.get("source") or item.get("sumber") or "supabase_core").strip() or "supabase_core"
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    return {
        "memory_id": _memory_id({**item, "kind": kind, "category": category, "memory": memory}),
        "kind": kind,
        "category": category,
        "priority": priority,
        "memory": memory,
        "source": source,
        "metadata": metadata,
        "created_at": str(item.get("created_at") or ""),
        "updated_at": str(item.get("updated_at") or ""),
        "usage_count": int(float(item.get("usage_count", 0) or 0)),
    }


def _ensure_core_memory_table(conn: Any, table: str) -> None:
    safe_table = _safe_table_name(table)
    index_prefix = _table_parts(table)[1]
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {safe_table} (
                memory_id text PRIMARY KEY,
                kind text NOT NULL DEFAULT 'learning',
                category text NOT NULL DEFAULT 'Catatan Lapangan',
                priority text NOT NULL DEFAULT 'Sedang',
                memory text NOT NULL,
                source text NOT NULL DEFAULT 'app',
                usage_count integer NOT NULL DEFAULT 0,
                metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{index_prefix}_kind ON {safe_table} (kind)")
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{index_prefix}_updated_at ON {safe_table} (updated_at DESC)")
    conn.commit()


def save_core_memory_items(items: List[Dict[str, Any]], secrets: Any = None) -> Dict[str, Any]:
    """Persist AI persona/skill/role/learning memory to Supabase PostgreSQL.

    This does not train model weights. It creates durable retrieval memory that is
    injected into future prompts so the assistant behaves consistently after app
    restarts and across sessions.
    """
    cfg = get_storage_config(secrets)
    if cfg.get("configured") != "true" or cfg.get("mode") != "postgres":
        return {"ok": False, "message": "AI Core Memory membutuhkan database PostgreSQL/Supabase aktif.", "saved": 0}
    clean_items = [_normalise_core_memory_item(item) for item in (items or [])]
    clean_items = [item for item in clean_items if item.get("memory")]
    if not clean_items:
        return {"ok": True, "message": "Tidak ada memory baru untuk disimpan.", "saved": 0}
    table = _core_memory_table(cfg)
    safe_table = _safe_table_name(table)
    try:
        from psycopg2.extras import Json
    except Exception as error:
        raise RuntimeError("Dependency psycopg2.extras tidak tersedia. Pastikan psycopg2-binary terpasang.") from error
    with _connect_postgres(cfg) as conn:
        _ensure_core_memory_table(conn, table)
        with conn.cursor() as cur:
            for item in clean_items:
                cur.execute(
                    f"""
                    INSERT INTO {safe_table}
                        (memory_id, kind, category, priority, memory, source, usage_count, metadata, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 1, %s, now())
                    ON CONFLICT (memory_id)
                    DO UPDATE SET
                        kind = EXCLUDED.kind,
                        category = EXCLUDED.category,
                        priority = EXCLUDED.priority,
                        memory = EXCLUDED.memory,
                        source = EXCLUDED.source,
                        usage_count = {safe_table}.usage_count + 1,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    (
                        item["memory_id"],
                        item["kind"],
                        item["category"],
                        item["priority"],
                        item["memory"],
                        item["source"],
                        Json(item.get("metadata") or {}),
                    ),
                )
        conn.commit()
    return {"ok": True, "message": f"{len(clean_items)} AI Core Memory tersimpan di Supabase.", "saved": len(clean_items), "table": table}


def load_core_memory_items(secrets: Any = None, limit: int = 240) -> Tuple[bool, List[Dict[str, Any]], str]:
    cfg = get_storage_config(secrets)
    if cfg.get("configured") != "true" or cfg.get("mode") != "postgres":
        return False, [], "Database PostgreSQL/Supabase belum aktif untuk AI Core Memory."
    table = _core_memory_table(cfg)
    safe_table = _safe_table_name(table)
    with _connect_postgres(cfg) as conn:
        _ensure_core_memory_table(conn, table)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT memory_id, kind, category, priority, memory, source, usage_count, metadata,
                       created_at::text, updated_at::text
                FROM {safe_table}
                ORDER BY
                    CASE priority WHEN 'Tinggi' THEN 0 WHEN 'Sedang' THEN 1 ELSE 2 END,
                    updated_at DESC
                LIMIT %s
                """,
                (int(limit),),
            )
            rows = cur.fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        items.append({
            "memory_id": row[0],
            "kind": row[1],
            "category": row[2],
            "priority": row[3],
            "memory": row[4],
            "source": row[5],
            "usage_count": row[6],
            "metadata": row[7] if isinstance(row[7], dict) else {},
            "created_at": row[8],
            "updated_at": row[9],
        })
    return True, items, f"{len(items)} AI Core Memory dimuat dari Supabase ({table})."


def test_core_memory_connection(secrets: Any = None) -> Dict[str, Any]:
    cfg = get_storage_config(secrets)
    if cfg.get("configured") != "true" or cfg.get("mode") != "postgres":
        return {"ok": False, "message": "Database PostgreSQL/Supabase belum dikonfigurasi.", "table": _core_memory_table(cfg)}
    table = _core_memory_table(cfg)
    with _connect_postgres(cfg) as conn:
        _ensure_core_memory_table(conn, table)
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {_safe_table_name(table)}")
            total = int(cur.fetchone()[0])
    return {"ok": True, "message": f"AI Core Memory aktif. Total memory: {total}.", "table": table, "total": total}
