# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


SCHEMA_SQL = """
create table if not exists users (
  id integer primary key autoincrement,
  username text not null unique,
  email text not null unique,
  password_hash text not null,
  role text not null default 'user',
  created_at integer not null,
  last_login_at integer
);

create table if not exists comments (
  id integer primary key autoincrement,
  page_key text not null,
  thread_key text not null,
  author_user_id integer not null,
  author_name text not null,
  body text not null,
  status text not null default 'visible',
  created_at integer not null,
  updated_at integer not null,
  foreign key(author_user_id) references users(id)
);

create index if not exists idx_comments_page_status_created
on comments(page_key, status, created_at desc);
"""


def now_ts() -> int:
    return int(time.time())


def t(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def db_conn(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("pragma journal_mode=WAL;")
    conn.execute("pragma synchronous=NORMAL;")
    conn.executescript(SCHEMA_SQL)
    return conn


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def hash_password(password: str, salt_hex: str | None = None) -> str:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt_hex, digest_hex = stored.split("$", 2)
        if algo != "pbkdf2_sha256":
            return False
        return hmac.compare_digest(hash_password(password, salt_hex), stored)
    except Exception:
        return False


def make_token(secret: str, payload: dict[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    body_b64 = base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
    sig = hmac.new(secret.encode("utf-8"), body_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body_b64}.{sig}"


def parse_token(secret: str, token: str) -> dict[str, Any] | None:
    try:
        body_b64, sig = token.split(".", 1)
        expected = hmac.new(secret.encode("utf-8"), body_b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        padded = body_b64 + "=" * (-len(body_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
        if int(payload.get("exp", 0)) < now_ts():
            return None
        return payload
    except Exception:
        return None


class PortalBackend:
    def __init__(self, db_path: Path, secret: str):
        self.db_path = db_path
        self.secret = secret

    def connection(self) -> sqlite3.Connection:
        return db_conn(self.db_path)

    def current_user(self, headers: Any) -> dict[str, Any] | None:
        cookie = SimpleCookie()
        cookie.load(headers.get("Cookie", ""))
        morsel = cookie.get("portal_session")
        if not morsel:
            return None
        payload = parse_token(self.secret, morsel.value)
        if not payload:
            return None
        user_id = int(payload.get("uid", 0))
        with self.connection() as conn:
            row = conn.execute("select id, username, email, role, created_at, last_login_at from users where id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def register(self, username: str, email: str, password: str) -> tuple[dict[str, Any], str]:
        ts = now_ts()
        with self.connection() as conn:
            count = int(conn.execute("select count(*) from users").fetchone()[0])
            role = "admin" if count == 0 else "user"
            password_hash = hash_password(password)
            cur = conn.execute(
                "insert into users(username, email, password_hash, role, created_at, last_login_at) values (?, ?, ?, ?, ?, ?)",
                (username, email, password_hash, role, ts, ts),
            )
            user_id = int(cur.lastrowid)
            conn.commit()
            row = conn.execute("select id, username, email, role, created_at, last_login_at from users where id = ?", (user_id,)).fetchone()
        token = make_token(self.secret, {"uid": user_id, "role": row["role"], "exp": ts + 86400 * 14})
        return dict(row), token

    def login(self, identity: str, password: str) -> tuple[dict[str, Any] | None, str | None]:
        with self.connection() as conn:
            row = conn.execute(
                "select id, username, email, role, created_at, last_login_at, password_hash from users where lower(username) = lower(?) or lower(email) = lower(?)",
                (identity, identity),
            ).fetchone()
            if not row or not verify_password(password, row["password_hash"]):
                return None, None
            ts = now_ts()
            conn.execute("update users set last_login_at = ? where id = ?", (ts, row["id"]))
            conn.commit()
            safe = dict(row)
            safe.pop("password_hash", None)
        token = make_token(self.secret, {"uid": safe["id"], "role": safe["role"], "exp": now_ts() + 86400 * 14})
        return safe, token

    def add_comment(self, user: dict[str, Any], page_key: str, thread_key: str, body: str) -> dict[str, Any]:
        ts = now_ts()
        with self.connection() as conn:
            cur = conn.execute(
                "insert into comments(page_key, thread_key, author_user_id, author_name, body, status, created_at, updated_at) values (?, ?, ?, ?, ?, 'visible', ?, ?)",
                (page_key, thread_key, user["id"], user["username"], body, ts, ts),
            )
            comment_id = int(cur.lastrowid)
            conn.commit()
            row = conn.execute("select * from comments where id = ?", (comment_id,)).fetchone()
        return dict(row)

    def list_comments(self, page_key: str, include_hidden: bool = False) -> list[dict[str, Any]]:
        sql = "select id, page_key, thread_key, author_name, body, status, created_at, updated_at from comments where page_key = ?"
        args: list[Any] = [page_key]
        if not include_hidden:
            sql += " and status = 'visible'"
        sql += " order by created_at desc limit 50"
        with self.connection() as conn:
            return [dict(r) for r in conn.execute(sql, args).fetchall()]

    def moderate_comment(self, comment_id: int, status: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            conn.execute("update comments set status = ?, updated_at = ? where id = ?", (status, now_ts(), comment_id))
            conn.commit()
            row = conn.execute("select id, page_key, thread_key, author_name, body, status, created_at, updated_at from comments where id = ?", (comment_id,)).fetchone()
        return dict(row) if row else None

    def admin_summary(self) -> dict[str, Any]:
        with self.connection() as conn:
            total_users = int(conn.execute("select count(*) from users").fetchone()[0])
            total_comments = int(conn.execute("select count(*) from comments").fetchone()[0])
            visible_comments = int(conn.execute("select count(*) from comments where status = 'visible'").fetchone()[0])
            hidden_comments = int(conn.execute("select count(*) from comments where status = 'hidden'").fetchone()[0])
            recent = [dict(r) for r in conn.execute(
                "select id, page_key, author_name, body, status, created_at, updated_at from comments order by created_at desc limit 30"
            ).fetchall()]
        return {
            "total_users": total_users,
            "total_comments": total_comments,
            "visible_comments": visible_comments,
            "hidden_comments": hidden_comments,
            "recent_comments": recent,
        }


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    return json.loads(raw.decode("utf-8"))


def send_json(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any], cookie: str | None = None) -> None:
    body = json_bytes(payload)
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    if cookie:
        handler.send_header("Set-Cookie", cookie)
    handler.end_headers()
    handler.wfile.write(body)


def session_cookie(token: str, clear: bool = False) -> str:
    if clear:
        return "portal_session=; Path=/; HttpOnly; Max-Age=0; SameSite=Lax"
    return f"portal_session={token}; Path=/; HttpOnly; Max-Age={86400 * 14}; SameSite=Lax"


class PortalHandler(BaseHTTPRequestHandler):
    backend: PortalBackend

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def api_path(self) -> str:
        path = urlparse(self.path).path
        return path[4:] if path.startswith("/api/") else path

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = self.api_path()
        user = self.backend.current_user(self.headers)
        if path == "/health":
            send_json(self, 200, {"ok": True, "service": "portal_backend", "timestamp": now_ts()})
            return
        if path == "/auth/me":
            send_json(self, 200, {"ok": True, "user": user})
            return
        if path == "/comments":
            qs = parse_qs(parsed.query)
            page_key = t((qs.get("page_key") or ["index"])[0], "index")
            include_hidden = bool(user and user.get("role") == "admin" and (qs.get("include_hidden") or ["0"])[0] == "1")
            comments = self.backend.list_comments(page_key, include_hidden=include_hidden)
            send_json(self, 200, {"ok": True, "page_key": page_key, "comments": comments, "viewer": user})
            return
        if path == "/admin/summary":
            if not user or user.get("role") != "admin":
                send_json(self, HTTPStatus.FORBIDDEN, {"ok": False, "error": "需要管理员权限。"})
                return
            send_json(self, 200, {"ok": True, "summary": self.backend.admin_summary(), "viewer": user})
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "接口不存在。"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = self.api_path()
        user = self.backend.current_user(self.headers)
        try:
            payload = read_json(self)
        except Exception:
            send_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "请求体不是有效 JSON。"})
            return

        if path == "/auth/register":
            username = t(payload.get("username"))
            email = t(payload.get("email"))
            password = t(payload.get("password"))
            if len(username) < 2 or "@" not in email or len(password) < 6:
                send_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "注册信息不完整，用户名至少 2 位，密码至少 6 位。"})
                return
            try:
                new_user, token = self.backend.register(username, email, password)
            except sqlite3.IntegrityError:
                send_json(self, HTTPStatus.CONFLICT, {"ok": False, "error": "用户名或邮箱已存在。"})
                return
            send_json(self, 200, {"ok": True, "user": new_user, "message": "注册成功。"}, cookie=session_cookie(token))
            return

        if path == "/auth/login":
            identity = t(payload.get("identity"))
            password = t(payload.get("password"))
            found_user, token = self.backend.login(identity, password)
            if not found_user or not token:
                send_json(self, HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "用户名、邮箱或密码错误。"})
                return
            send_json(self, 200, {"ok": True, "user": found_user, "message": "登录成功。"}, cookie=session_cookie(token))
            return

        if path == "/auth/logout":
            send_json(self, 200, {"ok": True, "message": "已退出登录。"}, cookie=session_cookie("", clear=True))
            return

        if path == "/comments":
            if not user:
                send_json(self, HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "请先登录后再发表评论。"})
                return
            page_key = t(payload.get("page_key"), "index")
            thread_key = t(payload.get("thread_key"), page_key)
            body = t(payload.get("body"))
            if len(body) < 2:
                send_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "评论内容至少需要 2 个字。"})
                return
            comment = self.backend.add_comment(user, page_key, thread_key, body)
            send_json(self, 200, {"ok": True, "comment": comment, "message": "评论已发布。"})
            return

        if path.startswith("/admin/comments/"):
            if not user or user.get("role") != "admin":
                send_json(self, HTTPStatus.FORBIDDEN, {"ok": False, "error": "需要管理员权限。"})
                return
            try:
                comment_id = int(path.rsplit("/", 1)[-1])
            except Exception:
                send_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "评论编号无效。"})
                return
            action = t(payload.get("action"))
            status = "hidden" if action == "hide" else "visible"
            row = self.backend.moderate_comment(comment_id, status)
            if not row:
                send_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "评论不存在。"})
                return
            send_json(self, 200, {"ok": True, "comment": row, "message": "管理员操作已完成。"})
            return

        send_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "接口不存在。"})


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the lightweight portal backend server.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--db-path", type=Path, default=Path("F:/quant_data/AshareC#/data/portal/portal.sqlite3"))
    ap.add_argument("--secret", default=os.environ.get("ASHARE_PORTAL_SECRET", "change-me-portal-secret"))
    args = ap.parse_args()

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    backend = PortalBackend(args.db_path, args.secret)

    class BoundHandler(PortalHandler):
        pass

    BoundHandler.backend = backend
    server = ThreadingHTTPServer((args.host, args.port), BoundHandler)
    print(f"portal backend listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
