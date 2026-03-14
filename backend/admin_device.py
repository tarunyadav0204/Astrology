"""
Admin device allowlist: per-user binding. Only (userid, device_id) pairs in the table can access admin routes.
Each admin registers their own devices; reusing another admin's device ID does not grant access.
"""
import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.environ.get("ASTROLOGY_DB_PATH") or os.path.join(_BACKEND_DIR, "astrology.db")
_TABLE = "admin_allowed_devices"


def ensure_table():
    """Create or migrate admin_allowed_devices: (userid, device_id) per-user binding."""
    conn = sqlite3.connect(_DB_PATH)
    try:
        cur = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (_TABLE,))
        exists = cur.fetchone() is not None
        if not exists:
            conn.execute(
                f"""
                CREATE TABLE {_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userid INTEGER NOT NULL,
                    device_id TEXT NOT NULL,
                    label TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(userid, device_id)
                )
                """
            )
            conn.commit()
            return
        # Check if we have userid column (new schema)
        cur = conn.execute(f"PRAGMA table_info({_TABLE})")
        columns = [row[1] for row in cur.fetchall()]
        if "userid" in columns:
            conn.commit()
            return
        # Migrate: old table (device_id UNIQUE) -> new (userid, device_id UNIQUE)
        admin_userid = None
        cur = conn.execute("SELECT userid FROM users WHERE role = 'admin' LIMIT 1")
        row = cur.fetchone()
        if row:
            admin_userid = row[0]
        conn.execute(
            f"""
            CREATE TABLE {_TABLE}_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                label TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(userid, device_id)
            )
            """
        )
        if admin_userid is not None:
            conn.execute(
                f"INSERT INTO {_TABLE}_new (id, userid, device_id, label, created_at) SELECT id, ?, device_id, label, created_at FROM {_TABLE}",
                (admin_userid,),
            )
        conn.execute(f"DROP TABLE {_TABLE}")
        conn.execute(f"ALTER TABLE {_TABLE}_new RENAME TO {_TABLE}")
        conn.commit()
    finally:
        conn.close()


def get_user_id_and_role_from_token(token: str) -> tuple[int | None, str | None]:
    """Decode JWT, get sub (phone), query users for userid and role. Returns (userid, role) or (None, None)."""
    import jwt
    secret = os.getenv("JWT_SECRET")
    if not secret or not token:
        return None, None
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        phone = payload.get("sub")
        if not phone:
            return None, None
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.execute("SELECT userid, role FROM users WHERE phone = ?", (phone,))
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        return None, None
    except Exception:
        return None, None


def get_user_role_from_token(token: str) -> str | None:
    """Backward compat: returns role only."""
    _, role = get_user_id_and_role_from_token(token)
    return role


def is_device_allowed_for_user(userid: int, device_id: str) -> bool:
    """True if (userid, device_id) is in the allowlist. Empty table = bootstrap (allow all)."""
    if not (device_id and str(device_id).strip()):
        return False
    device_id = str(device_id).strip()
    try:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.execute(f"SELECT 1 FROM {_TABLE} LIMIT 1")
        if cur.fetchone() is None:
            conn.close()
            return True  # bootstrap: no rows = allow all
        cur = conn.execute(
            f"SELECT 1 FROM {_TABLE} WHERE userid = ? AND device_id = ?",
            (userid, device_id),
        )
        allowed = cur.fetchone() is not None
        conn.close()
        return allowed
    except Exception as e:
        logger.warning("admin_device: is_device_allowed_for_user failed: %s", e)
        return False


def list_allowed_devices(userid: int) -> list[dict]:
    """Return list of allowed devices for this user only."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.execute(
            f"SELECT id, device_id, label, created_at FROM {_TABLE} WHERE userid = ? ORDER BY created_at DESC",
            (userid,),
        )
        rows = cur.fetchall()
        conn.close()
        return [
            {"id": r[0], "device_id": r[1], "label": r[2] or "", "created_at": r[3] or ""}
            for r in rows
        ]
    except Exception as e:
        logger.warning("admin_device: list_allowed_devices failed: %s", e)
        return []


def add_allowed_device(device_id: str, label: str | None, userid: int) -> bool:
    """Add (userid, device_id) to allowlist. Returns True if added, False if already exists."""
    if not (device_id and str(device_id).strip()):
        return False
    device_id = str(device_id).strip()
    try:
        conn = sqlite3.connect(_DB_PATH)
        try:
            conn.execute(
                f"INSERT INTO {_TABLE} (userid, device_id, label) VALUES (?, ?, ?)",
                (userid, device_id, (label or "").strip() or None),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    except Exception as e:
        logger.warning("admin_device: add_allowed_device failed: %s", e)
        return False


def register_this_device(device_id: str, userid: int) -> tuple[bool, str]:
    """
    One-click register only from first device (bootstrap) or idempotent confirm.
    Returns (success, message). If user already has >= 1 other device and this one is new, returns (False, 'use_approved_device').
    """
    if not (device_id and str(device_id).strip()):
        return False, "missing_device_id"
    device_id = str(device_id).strip()
    if _device_exists_for_user(userid, device_id):
        return True, "already_registered"
    devices = list_allowed_devices(userid)
    if len(devices) >= 1:
        return False, "use_approved_device"  # must add new devices from an already-approved device
    label = f"Registered {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    if add_allowed_device(device_id, label, userid):
        return True, "registered"
    return True, "already_registered"


def _device_exists_for_user(userid: int, device_id: str) -> bool:
    try:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.execute(
            f"SELECT 1 FROM {_TABLE} WHERE userid = ? AND device_id = ?",
            (userid, device_id),
        )
        ok = cur.fetchone() is not None
        conn.close()
        return ok
    except Exception:
        return False


def remove_allowed_device(device_id: str, userid: int) -> bool:
    """Remove (userid, device_id) from allowlist. Only own devices."""
    if not (device_id and str(device_id).strip()):
        return False
    try:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.execute(
            f"DELETE FROM {_TABLE} WHERE userid = ? AND device_id = ?",
            (userid, str(device_id).strip()),
        )
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted
    except Exception as e:
        logger.warning("admin_device: remove_allowed_device failed: %s", e)
        return False


def remove_allowed_device_by_id(row_id: int, userid: int) -> bool:
    """Remove row by id only if it belongs to this user."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.execute(
            f"DELETE FROM {_TABLE} WHERE id = ? AND userid = ?",
            (row_id, userid),
        )
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted
    except Exception as e:
        logger.warning("admin_device: remove_allowed_device_by_id failed: %s", e)
        return False


# Path that bypasses device check so admin can register from a new device
REGISTER_THIS_DEVICE_PATH = "/api/admin/register-this-device"


class AdminDeviceMiddleware:
    """Block admin requests unless (current user, X-Device-Id) is in the allowlist. Empty table = bootstrap."""
    ADMIN_PREFIXES = ("/api/admin", "/api/credits/admin", "/api/nudge/admin")

    def __init__(self, app):
        self.app = app

    def _is_admin_path(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.ADMIN_PREFIXES)

    def _is_register_path(self, path: str, method: str) -> bool:
        return method == "POST" and path.rstrip("/") == REGISTER_THIS_DEVICE_PATH.rstrip("/")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        method = scope.get("method", "")
        if method == "OPTIONS" or not self._is_admin_path(path):
            await self.app(scope, receive, send)
            return
        headers = dict((k.decode(), v.decode()) if isinstance(k, bytes) else (k, v) for k, v in scope.get("headers", []))
        auth = headers.get("authorization") or headers.get("Authorization") or ""
        if not auth.startswith("Bearer "):
            await self._send_403(scope, receive, send, "Missing or invalid authorization")
            return
        token = auth[7:].strip()
        userid, role = get_user_id_and_role_from_token(token)
        if role != "admin" or userid is None:
            await self._send_403(scope, receive, send, "Admin access required")
            return
        device_id = (headers.get("x-device-id") or headers.get("X-Device-Id") or "").strip()
        if self._is_register_path(path, method):
            await self.app(scope, receive, send)
            return
        if is_device_allowed_for_user(userid, device_id):
            await self.app(scope, receive, send)
            return
        await self._send_403(scope, receive, send, "Device not allowed", device_id=device_id or None, user_id=userid)
        return

    async def _send_403(self, scope, receive, send, message, device_id=None, user_id=None):
        from starlette.responses import JSONResponse
        body = {"detail": message}
        if device_id is not None:
            body["device_id"] = device_id
        if user_id is not None:
            body["user_id"] = user_id
        response = JSONResponse(status_code=403, content=body)
        await response(scope, receive, send)
