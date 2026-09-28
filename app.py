import os
import re
import secrets
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, render_template, request, session

from face_engine import FaceError, enrollment_template, verify
from rate_limit import LoginLimiter


USERNAME = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
app = Flask(__name__, instance_relative_config=True)
app.config.update(
    SECRET_KEY=os.environ.get("FACEGATE_SECRET", secrets.token_hex(32)),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
)
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
TEMPLATE_DIR = Path(app.instance_path) / "face_templates"
TEMPLATE_DIR.mkdir(exist_ok=True)
limiter = LoginLimiter()


def clean_username(value):
    value = (value or "").strip()
    if not USERNAME.fullmatch(value):
        raise ValueError("Username must be 3–32 letters, numbers, underscores, or hyphens.")
    return value.lower()


def template_path(username):
    return TEMPLATE_DIR / f"{username}.npy"


def client_key(username):
    return f"{request.remote_addr or 'unknown'}:{username}"


@app.after_request
def secure_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; media-src 'self' blob:; "
        "script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/enroll")
def enroll():
    try:
        body = request.get_json(silent=True) or {}
        username = clean_username(body.get("username"))
        path = template_path(username)
        if path.exists():
            return jsonify(error="That username is already enrolled."), 409
        template = enrollment_template(body.get("frames"))
        np.save(path, template, allow_pickle=False)
        return jsonify(message="Enrollment complete. Raw camera frames were discarded.")
    except (ValueError, FaceError) as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/login")
def login():
    try:
        body = request.get_json(silent=True) or {}
        username = clean_username(body.get("username"))
        key = client_key(username)
        allowed, retry = limiter.check(key)
        if not allowed:
            return jsonify(error=f"Too many attempts. Try again in {retry} seconds."), 429
        path = template_path(username)
        if not path.exists():
            limiter.fail(key)
            return jsonify(error="Authentication failed."), 401
        template = np.load(path, allow_pickle=False)
        matched, _ = verify(template, body.get("open_frame"), body.get("blink_frame"))
        if not matched:
            lock = limiter.fail(key)
            message = "Authentication failed."
            if lock:
                message += f" Locked for {lock} seconds."
            return jsonify(error=message), 401
        limiter.success(key)
        session.clear()
        session["username"] = username
        return jsonify(message="Authentication successful.", username=username)
    except (ValueError, FaceError) as exc:
        return jsonify(error=str(exc)), 400


@app.get("/api/session")
def session_status():
    return jsonify(authenticated="username" in session, username=session.get("username"))


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out.")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
