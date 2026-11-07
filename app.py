from __future__ import annotations

import io
import base64
import shutil
import subprocess
import tempfile
import json
import os
import re
import sqlite3
import hashlib
import hmac
import secrets
import time
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
from services.travel_provider_adapters import flight_search_alternatives as _build_flight_search_alternatives, normalise_metno_forecast, validate_weather_contact, provider_cache_until_epoch
from services.env_config import load_env_file

ROOT = Path(__file__).resolve().parent
load_env_file(ROOT / ".env")
FRONTEND_DIR = ROOT / "frontend"
INSTANCE_DIR = ROOT / "instance"
DEFAULT_DATABASE = INSTANCE_DIR / "citypulsex.sqlite3"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

app = Flask("citypulsex", static_folder=None)
if os.environ.get("CITYPULSEX_TRUST_PROXY", "0").strip().lower() in {"1", "true", "yes"}:
    # Enable only when exactly one trusted reverse proxy overwrites X-Forwarded-* headers.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0)
app.config.update(
    DATABASE=os.environ.get("CITYPULSEX_DB", str(DEFAULT_DATABASE)),
    MAX_CONTENT_LENGTH=25 * 1024 * 1024,
    JSON_SORT_KEYS=False,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def database_path() -> Path:
    return Path(app.config.get("DATABASE", str(DEFAULT_DATABASE))).expanduser().resolve()


class ClosingConnection(sqlite3.Connection):
    """Commit/rollback with the SQLite context manager, then always close."""
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect_db() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def init_database() -> None:
    with connect_db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('member','admin')),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                csrf_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry ON auth_sessions(expires_at);
            CREATE TABLE IF NOT EXISTS shared_trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code_hash TEXT NOT NULL UNIQUE,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                editor_token_hash TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_shared_trips_updated ON shared_trips(updated_at);
            CREATE TABLE IF NOT EXISTS rate_limit_buckets (
                bucket_key TEXT PRIMARY KEY,
                window_start INTEGER NOT NULL,
                request_count INTEGER NOT NULL CHECK(request_count >= 1),
                expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_rate_limit_expiry ON rate_limit_buckets(expires_at);
            """
        )
        # Civic Pulse was removed from TRAVESÍA; remove its legacy local tables.
        conn.execute("DROP TABLE IF EXISTS complaints")
        conn.execute("DROP TABLE IF EXISTS incidents")
        conn.execute("DROP TABLE IF EXISTS audit_events")
        # Additive migration keeps earlier local TRAVESÍA databases usable.
        shared_columns = {row[1] for row in conn.execute("PRAGMA table_info(shared_trips)").fetchall()}
        if "editor_token_hash" not in shared_columns:
            conn.execute("ALTER TABLE shared_trips ADD COLUMN editor_token_hash TEXT NOT NULL DEFAULT ''")
        if "owner_user_id" not in shared_columns:
            conn.execute("ALTER TABLE shared_trips ADD COLUMN owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL")
        # Expired sessions and rate-limit rows can be safely removed during startup.
        conn.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (utc_now(),))
        conn.execute("DELETE FROM rate_limit_buckets WHERE expires_at <= ?", (int(time.time()),))
        admin_email = os.environ.get("CITYPULSEX_ADMIN_EMAIL", "").strip().lower()
        admin_password = os.environ.get("CITYPULSEX_ADMIN_PASSWORD", "")
        if admin_email and admin_password and len(admin_password) >= 16 and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", admin_email):
            exists = conn.execute("SELECT id FROM users WHERE email=? COLLATE NOCASE", (admin_email,)).fetchone()
            if not exists:
                conn.execute("INSERT INTO users(email,display_name,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                    (admin_email, "TRAVESÍA Administrator", generate_password_hash(admin_password), "admin", utc_now()))


def _sha256_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rate_limit_response(scope: str, limit: int, window_seconds: int, subject: str = ""):
    """Persistent fixed-window limiter. Identities are hashed; raw IPs/emails are not stored."""
    now = time.time()
    window_start = int(now // window_seconds) * window_seconds
    client_ip = request.remote_addr or "unknown"
    identity = "\0".join((scope, client_ip, str(subject).strip().casefold(), str(window_start)))
    bucket_key = _sha256_secret(identity)
    try:
        with connect_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT request_count FROM rate_limit_buckets WHERE bucket_key=?",
                (bucket_key,),
            ).fetchone()
            count = (int(row["request_count"]) if row else 0) + 1
            conn.execute(
                "INSERT INTO rate_limit_buckets(bucket_key,window_start,request_count,expires_at) "
                "VALUES(?,?,?,?) ON CONFLICT(bucket_key) DO UPDATE SET request_count=excluded.request_count",
                (bucket_key, window_start, count, window_start + window_seconds + 86400),
            )
            # Periodic cleanup without a process-local counter, so this works across workers.
            conn.execute("DELETE FROM rate_limit_buckets WHERE expires_at < ?", (int(now) - 86400,))
    except sqlite3.Error:
        app.logger.exception("Rate-limit storage is unavailable")
        response = jsonify({"error": "The service is temporarily unable to validate request limits. Please retry shortly."})
        response.status_code = 503
        response.headers["Retry-After"] = "5"
        return response
    if count <= limit:
        return None
    retry_after = max(1, int(window_start + window_seconds - now))
    response = jsonify({"error": "Too many requests. Please wait before trying again.", "retry_after_seconds": retry_after})
    response.status_code = 429
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = "0"
    return response


def _same_origin_api_request() -> bool:
    """Reject cross-site browser mutations while allowing non-browser clients without Origin."""
    fetch_site = request.headers.get("Sec-Fetch-Site", "").strip().lower()
    if fetch_site == "cross-site":
        return False
    origin = request.headers.get("Origin", "").strip()
    if not origin:
        return True
    try:
        parsed = urlparse(origin)
        expected_scheme = "https" if request.is_secure else "http"
        return bool(parsed.scheme == expected_scheme and parsed.netloc.lower() == request.host.lower())
    except ValueError:
        return False


@app.before_request
def enforce_same_origin_for_api_mutations():
    if request.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if not _same_origin_api_request():
            return jsonify({"error": "Cross-origin API mutations are not allowed."}), 403
    return None


def _session_record():
    token = request.cookies.get("citypulsex_session", "").strip()
    if not token or len(token) > 200:
        return None
    with connect_db() as conn:
        row = conn.execute("""SELECT s.id AS session_id,s.token_hash,s.csrf_hash,s.expires_at,u.id AS user_id,
            u.email,u.display_name,u.role FROM auth_sessions s JOIN users u ON u.id=s.user_id
            WHERE s.token_hash=? AND s.expires_at>?""", (_sha256_secret(token), utc_now())).fetchone()
        if row is None:
            return None
        conn.execute("UPDATE auth_sessions SET last_seen_at=? WHERE id=?", (utc_now(), row["session_id"]))
        return dict(row)


def _cookie_settings(response, token: str | None = None, csrf: str | None = None, clear: bool = False):
    secure_setting = os.environ.get("COOKIE_SECURE")
    if secure_setting is None:
        secure = os.environ.get("CITYPULSEX_ENV", "").strip().lower() == "production"
    else:
        secure = secure_setting.strip().lower() in {"1", "true", "yes"}
    max_age = 0 if clear else 14 * 24 * 60 * 60
    if token is not None or clear:
        response.set_cookie("citypulsex_session", "" if clear else token, max_age=max_age, httponly=True,
            secure=secure, samesite="Lax", path="/")
    if csrf is not None or clear:
        response.set_cookie("citypulsex_csrf", "" if clear else csrf, max_age=max_age, httponly=False,
            secure=secure, samesite="Lax", path="/")
    return response


def ensure_db_exists() -> None:
    init_database()


@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/styles.css")
def styles():
    return send_from_directory(FRONTEND_DIR, "styles.css")


@app.get("/app.js")
def javascript():
    return send_from_directory(FRONTEND_DIR, "app.js")


@app.get("/expense-ledger.js")
def expense_ledger_javascript():
    return send_from_directory(FRONTEND_DIR, "expense-ledger.js")


@app.get("/extensions.js")
def extensions_javascript():
    return send_from_directory(FRONTEND_DIR, "extensions.js")


@app.get("/pulseboard.js")
def pulseboard_javascript():
    return send_from_directory(FRONTEND_DIR, "pulseboard.js")


@app.get("/pulseboard.css")
def pulseboard_styles():
    return send_from_directory(FRONTEND_DIR, "pulseboard.css")


@app.get("/feature-upgrades.js")
def feature_upgrades_javascript():
    return send_from_directory(FRONTEND_DIR, "feature-upgrades.js")


@app.get("/globe.js")
def globe_javascript():
    return send_from_directory(FRONTEND_DIR, "globe.js")


@app.get("/providers.js")
def providers_javascript():
    return send_from_directory(FRONTEND_DIR, "providers.js")


@app.get("/glb-viewer.js")
def glb_viewer_javascript():
    return send_from_directory(FRONTEND_DIR, "glb-viewer.js")


@app.get("/companion-3d.js")
def companion_3d_javascript():
    return send_from_directory(FRONTEND_DIR, "companion-3d.js")


@app.get("/world-game.js")
def world_game_javascript():
    return send_from_directory(FRONTEND_DIR, "world-game.js")


# These three files are loaded directly by frontend/index.html. Keeping explicit
# routes prevents the friend picker and the cinematic page-scene layer from
# silently falling back to a plain page when Flask is used as the web server.
@app.get("/friend-characters.js")
def friend_characters_javascript():
    return send_from_directory(FRONTEND_DIR, "friend-characters.js")


@app.get("/cinematic.js")
def cinematic_javascript():
    return send_from_directory(FRONTEND_DIR, "cinematic.js")


@app.get("/cinematic.css")
def cinematic_styles():
    return send_from_directory(FRONTEND_DIR, "cinematic.css")


@app.get("/assets/<path:filename>")
def frontend_assets(filename: str):
    return send_from_directory(FRONTEND_DIR / "assets", filename)


@app.after_request
def set_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(self), geolocation=(self)")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    response.headers.setdefault("X-Download-Options", "noopen")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    if request.path.startswith("/api/auth/") or request.path.startswith("/api/shared-trips"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Vary"] = "Cookie"
    return response


@app.post("/api/companion/chat")
def companion_chat():
    """Optional server-side OpenAI-compatible chat adapter; never exposes the API key."""
    limited = rate_limit_response("companion-chat", 30, 600)
    if limited is not None:
        return limited
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    companion = str(data.get("companion", "Sprout")).strip()[:40] or "Sprout"
    destination = str(data.get("destination", "")).strip()[:120]
    if not message:
        return jsonify({"error": "Enter a message first."}), 400
    if len(message) > 2000:
        return jsonify({"error": "Message must be 2,000 characters or fewer."}), 400

    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    if not api_key:
        return jsonify({"configured": False, "mode": "local_fallback", "message": "The AI provider is not configured. Your companion is using the built-in local responses. Add LLM_API_KEY to the server environment to enable generative chat."}), 200
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        return jsonify({"error": "LLM_BASE_URL must be an HTTPS chat-completions endpoint."}), 400

    system_prompt = (
        f"You are {companion}, an original friendly travel companion inside TRAVESÍA. "
        "Use clear, concise English. Help users plan trips and understand places. "
        "Never invent live prices, opening hours, bookings, safety status, or weather observations, "
        "or medical/legal advice. Clearly label estimates and direct users "
        "to authoritative sources for current facts. Do not claim you performed actions you did not perform. "
        f"The user's current destination draft is: {destination or 'not specified'}."
    )
    raw_history = data.get("history", [])
    history = []
    if isinstance(raw_history, list):
        for item in raw_history[-8:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = str(item.get("content", "")).strip()[:1500]
            if role in {"user", "assistant"} and content:
                history.append({"role": role, "content": content})
    body = json.dumps({"model": model, "messages": [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": message},
    ], "temperature": 0.6, "max_tokens": 500}).encode("utf-8")
    req = Request(base_url, data=body, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
        "Accept": "application/json", "User-Agent": "TRAVESÍA/1.0",
    }, method="POST")
    try:
        with urlopen(req, timeout=20) as response:
            result = json.loads(response.read(1_000_000).decode("utf-8"))
        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("The AI provider returned an empty reply.")
        return jsonify({"configured": True, "mode": "provider", "companion": companion, "message": reply.strip()[:5000], "model": model})
    except HTTPError as exc:
        # Do not relay provider response bodies, which may contain sensitive diagnostics.
        return jsonify({"error": f"AI provider request failed (HTTP {exc.code}). Check provider configuration and server logs."}), 502
    except (URLError, TimeoutError, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
        app.logger.warning("Companion provider request failed: %s", type(exc).__name__)
        return jsonify({"error": "The AI provider could not be reached or returned an invalid response. Please retry or use the local companion fallback."}), 502


@app.post("/api/media/clip-storyboard")
def clip_storyboard():
    """Create a visual storyboard from sampled frames; never stores uploaded clips permanently."""
    record = _session_record()
    if not record:
        return jsonify({"error": "Sign in before analyzing a travel clip."}), 401
    limited = rate_limit_response("clip-storyboard", 5, 3600, str(record["user_id"]))
    if limited is not None:
        return limited
    csrf = request.headers.get("X-CSRF-Token", "")
    if not csrf or not hmac.compare_digest(_sha256_secret(csrf), record["csrf_hash"]):
        return jsonify({"error": "A valid CSRF token is required."}), 403
    if str(request.form.get("consent", "")).strip().lower() not in {"on", "true", "yes", "1"}:
        return jsonify({"error": "Confirm the sampled-frame AI-provider disclosure before uploading."}), 400
    uploaded = request.files.get("video")
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "Choose a video file first."}), 400
    filename = Path(uploaded.filename).name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".webm", ".m4v"}:
        return jsonify({"error": "Supported formats: MP4, MOV, WEBM and M4V."}), 415
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        return jsonify({"error": "Visual storyboard analysis is not configured. Set LLM_API_KEY on the server; no clip is uploaded to a third-party service until this is configured."}), 503
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        return jsonify({"error": "FFmpeg and FFprobe are required on the server for safe keyframe extraction."}), 503
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        return jsonify({"error": "LLM_BASE_URL must be an HTTPS chat-completions endpoint."}), 400
    with tempfile.TemporaryDirectory(prefix="citypulsex-clip-") as work:
        workdir = Path(work)
        source = workdir / ("source" + suffix)
        uploaded.save(source)
        try:
            meta = subprocess.run([ffprobe,"-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(source)], capture_output=True, text=True, timeout=8, check=True)
            duration = float(meta.stdout.strip())
        except (subprocess.SubprocessError, ValueError):
            return jsonify({"error": "The uploaded file is not a readable video."}), 400
        if duration <= 0 or duration > 180:
            return jsonify({"error": "For this first version, clips must be between 1 second and 3 minutes."}), 400
        timestamps = sorted(set(round(min(duration - .08, max(0, duration * fraction)), 2) for fraction in (.08,.24,.4,.56,.72,.9)))
        frame_parts = []
        for index, stamp in enumerate(timestamps):
            frame_path = workdir / f"frame-{index}.jpg"
            try:
                subprocess.run([ffmpeg,"-nostdin","-v","error","-ss",str(stamp),"-i",str(source),"-frames:v","1","-vf","scale=640:-2","-q:v","6","-y",str(frame_path)], capture_output=True, timeout=10, check=True)
            except subprocess.SubprocessError:
                continue
            if frame_path.exists() and frame_path.stat().st_size < 700_000:
                frame64 = base64.b64encode(frame_path.read_bytes()).decode("ascii")
                frame_parts.append({"type":"text","text":f"Approximate timestamp: {stamp:.2f} seconds"})
                frame_parts.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+frame64,"detail":"low"}})
        if not frame_parts:
            return jsonify({"error": "No usable frames could be extracted from this clip."}), 422
        prompt = ("Analyze only the supplied sampled video frames, not audio. Return a concise visual summary, up to five timestamped moments, a 5-shot storyboard, short caption ideas, and an optional 15-second highlight sequence. Timestamps are approximate sample positions. Do not invent dialogue, sound, location identity or events not visible. Distinguish uncertainty. Return readable Markdown.")
        body = json.dumps({"model":model,"messages":[{"role":"system","content":"You are a careful visual travel-story editor. Only describe evidence in the provided frames."},{"role":"user","content":[{"type":"text","text":prompt},*frame_parts]}],"temperature":0.3,"max_tokens":900}).encode("utf-8")
        req = Request(base_url,data=body,headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json","Accept":"application/json","User-Agent":"TRAVESÍA/1.0"},method="POST")
        try:
            with urlopen(req, timeout=45) as response:
                result=json.loads(response.read(1_500_000).decode("utf-8"))
            analysis=result.get("choices",[{}])[0].get("message",{}).get("content","")
            if not isinstance(analysis,str) or not analysis.strip():
                raise ValueError("Empty visual analysis")
            return jsonify({"ok":True,"analysis":analysis.strip()[:12000],"duration_seconds":round(duration,2),"sampled_timestamps":timestamps,"frames_analyzed":len([p for p in frame_parts if p.get("type")=="image_url"]),"audio_analyzed":False,"retention":"temporary upload and extracted frames are deleted after this request","model":model})
        except HTTPError as exc:
            return jsonify({"error":f"Video analysis provider returned HTTP {exc.code}. Check server configuration."}),502
        except (URLError, TimeoutError, ValueError, KeyError, IndexError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
            app.logger.warning("Clip storyboard failed: %s",type(exc).__name__)
            return jsonify({"error":"Clip analysis failed. The temporary upload was discarded; retry with a shorter MP4 or check provider logs."}),502


@app.post("/api/auth/register")
def auth_register():
    limited = rate_limit_response("auth-register", 8, 3600)
    if limited is not None:
        return limited
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    display_name = str(data.get("display_name", data.get("name", ""))).strip()[:80]
    password = str(data.get("password", ""))
    if not re.fullmatch(r"[^@\s]{1,100}@[^@\s]{1,100}\.[^@\s]{2,30}", email):
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(display_name) < 2:
        return jsonify({"error": "Display name must contain at least two characters."}), 400
    if len(password) < 12 or len(password) > 256:
        return jsonify({"error": "Password must be 12–256 characters. Use a unique passphrase."}), 400
    try:
        with connect_db() as conn:
            conn.execute("INSERT INTO users(email,display_name,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                (email, display_name, generate_password_hash(password), "member", utc_now()))
    except sqlite3.IntegrityError:
        return jsonify({"error": "An account with that email already exists. Sign in instead."}), 409
    return _create_login_response(email, password)


def _create_login_response(email: str, password: str):
    with connect_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=? COLLATE NOCASE", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Email or password is incorrect."}), 401
        previous_token = request.cookies.get("citypulsex_session", "").strip()
        if previous_token:
            conn.execute("DELETE FROM auth_sessions WHERE token_hash=?", (_sha256_secret(previous_token),))
        token, csrf = secrets.token_urlsafe(40), secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=14)).isoformat(timespec="microseconds")
        conn.execute("INSERT INTO auth_sessions(token_hash,user_id,csrf_hash,created_at,expires_at,last_seen_at) VALUES(?,?,?,?,?,?)",
            (_sha256_secret(token), user["id"], _sha256_secret(csrf), now.isoformat(timespec="microseconds"), expires, now.isoformat(timespec="microseconds")))
    response = jsonify({"ok": True, "user": {"id": user["id"], "email": user["email"], "display_name": user["display_name"], "role": user["role"]}, "csrf_token": csrf})
    response = _cookie_settings(response, token=token, csrf=csrf)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/auth/login")
def auth_login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    limited = rate_limit_response("auth-login-ip", 30, 900)
    if limited is not None:
        return limited
    limited = rate_limit_response("auth-login-account", 20, 900, email)
    if limited is not None:
        return limited
    password = str(data.get("password", ""))
    if not email or not password or len(email) > 120 or len(password) > 256:
        return jsonify({"error": "Enter your email and password."}), 400
    return _create_login_response(email, password)


@app.get("/api/auth/me")
def auth_me():
    record = _session_record()
    if not record:
        response = jsonify({"authenticated": False})
        response.headers["Cache-Control"] = "no-store"
        return response
    csrf = request.cookies.get("citypulsex_csrf", "")
    response = None
    if not csrf or not hmac.compare_digest(_sha256_secret(csrf), record["csrf_hash"]):
        csrf = secrets.token_urlsafe(32)
        with connect_db() as conn:
            conn.execute("UPDATE auth_sessions SET csrf_hash=? WHERE id=?", (_sha256_secret(csrf), record["session_id"]))
        response = jsonify({"authenticated": True, "user": {"id":record["user_id"], "email":record["email"], "display_name":record["display_name"], "role":record["role"]}, "csrf_token":csrf})
        response = _cookie_settings(response, csrf=csrf)
    else:
        response = jsonify({"authenticated": True, "user": {"id":record["user_id"], "email":record["email"], "display_name":record["display_name"], "role":record["role"]}, "csrf_token":csrf})
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/auth/logout")
def auth_logout():
    token = request.cookies.get("citypulsex_session", "").strip()
    record = _session_record() if token else None
    if record:
        csrf = request.headers.get("X-CSRF-Token", "").strip()
        if not csrf or not hmac.compare_digest(_sha256_secret(csrf), record["csrf_hash"]):
            return jsonify({"error": "A valid CSRF token is required to sign out."}), 403
    if token:
        with connect_db() as conn:
            conn.execute("DELETE FROM auth_sessions WHERE token_hash=?", (_sha256_secret(token),))
    response = jsonify({"ok": True})
    response = _cookie_settings(response, clear=True)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health():
    try:
        with connect_db() as conn:
            conn.execute("SELECT 1").fetchone()
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required = {"users", "auth_sessions", "shared_trips", "rate_limit_buckets"}
            db_status = "ok" if required.issubset(tables) else "schema_incomplete"
    except (sqlite3.Error, OSError):
        db_status="unavailable"
    code=200 if db_status=="ok" else 503
    return jsonify({"status":"ok" if db_status=="ok" else "degraded","service":"citypulsex",
        "pilot_scope":"Global travel discovery and playful trip-planning demo","data_mode":"provider-backed plus clearly labelled illustrative planning",
        "database":db_status,"authentication":"available","shared_trip_sync":"editor-token protected","time":utc_now()}),code

@app.get("/api/capabilities")
def capabilities():
    return jsonify({
        "modules": ["world_explorer", "trip_planning", "trip_pulseboard", "explainable_squad_destination_fit", "external_booking_handoffs", "mobility_comparison", "stays_and_experiences", "companion", "squad_planning", "expense_split", "world_scene_scenarios"],
        "connected_live_providers": [name for name, ok in [("Amadeus flight offers", bool(os.environ.get("AMADEUS_CLIENT_ID") and os.environ.get("AMADEUS_CLIENT_SECRET"))), ("MapTiler satellite imagery", bool(os.environ.get("MAPTILER_API_KEY"))), ("MET Norway forecast", bool(validate_weather_contact(os.environ.get("CITYPULSEX_CONTACT_EMAIL", ""), os.environ.get("CITYPULSEX_CONTACT_URL", ""))))] if ok],
        "available_public_sources": [{"name":"NASA GIBS global satellite imagery","status":"public_no_key_source_configured_network_delivery_not_verified_here"}],
        "shared_trip_sync": "server-side SQLite with separate high-entropy read code and editor token; cross-user edits require the editor token",
        "authentication": "server-side sessions, password hashing, HttpOnly session cookie, CSRF protection for administrator mutations, member/admin roles",
        "official_links": {"irctc": "https://www.irctc.co.in/eticket/", "ixigo_trains": "https://www.ixigo.com/trains", "flights": "https://www.google.com/travel/flights", "ixigo_flights": "https://www.ixigo.com/flights"},
        "note": "Live in-app flight offers require authorised Amadeus credentials; without them the app provides no-key Google Flights, KAYAK and ixigo Flights hand-offs. Train search and checkout open official IRCTC or IRCTC-listed ixigo; credentials and payment stay with the provider. NASA GIBS supplies lower-detail global daily satellite imagery without a key; licensed MapTiler is an optional higher-detail layer. Travel scenario outputs remain local and illustrative unless an authorised source is configured."
    })


def shared_trip_state(payload: Any) -> tuple[dict[str, Any] | None, dict[str, str]]:
    """Validate a compact, privacy-conscious shared trip payload before persistence."""
    errors: dict[str, str] = {}
    if not isinstance(payload, dict):
        return None, {"state": "Shared trip state must be a JSON object."}
    people_raw = payload.get("people", [])
    expenses_raw = payload.get("expenses", [])
    avatars_raw = payload.get("avatars", {})
    characters_raw = payload.get("characters", {})
    if not isinstance(people_raw, list) or not 1 <= len(people_raw) <= 12:
        errors["people"] = "Provide between 1 and 12 friend names."
        people: list[str] = []
    else:
        people = [str(p).strip()[:60] for p in people_raw]
        if any(not p for p in people):
            errors["people"] = "Friend names cannot be blank."
        elif len({p.casefold() for p in people}) != len(people):
            errors["people"] = "Friend names must be unique."
    if not isinstance(expenses_raw, list) or len(expenses_raw) > 500:
        errors["expenses"] = "Provide no more than 500 expenses."
        expenses_raw = []
    if not isinstance(avatars_raw, dict):
        errors["avatars"] = "Friend portraits must be a name-to-image object."
        avatars_raw = {}
    avatars: dict[str, str] = {}
    if people:
        for name, image in avatars_raw.items():
            if name not in people:
                continue
            allowed_data_prefixes = ("data:image/webp;base64,", "data:image/png;base64,", "data:image/jpeg;base64,")
            if not isinstance(image, str) or not image.startswith(allowed_data_prefixes) or len(image) > 180_000:
                errors["avatars"] = "Each friend portrait must be a small PNG, JPEG or WebP image (maximum 180 KB encoded)."
                break
            avatars[name] = image
    allowed_character_ids = {
        "traveller", "sprout", "pip", "roo", "mira", "orbit", "paws",
        "pikachu", "bulbasaur", "iron-man", "spider-man", "harry-potter", "hermione",
    }
    if not isinstance(characters_raw, dict):
        errors["characters"] = "Friend characters must be a name-to-character object."
        characters_raw = {}
    characters: dict[str, str] = {}
    character_owners: dict[str, str] = {}
    if people:
        for name, character_id in characters_raw.items():
            if name not in people:
                continue
            if not isinstance(character_id, str) or character_id not in allowed_character_ids:
                errors["characters"] = "Choose a character from the TRAVESÍA character library."
                break
            if character_id in character_owners:
                errors["characters"] = f"Each friend must have a different character; {character_id} is assigned more than once."
                break
            characters[name] = character_id
            character_owners[character_id] = name
    expenses: list[dict[str, Any]] = []
    for index, item in enumerate(expenses_raw):
        if not isinstance(item, dict):
            errors[f"expenses[{index}]"] = "Each expense must be an object."
            continue
        description = str(item.get("description", "Expense")).strip()[:100]
        payer = str(item.get("paidBy", ""))
        participants = item.get("splitWith", [])
        try:
            amount = round(float(item.get("amount", 0)), 2)
        except (TypeError, ValueError):
            amount = 0
        if not description or not (0 < amount <= 100_000_000) or payer not in people:
            errors[f"expenses[{index}]"] = "Expense needs a description, positive amount, and valid payer."
            continue
        if not isinstance(participants, list):
            errors[f"expenses[{index}]"] = "Expense participants must be a list."
            continue
        split_with = list(dict.fromkeys(str(p) for p in participants if str(p) in people))
        if not split_with:
            errors[f"expenses[{index}]"] = "Each expense must have at least one valid participant."
            continue
        expenses.append({
            "id": str(item.get("id") or secrets.token_hex(8))[:80],
            "description": description, "amount": amount, "paidBy": payer,
            "splitWith": split_with,
            "createdAt": str(item.get("createdAt") or utc_now())[:40],
        })
    if errors:
        return None, errors
    return {"people": people, "expenses": expenses, "avatars": avatars, "characters": characters}, {}


def shared_trip_code_hash(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


@app.post("/api/shared-trips")
def create_shared_trip():
    limited = rate_limit_response("shared-trip-create", 12, 3600)
    if limited is not None:
        return limited
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "Our TRAVESÍA trip")).strip()[:80]
    if not name:
        return jsonify({"error": "Give your shared trip a name."}), 400
    clean, errors = shared_trip_state(data.get("state", {}))
    if errors:
        return jsonify({"error": "Shared trip state did not pass validation.", "fields": errors}), 400
    code = secrets.token_hex(16).upper()
    editor_token = secrets.token_urlsafe(36)
    now = utc_now()
    owner = _session_record()
    with connect_db() as conn:
        cur = conn.execute(
            "INSERT INTO shared_trips(name, code_hash, state_json, created_at, updated_at, owner_user_id, editor_token_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, shared_trip_code_hash(code), json.dumps(clean, separators=(",", ":")), now, now,
             owner["user_id"] if owner else None, _sha256_secret(editor_token)),
        )
        trip_id = int(cur.lastrowid)
    return jsonify({"ok": True, "id": trip_id, "name": name, "share_code": code, "editor_token": editor_token,
        "state": clean, "updated_at": now,
        "security_note": "The trip code is read-only. The separate editor token grants write access; share it only with collaborators you trust. The token is shown once."}), 201


@app.get("/api/shared-trips/<share_code>")
def get_shared_trip(share_code: str):
    limited = rate_limit_response("shared-trip-read", 120, 60)
    if limited is not None:
        return limited
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,64}", share_code.strip()):
        return jsonify({"error": "Shared trip not found. Check the code."}), 404
    with connect_db() as conn:
        row = conn.execute("SELECT id, name, state_json, created_at, updated_at FROM shared_trips WHERE code_hash=?", (shared_trip_code_hash(share_code),)).fetchone()
    if row is None:
        return jsonify({"error": "Shared trip not found. Check the code."}), 404
    return jsonify({"ok": True, "id": row["id"], "name": row["name"], "state": json.loads(row["state_json"]), "created_at": row["created_at"], "updated_at": row["updated_at"]})


@app.put("/api/shared-trips/<share_code>")
def update_shared_trip(share_code: str):
    limited = rate_limit_response("shared-trip-update", 60, 900)
    if limited is not None:
        return limited
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,64}", share_code.strip()):
        return jsonify({"error": "Shared trip not found. Check the code."}), 404
    data = request.get_json(silent=True) or {}
    clean, errors = shared_trip_state(data.get("state", {}))
    if errors:
        return jsonify({"error": "Shared trip state did not pass validation.", "fields": errors}), 400
    now = utc_now()
    expected = str(data.get("expected_updated_at", "")).strip()
    if not expected:
        return jsonify({"error": "A current updated_at value is required to prevent overwriting another collaborator's changes."}), 428
    with connect_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute("SELECT id, name, updated_at, editor_token_hash FROM shared_trips WHERE code_hash=?", (shared_trip_code_hash(share_code),)).fetchone()
        if current is None:
            return jsonify({"error": "Shared trip not found. Check the code."}), 404
        editor_token = request.headers.get("X-Shared-Trip-Editor", "").strip()
        stored_editor_hash = current["editor_token_hash"] or ""
        if not stored_editor_hash or not editor_token or not hmac.compare_digest(_sha256_secret(editor_token), stored_editor_hash):
            return jsonify({"error": "Read-only access. A valid separate editor token is required to change this trip."}), 403
        if expected and expected != current["updated_at"]:
            return jsonify({"error": "This shared trip changed on another device. Refresh it before saving so another friend's update is not overwritten.", "conflict": True, "updated_at": current["updated_at"]}), 409
        conn.execute("UPDATE shared_trips SET state_json=?, updated_at=? WHERE id=?", (json.dumps(clean, separators=(",", ":")), now, current["id"]))
        row = conn.execute("SELECT id, name FROM shared_trips WHERE id=?", (current["id"],)).fetchone()
    return jsonify({"ok": True, "id": row["id"], "name": row["name"], "updated_at": now, "state": clean})


_amadeus_token_cache: dict[str, Any] = {"token": "", "expires_at": 0.0, "base_url": ""}

def flight_search_alternatives(origin: str, destination: str, departure: str, return_date: str, adults: int) -> list[dict[str, str]]:
    """Credential-free live search hand-offs; never synthetic fare results."""
    return _build_flight_search_alternatives(origin, destination, departure, return_date, adults)


def _amadeus_access_token():
    client_id = os.environ.get("AMADEUS_CLIENT_ID", "").strip()
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET", "").strip()
    base_url = os.environ.get("AMADEUS_BASE_URL", "https://test.api.amadeus.com").strip().rstrip("/")
    parsed = urlparse(base_url)
    if not client_id or not client_secret:
        raise RuntimeError("amadeus_not_configured")
    if parsed.scheme != "https" or parsed.hostname not in {"api.amadeus.com", "test.api.amadeus.com"}:
        raise ValueError("AMADEUS_BASE_URL must be the official Amadeus production or test HTTPS host.")
    if _amadeus_token_cache.get("base_url") == base_url and _amadeus_token_cache.get("expires_at", 0) > datetime.now(timezone.utc).timestamp() + 45:
        return _amadeus_token_cache["token"], base_url
    body = urlencode({"grant_type":"client_credentials", "client_id":client_id, "client_secret":client_secret}).encode()
    req = Request(base_url + "/v1/security/oauth2/token", data=body, headers={"Content-Type":"application/x-www-form-urlencoded", "Accept":"application/json", "User-Agent":"TRAVESÍA/1.0"}, method="POST")
    with urlopen(req, timeout=18) as resp:
        payload = json.loads(resp.read(1_000_000).decode("utf-8"))
    token = str(payload.get("access_token", ""))
    expires_in = max(60, min(3600, int(payload.get("expires_in", 1700))))
    if not token:
        raise ValueError("Amadeus returned no access token.")
    _amadeus_token_cache.update({"token":token, "expires_at":datetime.now(timezone.utc).timestamp()+expires_in, "base_url":base_url})
    return token, base_url


@app.post("/api/travel/flights/offers")
def travel_flight_offers():
    limited = rate_limit_response("flight-search", 30, 60)
    if limited is not None:
        return limited
    data = request.get_json(silent=True) or {}
    origin = str(data.get("origin", "")).strip().upper()
    destination = str(data.get("destination", "")).strip().upper()
    departure = str(data.get("departure_date", "")).strip()
    return_date = str(data.get("return_date", "")).strip()
    try: adults = int(data.get("adults", 1))
    except (TypeError, ValueError): adults = 0
    if not re.fullmatch(r"[A-Z]{3}", origin) or not re.fullmatch(r"[A-Z]{3}", destination) or origin == destination:
        return jsonify({"error":"Enter two different 3-letter IATA airport/city codes, such as NAG and GOI."}), 400
    try:
        depart_day = datetime.strptime(departure, "%Y-%m-%d").date()
        if depart_day < datetime.now(timezone.utc).date(): raise ValueError
        if return_date:
            return_day = datetime.strptime(return_date, "%Y-%m-%d").date()
            if return_day < depart_day: raise ValueError
    except ValueError:
        return jsonify({"error":"Departure date must be today or later. Return date must be on or after departure."}), 400
    if adults < 1 or adults > 9:
        return jsonify({"error":"Choose between 1 and 9 adult travellers."}), 400
    if len(str(data.get("currency", "INR"))) != 3 or not str(data.get("currency", "INR")).isalpha():
        return jsonify({"error":"Currency must be a 3-letter currency code."}), 400
    try:
        token, base_url = _amadeus_access_token()
    except RuntimeError:
        return jsonify({"error":"In-app flight offers need authorised Amadeus credentials. Open current results through the provider hand-offs below; these are not in-app offers.", "data_mode":"not_configured", "docs":"https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search", "alternatives":flight_search_alternatives(origin,destination,departure,return_date,adults)}), 503
    except HTTPError as exc:
        app.logger.warning("Amadeus token request failed: HTTP %s", exc.code)
        return jsonify({"error":"Amadeus authentication failed. Check the provider key, secret and environment. You can still open current external search pages.", "data_mode":"provider_error", "alternatives":flight_search_alternatives(origin,destination,departure,return_date,adults)}), 502
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        app.logger.warning("Amadeus authentication error: %s", type(exc).__name__)
        return jsonify({"error":"Could not authenticate with Amadeus. Check provider availability and configuration. You can still open current external search pages.", "data_mode":"provider_error", "alternatives":flight_search_alternatives(origin,destination,departure,return_date,adults)}), 502
    params = {"originLocationCode":origin,"destinationLocationCode":destination,"departureDate":departure,"adults":adults,
              "currencyCode":str(data.get("currency","INR")).upper(),"max":min(20,max(1,int(data.get("limit",10)) if str(data.get("limit",10)).isdigit() else 10))}
    if return_date: params["returnDate"] = return_date
    req = Request(base_url + "/v2/shopping/flight-offers?" + urlencode(params), headers={"Authorization":f"Bearer {token}","Accept":"application/json","User-Agent":"TRAVESÍA/1.0"})
    try:
        with urlopen(req, timeout=22) as resp:
            payload = json.loads(resp.read(3_000_000).decode("utf-8"))
        dictionaries = payload.get("dictionaries", {})
        carriers = dictionaries.get("carriers", {}) if isinstance(dictionaries, dict) else {}
        results = []
        for offer in payload.get("data", [])[:20]:
            itinerary_rows = []
            for itinerary in offer.get("itineraries", []):
                segments=[]
                for seg in itinerary.get("segments", []):
                    segments.append({"from":seg.get("departure",{}).get("iataCode"),"to":seg.get("arrival",{}).get("iataCode"),
                        "departure_at":seg.get("departure",{}).get("at"),"arrival_at":seg.get("arrival",{}).get("at"),
                        "carrier":carriers.get(seg.get("carrierCode"),seg.get("carrierCode")),"flight_number":seg.get("number"),"duration":seg.get("duration")})
                itinerary_rows.append({"duration":itinerary.get("duration"),"segments":segments})
            price=offer.get("price",{})
            results.append({"id":offer.get("id"),"price_total":price.get("grandTotal",price.get("total")),"currency":price.get("currency",params["currencyCode"]),
                "bookable_seats":offer.get("numberOfBookableSeats"),"one_way":offer.get("oneWay"),"itineraries":itinerary_rows})
        return jsonify({"source":"Amadeus Flight Offers Search API","data_mode":"provider_test_response" if "test.api.amadeus.com" in base_url else "live_provider_response",
            "retrieved_at":utc_now(),"route":{"origin":origin,"destination":destination,"departure_date":departure,"return_date":return_date or None,"adults":adults},
            "count":len(results),"offers":results,"alternatives":flight_search_alternatives(origin,destination,departure,return_date,adults),"disclaimer":"Provider offers are indicative and may change. Confirm all terms and final price with the authorised seller before purchase. TRAVESÍA does not issue tickets. External search links are hand-offs, not Amadeus inventory."})
    except HTTPError as exc:
        app.logger.warning("Amadeus flight search failed: HTTP %s", exc.code)
        return jsonify({"error":f"The travel provider rejected the search (HTTP {exc.code}). Check airport codes, dates, credentials and API entitlements.", "data_mode":"provider_error", "alternatives":flight_search_alternatives(origin,destination,departure,return_date,adults)}), 502
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError, TypeError) as exc:
        app.logger.warning("Amadeus flight search error: %s", type(exc).__name__)
        return jsonify({"error":"The flight provider could not be reached or returned invalid data. Please retry or use an external search hand-off.", "data_mode":"provider_error", "alternatives":flight_search_alternatives(origin,destination,departure,return_date,adults)}), 502


_weather_cache: dict[tuple[float,float,int,str], dict[str, Any]] = {}

@app.get("/api/travel/weather")
def travel_weather():
    try:
        lat=float(request.args.get("latitude", "")); lon=float(request.args.get("longitude", ""))
        forecast_days=int(request.args.get("forecast_days", "3"))
    except (TypeError, ValueError):
        return jsonify({"error":"Latitude, longitude and forecast days must be numeric."}), 400
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error":"Latitude must be −90 to 90 and longitude −180 to 180."}), 400
    if not 1 <= forecast_days <= 7:
        return jsonify({"error":"Forecast days must be between 1 and 7."}), 400
    contact=validate_weather_contact(os.environ.get("CITYPULSEX_CONTACT_EMAIL", ""), os.environ.get("CITYPULSEX_CONTACT_URL", ""))
    allow_open_meteo=os.environ.get("WEATHER_ALLOW_OPEN_METEO_FREE","1").strip().lower() not in {"0","false","no","off"}
    provider_mode="metno" if contact else ("open_meteo_noncommercial" if allow_open_meteo else "provider_disabled")
    key=(round(lat,3),round(lon,3),forecast_days,provider_mode)
    now_ts=datetime.now(timezone.utc).timestamp()
    cached=_weather_cache.get(key)
    if cached and now_ts < cached.get("cache_until_epoch", cached["cached_epoch"] + 15*60):
        body=dict(cached["body"]); body["data_mode"]="cached_recent_provider_response"; body["cache_age_seconds"]=int(now_ts-cached["cached_epoch"]); body["stale"]=False
        return jsonify(body)
    params=urlencode({"latitude":lat,"longitude":lon,"current":"temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
        "daily":"weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max","forecast_days":forecast_days,"timezone":"auto"})
    # MET Norway can be used commercially under CC BY 4.0, but requires a truthful identifying
    # User-Agent with contact info. Configure an email or public contact URL to enable it.
    if contact:
        metno_url="https://api.met.no/weatherapi/locationforecast/2.0/compact?"+urlencode({"lat":lat,"lon":lon})
        metno_req=Request(metno_url,headers={"Accept":"application/json","User-Agent":f"TRAVESÍA/1.2 (contact: {contact})"})
        try:
            with urlopen(metno_req,timeout=12) as resp:
                metno_raw=resp.read(1_000_000).decode("utf-8")
                expires_header=resp.headers.get("Expires") if getattr(resp,"headers",None) is not None else None
            metno_payload=json.loads(metno_raw)
            body=normalise_metno_forecast(metno_payload,latitude=lat,longitude=lon,forecast_days=forecast_days,retrieved_at=utc_now())
            body["provider_terms_url"]="https://api.met.no/doc/TermsOfService"
            body["provider_cache_expires_at"]=datetime.fromtimestamp(provider_cache_until_epoch(expires_header,now_ts),timezone.utc).isoformat()
            _weather_cache[key]={"body":body,"cached_epoch":now_ts,"cache_until_epoch":provider_cache_until_epoch(expires_header,now_ts)}
            return jsonify(body)
        except HTTPError as exc:
            app.logger.warning("MET Norway request failed: HTTP %s",exc.code)
        except (URLError,TimeoutError,ValueError,json.JSONDecodeError,TypeError,KeyError) as exc:
            app.logger.warning("MET Norway request error: %s",type(exc).__name__)

    # Open-Meteo's free endpoint is a non-commercial fallback. Set
    # WEATHER_ALLOW_OPEN_METEO_FREE=0 for commercial deployments; MET Norway then needs contact info.
    if not allow_open_meteo:
        if cached and now_ts-cached["cached_epoch"] < 24*60*60:
            body=dict(cached["body"]); body["data_mode"]="stale_cached_weather_fallback"; body["stale"]=True
            body["cache_age_seconds"]=int(now_ts-cached["cached_epoch"]); body["cache_warning"]="Provider unavailable; cached data is not current."
            return jsonify(body)
        return jsonify({"error":"No weather provider is configured for this deployment. Set CITYPULSEX_CONTACT_EMAIL or CITYPULSEX_CONTACT_URL for MET Norway, or enable the non-commercial Open-Meteo fallback only where its terms permit it.","data_mode":"provider_not_configured"}),503
    req=Request("https://api.open-meteo.com/v1/forecast?"+params, headers={"Accept":"application/json","User-Agent":"TRAVESÍA/1.2 (travel planning; attribution shown in UI)"})
    try:
        with urlopen(req,timeout=12) as resp:
            raw_payload=resp.read(1_000_000).decode("utf-8")
            open_meteo_expires=resp.headers.get("Expires") if getattr(resp,"headers",None) is not None else None
        payload=json.loads(raw_payload)
        current=payload.get("current")
        if not isinstance(current,dict) or "time" not in current: raise ValueError("No current weather result")
        body={"source":"Open-Meteo Forecast API","source_url":"https://open-meteo.com/","data_mode":"live_provider_response",
            "retrieved_at":utc_now(),"coordinates":{"latitude":lat,"longitude":lon},"timezone":payload.get("timezone"),
            "current":current,"units":payload.get("current_units",{}),"daily":payload.get("daily",{}),"daily_units":payload.get("daily_units",{}),
            "forecast_days":forecast_days,"stale":False,
            "disclaimer":"Weather-model/current-condition output, not a local instrument reading, official emergency warning or safety assessment. Attribution is required. Open-Meteo's free API is non-commercial; commercial deployments must use a plan permitted by the provider terms."}
        cache_until=provider_cache_until_epoch(open_meteo_expires,now_ts,900)
        body["provider_cache_expires_at"]=datetime.fromtimestamp(cache_until,timezone.utc).isoformat()
        _weather_cache[key]={"body":body,"cached_epoch":now_ts,"cache_until_epoch":cache_until}
        return jsonify(body)
    except HTTPError as exc:
        app.logger.warning("Open-Meteo request failed: HTTP %s", exc.code)
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        app.logger.warning("Open-Meteo request error: %s", type(exc).__name__)
    if cached and now_ts-cached["cached_epoch"] < 24*60*60:
        body=dict(cached["body"]); body["data_mode"]="stale_cached_weather_fallback"; body["stale"]=True
        body["cache_age_seconds"]=int(now_ts-cached["cached_epoch"]); body["cache_warning"]="Weather provider unavailable; this is a previous response and must not be treated as current."
        return jsonify(body)
    return jsonify({"error":"Current weather is temporarily unavailable and no recent cached response exists. Retry when the provider is reachable.","data_mode":"provider_unavailable"}),502

@app.get("/api/maps/config")
def maps_config():
    """Expose a no-key global satellite fallback plus licensed higher-detail tiles if configured."""
    key=os.environ.get("MAPTILER_API_KEY", "").strip()
    maptiler_enabled=bool(key and key.lower() not in {"your_maptiler_api_key", "replace_me"})
    # A two-day offset allows for imagery processing latency and is returned explicitly.
    imagery_date=(datetime.now(timezone.utc).date()-timedelta(days=2)).isoformat()
    nasa_url=("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
        f"MODIS_Terra_CorrectedReflectance_TrueColor/default/{imagery_date}/"
        "GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg")
    layers=[{
        "id":"nasa_gibs", "name":"NASA daily satellite · global / lower detail",
        "provider":"NASA GIBS / EOSDIS", "tile_url":nasa_url, "max_native_zoom":9,
        "attribution":f"Imagery <a href=\"https://earthdata.nasa.gov/gibs\" target=\"_blank\" rel=\"noopener noreferrer\">NASA GIBS / EOSDIS</a> · source date {imagery_date} · MODIS Terra True Color.",
        "data_mode":"public_satellite_visualization", "imagery_date":imagery_date,
        "detail_note":"Global true-colour MODIS visualization at lower resolution than street-level commercial imagery. Clouds, darkness and processing gaps can occur."
    }]
    if maptiler_enabled:
        layers.insert(0,{
            "id":"maptiler", "name":"MapTiler satellite · higher detail", "provider":"MapTiler",
            "tile_url":f"https://api.maptiler.com/tiles/satellite-v4/{{z}}/{{x}}/{{y}}.jpg?key={key}",
            "max_native_zoom":20, "attribution":"Satellite imagery © MapTiler",
            "data_mode":"licensed_provider_tiles", "detail_note":"Higher-detail tiles subject to the configured plan, usage terms, domain restrictions and quotas."
        })
    requested=os.environ.get("MAP_DEFAULT_LAYER","road").lower()
    default_layer=("maptiler" if maptiler_enabled else "nasa_gibs") if requested=="satellite" else "road"
    selected=next((item for item in layers if item["id"]==default_layer),layers[0])
    return jsonify({"satellite_enabled":True,"provider":selected["provider"],"satellite_tile_url":selected["tile_url"],
        "attribution":selected["attribution"],"default_layer":default_layer,"road_provider":"OpenStreetMap",
        "layers":layers,"maptiler_enabled":maptiler_enabled,"nasa_fallback_available":True,"imagery_date":imagery_date,
        "imagery_handoff_url":"https://worldview.earthdata.nasa.gov/",
        "note":"NASA GIBS is the no-key global satellite fallback with date and attribution. MapTiler is optional higher-detail imagery; road tiles are never mislabeled as satellite imagery."})

@app.get("/api/providers/status")
def provider_status():
    return jsonify({
        "providers": [
            {"name": "Amadeus Flight Offers Search", "type": "flight_offer_api", "status": "configured" if os.environ.get("AMADEUS_CLIENT_ID") and os.environ.get("AMADEUS_CLIENT_SECRET") else "needs_authorised_credentials", "environment": "test" if "test.api.amadeus.com" in os.environ.get("AMADEUS_BASE_URL", "https://test.api.amadeus.com") else "production", "documentation": "https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search"},
            {"name": "MET Norway Locationforecast", "type": "global_weather_api", "status": "configured" if validate_weather_contact(os.environ.get("CITYPULSEX_CONTACT_EMAIL", ""), os.environ.get("CITYPULSEX_CONTACT_URL", "")) else "contact_info_required", "api_key_required": False, "license": "CC BY 4.0", "documentation": "https://api.met.no/doc/locationforecast/HowTO"},
            {"name": "Open-Meteo", "type": "current_weather_api", "status": "public_api_configured_noncommercial_fallback" if os.environ.get("WEATHER_ALLOW_OPEN_METEO_FREE","1").lower() not in {"0","false","no","off"} else "disabled_by_deployment_policy", "attribution_required": True, "commercial_use": "An appropriate provider plan is required; free endpoint is non-commercial."},
            {"name": "NASA GIBS daily satellite", "type": "satellite_tiles", "status": "public_fallback_available", "api_key_required": False, "documentation": "https://nasa-gibs.github.io/gibs-api-docs/"},
            {"name": "MapTiler satellite (higher detail)", "type": "satellite_tiles_premium", "status": "configured" if os.environ.get("MAPTILER_API_KEY") else "optional_licensed_key", "documentation": "https://docs.maptiler.com/cloud/api/tiles/"},
            {"name": "IRCTC", "type": "official_booking_handoff", "status": "external_link", "url": "https://www.irctc.co.in/eticket/"},
            {"name": "Google Flights", "type": "flight_search_handoff", "status": "external_link", "url": "https://www.google.com/travel/flights"},
            {"name": "ixigo Flights", "type": "flight_search_handoff", "status": "external_live_search", "api_key_required": False, "url": "https://www.ixigo.com/flights"},
            {"name": "ixigo Trains (IRCTC-listed B2C PSP)", "type": "train_booking_handoff", "status": "external_partner_checkout", "api_key_required": False, "url": "https://www.ixigo.com/trains"},
        ],
        "provider_onboarding": {
            "flights": {
                "search_status": "configured" if os.environ.get("AMADEUS_CLIENT_ID") and os.environ.get("AMADEUS_CLIENT_SECRET") else "external_search_available_no_key",
                "ticket_issuance_status": "consolidator_agreement_required",
                "production_access_url": "https://developers.amadeus.com/",
                "requirements_url": "https://github.com/amadeus4dev/developer-guides/blob/master/docs/API-Keys/moving-to-production.md",
                "note": "Amadeus production ticket issuance requires an eligible production application and a signed ticket-issuance agreement with an airline consolidator unless the operator is accredited to issue tickets."
            },
            "rail": {
                "search_status": "external_partner_search_available_no_key",
                "ticket_issuance_status": "authorised_psp_or_registered_affiliate_required_for_in_app_checkout",
                "recommended_path": "affiliate_or_associate_of_an_existing_irctc_b2c_psp",
                "current_authorised_provider_list": "https://contents.irctc.co.in/en/IRCTC%20Authorised%20Principal%20Service%20Providers.pdf",
                "policy_url": "https://contents.irctc.co.in/en/New_B2C_Policy.pdf",
                "note": "TRAVESÍA currently hands off to official IRCTC and IRCTC-listed ixigo. Direct or affiliate integration requires written PSP acceptance and IRCTC registration; no provider login or payment data is collected by TRAVESÍA."
            }
        },
        "connected_live_booking_apis": ["Amadeus Flight Offers Search"] if os.environ.get("AMADEUS_CLIENT_ID") and os.environ.get("AMADEUS_CLIENT_SECRET") else [],
        "connected_live_data_apis": (["MET Norway global forecast"] if validate_weather_contact(os.environ.get("CITYPULSEX_CONTACT_EMAIL", ""), os.environ.get("CITYPULSEX_CONTACT_URL", "")) else []) + (["Open-Meteo non-commercial fallback"] if os.environ.get("WEATHER_ALLOW_OPEN_METEO_FREE","1").lower() not in {"0","false","no","off"} else []) + ["NASA GIBS global daily satellite imagery"],
        "data_policy": "The Amadeus endpoint returns offers only when authorised credentials are configured; without them it supplies Google Flights, KAYAK and ixigo Flights hand-offs that require no TRAVESÍA API key. Train search and checkout are handed to official IRCTC or IRCTC-listed ixigo; TRAVESÍA never collects provider passwords or payment details. Weather prefers MET Norway Locationforecast when an identifying contact is configured, then optionally uses Open-Meteo only where its terms permit. NASA GIBS supplies dated, lower-resolution satellite visualizations; MapTiler is optional higher-detail imagery. TRAVESÍA does not issue tickets or claim bookings are complete."
    })


@app.post("/api/budget/allocate")
def allocate_budget():
    data = request.get_json(silent=True) or {}
    destination = str(data.get("destination", "")).strip()
    try:
        budget = float(data.get("budget", 0))
        days = int(data.get("days", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Budget and trip length must be numeric."}), 400
    currency = str(data.get("currency", "INR")).upper()
    if not destination or len(destination) > 160 or budget < 0 or budget > 100_000_000 or not 1 <= days <= 90 or len(currency) != 3:
        return jsonify({"error": "Check destination, budget, trip duration (1–90 days), and 3-letter currency code."}), 400
    ratios = {"intercity_transport": .25, "accommodation": .30, "local_transport": .12, "food": .16, "activities": .10, "reserve": .07}
    allocations = {key: round(budget * ratio, 2) for key, ratio in ratios.items()}
    return jsonify({"destination": destination, "budget": budget, "days": days, "currency": currency, "daily_budget": round(budget / days, 2), "allocations": allocations, "data_mode": "illustrative_allocation_not_a_price_quote"})


@app.post("/api/trip/fit")
def trip_fit():
    """Explainable destination shortlist for a group; all cost bands are illustrative, not live quotes."""
    data = request.get_json(silent=True) or {}
    try:
        budget = float(data.get("budget_per_person", 0))
        days = int(data.get("days", 0))
        people = int(data.get("people", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Budget, trip duration and group size must be numeric."}), 400
    if not 0 <= budget <= 10_000_000 or not 1 <= days <= 45 or not 1 <= people <= 30:
        return jsonify({"error": "Use a non-negative per-person budget, 1–45 days and 1–30 travellers."}), 400
    vibe = str(data.get("vibe", "balanced")).strip().lower()
    allowed_vibes = {"balanced", "low-cost", "culture", "nature", "beach", "adventure", "wildlife"}
    if vibe not in allowed_vibes:
        return jsonify({"error": "Choose a supported travel vibe."}), 400
    # These are transparent planning priors used for ranking only, not market prices.
    places = [
        {"name":"Goa, India", "daily_cost":2200, "days_min":2, "days_max":8, "vibes":["balanced","low-cost","beach","adventure"], "tags":["beaches","food","sunsets"], "why":"A short beach break with food and relaxed activities.", "budget_note":"Illustrative local-trip planning band; transport is not included."},
        {"name":"Jaipur, India", "daily_cost":1900, "days_min":2, "days_max":5, "vibes":["balanced","low-cost","culture","adventure"], "tags":["heritage","markets","food"], "why":"Heritage, markets and food can fit a compact itinerary.", "budget_note":"Illustrative domestic planning band; transport is not included."},
        {"name":"Bali, Indonesia", "daily_cost":3200, "days_min":3, "days_max":7, "vibes":["balanced","nature","culture"], "tags":["islands","temples","nature"], "why":"A varied island trip with nature, temples and beach time.", "budget_note":"Illustrative daily cost band; not a quote."},
        {"name":"Kyoto, Japan", "daily_cost":8500, "days_min":4, "days_max":10, "vibes":["balanced","culture","nature"], "tags":["temples","gardens","culture"], "why":"Best suited to a longer culture-and-gardens trip.", "budget_note":"Illustrative international daily spend only; flights/visa are not included."},
        {"name":"Sydney, Australia", "daily_cost":10500, "days_min":5, "days_max":12, "vibes":["balanced","beach","nature","adventure"], "tags":["harbour","coast","outdoors"], "why":"A varied city-and-coast trip that needs more time and budget.", "budget_note":"Illustrative international daily spend only; flights/visa are not included."},
        {"name":"Rome, Italy", "daily_cost":9000, "days_min":4, "days_max":10, "vibes":["balanced","culture","food"], "tags":["history","architecture","food"], "why":"A strong match for history, architecture and food-focused groups.", "budget_note":"Illustrative international daily spend only; flights/visa are not included."},
        {"name":"Antarctica", "daily_cost":35000, "days_min":7, "days_max":18, "vibes":["adventure","nature","wildlife"], "tags":["wildlife","ice","expedition"], "why":"A specialist expedition with major logistics, season and cost constraints.", "budget_note":"Very rough illustrative expedition planning band; specialist transport and permits vary."},
    ]
    ranked = []
    total_group_budget = round(budget * people, 2)
    for place in places:
        daily_budget = budget / days if days else 0
        ratio = daily_budget / place["daily_cost"] if place["daily_cost"] else 0
        budget_score = max(0, min(100, ratio * 100))
        vibe_score = 100 if vibe in place["vibes"] else (65 if "balanced" in place["vibes"] else 35)
        duration_score = 100 if place["days_min"] <= days <= place["days_max"] else max(20, 100 - min(abs(days-place["days_min"]), abs(days-place["days_max"])) * 12)
        score = round(0.55 * budget_score + 0.30 * vibe_score + 0.15 * duration_score)
        reasons = []
        reasons.append("budget fit is strong" if budget_score >= 80 else "budget needs checking" if budget_score >= 45 else "likely over the stated daily budget")
        reasons.append("matches the selected travel vibe" if vibe_score == 100 else "partial vibe match")
        reasons.append("duration suits this destination" if duration_score >= 85 else "trip length may need adjusting")
        ranked.append({**place, "score": score, "score_breakdown":{"budget_fit":round(budget_score),"vibe_fit":vibe_score,"duration_fit":duration_score}, "reasons":reasons})
    ranked.sort(key=lambda item:(item["score"], item["name"]), reverse=True)
    return jsonify({"recommendations":ranked[:5], "all_destinations":ranked, "inputs":{"budget_per_person":budget,"days":days,"people":people,"vibe":vibe,"total_group_budget":total_group_budget}, "method":{"weights":{"budget_fit":0.55,"vibe_fit":0.30,"duration_fit":0.15},"data_mode":"illustrative_heuristic_not_live_prices_or_personalised_AI","disclaimer":"Planning shortlist only. Daily-cost bands are illustrative assumptions, exclude some transport/visa/permit costs and must be verified. The score is not a guarantee of affordability or availability."}})


@app.post("/api/scenarios/run")
def run_scenario():
    """Transparent travel-scenario sandbox; never represents official routing, forecast or pricing."""
    data = request.get_json(silent=True) or {}
    scenario_type = str(data.get("scenario_type", "")).strip().lower()
    if scenario_type not in {"route", "weather", "budget", "pace"}:
        return jsonify({"error": "Choose route, weather, budget or pace."}), 400
    try:
        intensity = int(data.get("intensity", 1))
        budget = float(data.get("budget", 0))
        days = int(data.get("days", 4))
    except (TypeError, ValueError):
        return jsonify({"error": "Intensity, budget and days must be numeric."}), 400
    if not 1 <= intensity <= 10 or not 0 <= budget <= 100_000_000 or not 1 <= days <= 90:
        return jsonify({"error": "Intensity must be 1–10, budget non-negative and days 1–90."}), 400
    factors = {"route": 1.0, "weather": 1.1, "budget": 0.85, "pace": 0.75}
    index = round(min(100, intensity * factors[scenario_type] * 10), 1)
    descriptions = {
        "route": "Illustrative route-friction score. A real result needs a selected route and live transport data.",
        "weather": "Illustrative weather-flexibility score. This is not a forecast; check current provider observations.",
        "budget": "Illustrative budget pressure score based only on the intensity slider and stated budget.",
        "pace": "Illustrative itinerary-pace score. A real accessibility estimate needs activity and mobility preferences.",
    }
    return jsonify({"scenario_type": scenario_type, "intensity": intensity, "budget_assumption": budget, "days": days,
        "simulated_planning_index": index, "data_mode": "illustrative_rule_based_travel_scenario",
        "result": descriptions[scenario_type], "official_assessment": False, "official_risk_assessment": False,
        "assumptions": {"formula": "min(100, intensity × scenario_factor × 10)", "scenario_factor": factors[scenario_type], "live_route_or_weather_model_used": False}})


# Initialise the schema before the WSGI server accepts traffic. Previously this helper was
# only called by tests, leaving a freshly deployed database without its application tables.
init_database()

# The TRAVESÍA Flask app is the single WSGI entry point. Other projects are not mounted here.
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "127.0.0.1")
    print("TRAVESÍA is starting on http://%s:%s" % (host, port))
    run_simple(host, port, app, use_reloader=False, threaded=True)
