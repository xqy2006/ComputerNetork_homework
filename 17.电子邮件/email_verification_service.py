from __future__ import annotations

import datetime as dt
import hashlib
import os
import sqlite3
from dataclasses import dataclass
from email.message import EmailMessage
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DB_PATH = Path(__file__).resolve().parent / "users.db"
OUTBOX_DIR = Path(__file__).resolve().parent / "outbox"
SECRET = "codex-email-secret"


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def make_code(username: str) -> str:
    return hashlib.sha256((username + SECRET).encode("utf-8")).hexdigest()[:12].upper()


@dataclass
class UserRecord:
    username: str
    password: str
    email: str
    code: str
    created_at: str
    verified: int


class UserStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    email TEXT NOT NULL,
                    code TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    verified INTEGER NOT NULL
                )
                """
            )

    def register(self, username: str, password: str, email: str, current_time: dt.datetime | None = None) -> str:
        current_time = current_time or now_utc()
        code = make_code(username)
        created_at = current_time.isoformat()

        with self._connect() as conn:
            row = conn.execute("SELECT created_at, verified FROM users WHERE username = ?", (username,)).fetchone()
            if row is not None:
                existing_time = dt.datetime.fromisoformat(row[0])
                if row[1] == 1 or current_time - existing_time <= dt.timedelta(hours=1):
                    raise ValueError("username already reserved")
                conn.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.execute(
                "INSERT INTO users(username, password, email, code, created_at, verified) VALUES (?, ?, ?, ?, ?, 0)",
                (username, password, email, code, created_at),
            )
        return code

    def verify(self, username: str, code: str, current_time: dt.datetime | None = None) -> bool:
        current_time = current_time or now_utc()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT code, created_at, verified FROM users WHERE username = ?", (username,)
            ).fetchone()
            if row is None:
                return False
            created_at = dt.datetime.fromisoformat(row[1])
            if current_time - created_at > dt.timedelta(hours=1):
                conn.execute("DELETE FROM users WHERE username = ?", (username,))
                return False
            if row[0] != code:
                return False
            conn.execute("UPDATE users SET verified = 1 WHERE username = ?", (username,))
        return True


def deliver_email(to_address: str, verify_url: str) -> Path:
    OUTBOX_DIR.mkdir(exist_ok=True)
    message = EmailMessage()
    message["Subject"] = "Verify your account"
    message["From"] = "noreply@example.com"
    message["To"] = to_address
    message.set_content(f"Click the following link within 1 hour:\n{verify_url}\n")
    target = OUTBOX_DIR / f"{to_address.replace('@', '_at_')}.eml"
    target.write_text(message.as_string(), encoding="utf-8")
    return target


HTML_FORM = """<!doctype html>
<html><head><meta charset="utf-8"><title>Email Verify</title></head>
<body>
<h1>Register</h1>
<form method="post" action="/register">
<label>昵称 <input name="user"></label><br>
<label>口令 <input name="password" type="password"></label><br>
<label>邮箱 <input name="email"></label><br>
<button type="submit">提交</button>
</form>
</body></html>"""


class VerificationHandler(BaseHTTPRequestHandler):
    store = UserStore()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTML_FORM)
            return
        if parsed.path == "/verify":
            params = parse_qs(parsed.query)
            username = params.get("user", [""])[0]
            code = params.get("code", [""])[0]
            ok = self.store.verify(username, code)
            status = "激活成功" if ok else "激活失败或链接已过期"
            self._send_html(f"<html><body><h1>{status}</h1></body></html>")
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path != "/register":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8")
        data = parse_qs(payload)
        username = data.get("user", [""])[0]
        password = data.get("password", [""])[0]
        email = data.get("email", [""])[0]
        try:
            code = self.store.register(username, password, email)
            verify_url = f"http://127.0.0.1:8000/verify?user={username}&code={code}"
            outbox = deliver_email(email, verify_url)
            self._send_html(f"<html><body><p>注册成功，验证邮件已生成：{outbox.name}</p><p>{verify_url}</p></body></html>")
        except ValueError as exc:
            self._send_html(f"<html><body><p>{exc}</p></body></html>", HTTPStatus.BAD_REQUEST)

    def _send_html(self, text: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = HTTPServer((host, port), VerificationHandler)
    print(f"server listening on http://{host}:{port}")
    print("open / to register, /verify?user=hw&code=ABCDEF to verify")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
