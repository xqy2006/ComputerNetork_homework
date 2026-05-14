from __future__ import annotations

import argparse
import json
import os
import secrets
import signal
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_DB_PATH = Path("data") / "license_db.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def now_ts() -> float:
    return time.time()


def iso_time(ts: float | None = None) -> str:
    stamp = ts if ts is not None else now_ts()
    return datetime.fromtimestamp(stamp).strftime("%Y-%m-%d %H:%M:%S")


def print_line(message: str) -> None:
    print(message, flush=True)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp_path, path)


class LicenseStore:
    def __init__(self, db_path: Path, heartbeat_timeout: int, recovery_grace: int) -> None:
        self.db_path = db_path
        self.heartbeat_timeout = heartbeat_timeout
        self.recovery_grace = recovery_grace
        self.lock = threading.RLock()
        self.startup_time = now_ts()
        self.data = self._load()
        self._reserve_sessions_after_restart()

    def _load(self) -> dict[str, Any]:
        if not self.db_path.exists():
            return {
                "version": 1,
                "licenses": {},
                "sessions": {},
            }
        return json.loads(self.db_path.read_text(encoding="utf-8"))

    def _save_locked(self) -> None:
        atomic_write_json(self.db_path, self.data)

    def _reserve_sessions_after_restart(self) -> None:
        changed = False
        with self.lock:
            for session in self.data["sessions"].values():
                if session["status"] != "active":
                    continue
                session["recovery_required"] = True
                session["recovery_deadline"] = self.startup_time + self.recovery_grace
                session["recovery_marked_at"] = iso_time(self.startup_time)
                changed = True
            if changed:
                self._save_locked()

    def _generate_serial_locked(self) -> str:
        while True:
            candidate = f"{secrets.randbelow(10**10):010d}"
            if candidate not in self.data["licenses"]:
                return candidate

    def _get_license_locked(self, serial: str) -> dict[str, Any] | None:
        return self.data["licenses"].get(serial)

    def _find_active_session_locked(self, serial: str, user_name: str) -> dict[str, Any] | None:
        for session in self.data["sessions"].values():
            if (
                session["serial"] == serial
                and session["user_name"] == user_name
                and session["status"] == "active"
            ):
                return session
        return None

    def _count_active_sessions_locked(self, serial: str, at_time: float) -> tuple[int, int]:
        active = 0
        reserved = 0
        for session in self.data["sessions"].values():
            if session["serial"] != serial or session["status"] != "active":
                continue
            active += 1
            if session.get("recovery_required"):
                reserved += 1
        return active, reserved

    def cleanup_expired_sessions(self) -> int:
        with self.lock:
            return self._cleanup_expired_sessions_locked(now_ts())

    def _cleanup_expired_sessions_locked(self, at_time: float) -> int:
        expired = 0
        for session in self.data["sessions"].values():
            if session["status"] != "active":
                continue
            if session.get("recovery_required"):
                if at_time > session.get("recovery_deadline", 0):
                    session["status"] = "expired"
                    session["release_reason"] = "recovery_timeout_after_server_restart"
                    session["released_at"] = iso_time(at_time)
                    expired += 1
                continue
            if at_time - session["last_heartbeat"] > self.heartbeat_timeout:
                session["status"] = "expired"
                session["release_reason"] = "heartbeat_timeout"
                session["released_at"] = iso_time(at_time)
                expired += 1
        if expired:
            self._save_locked()
        return expired

    def issue_license(self, admin_user: str, password: str, max_users: int) -> dict[str, Any]:
        if max_users <= 0:
            raise ValueError("max_users must be positive")
        with self.lock:
            serial = self._generate_serial_locked()
            record = {
                "serial": serial,
                "admin_user": admin_user,
                "password_hash": sha256(password.encode("utf-8")).hexdigest(),
                "license_type": f"{max_users} users",
                "max_users": max_users,
                "created_at": iso_time(),
            }
            self.data["licenses"][serial] = record
            self._save_locked()
            return record

    def authorize(self, serial: str, user_name: str, session_id: str | None) -> tuple[int, dict[str, Any]]:
        with self.lock:
            current_time = now_ts()
            self._cleanup_expired_sessions_locked(current_time)
            license_record = self._get_license_locked(serial)
            if license_record is None:
                return HTTPStatus.NOT_FOUND, {
                    "ok": False,
                    "reason": "unknown_license",
                }

            existing = self._find_active_session_locked(serial, user_name)
            if existing is not None:
                if session_id and existing["session_id"] != session_id:
                    return HTTPStatus.CONFLICT, {
                        "ok": False,
                        "reason": "session_mismatch",
                        "expected_session_id": existing["session_id"],
                    }
                existing["last_heartbeat"] = current_time
                existing["updated_at"] = iso_time(current_time)
                existing["recovery_required"] = False
                existing["recovery_deadline"] = None
                self._save_locked()
                active_count, reserved_count = self._count_active_sessions_locked(serial, current_time)
                return HTTPStatus.OK, {
                    "ok": True,
                    "authorized": True,
                    "recovered": True,
                    "session_id": existing["session_id"],
                    "active_count": active_count,
                    "reserved_count": reserved_count,
                    "max_users": license_record["max_users"],
                }

            active_count, reserved_count = self._count_active_sessions_locked(serial, current_time)
            if active_count >= license_record["max_users"]:
                return HTTPStatus.CONFLICT, {
                    "ok": False,
                    "authorized": False,
                    "reason": "capacity_exceeded",
                    "active_count": active_count,
                    "reserved_count": reserved_count,
                    "max_users": license_record["max_users"],
                }

            new_session_id = session_id or str(uuid.uuid4())
            session = {
                "session_id": new_session_id,
                "serial": serial,
                "user_name": user_name,
                "status": "active",
                "created_at": iso_time(current_time),
                "updated_at": iso_time(current_time),
                "last_heartbeat": current_time,
                "recovery_required": False,
                "recovery_deadline": None,
                "release_reason": None,
            }
            self.data["sessions"][new_session_id] = session
            self._save_locked()
            active_count, reserved_count = self._count_active_sessions_locked(serial, current_time)
            return HTTPStatus.OK, {
                "ok": True,
                "authorized": True,
                "recovered": False,
                "session_id": new_session_id,
                "active_count": active_count,
                "reserved_count": reserved_count,
                "max_users": license_record["max_users"],
            }

    def heartbeat(self, session_id: str) -> tuple[int, dict[str, Any]]:
        with self.lock:
            current_time = now_ts()
            self._cleanup_expired_sessions_locked(current_time)
            session = self.data["sessions"].get(session_id)
            if session is None or session["status"] != "active":
                return HTTPStatus.NOT_FOUND, {
                    "ok": False,
                    "reason": "unknown_or_expired_session",
                }
            session["last_heartbeat"] = current_time
            session["updated_at"] = iso_time(current_time)
            session["recovery_required"] = False
            session["recovery_deadline"] = None
            self._save_locked()
            license_record = self.data["licenses"][session["serial"]]
            active_count, reserved_count = self._count_active_sessions_locked(session["serial"], current_time)
            return HTTPStatus.OK, {
                "ok": True,
                "active_count": active_count,
                "reserved_count": reserved_count,
                "max_users": license_record["max_users"],
            }

    def release(self, session_id: str, reason: str) -> tuple[int, dict[str, Any]]:
        with self.lock:
            session = self.data["sessions"].get(session_id)
            if session is None:
                return HTTPStatus.NOT_FOUND, {
                    "ok": False,
                    "reason": "unknown_session",
                }
            if session["status"] != "active":
                return HTTPStatus.OK, {
                    "ok": True,
                    "already_released": True,
                    "status": session["status"],
                }
            session["status"] = "released"
            session["release_reason"] = reason
            session["released_at"] = iso_time()
            session["updated_at"] = iso_time()
            self._save_locked()
            return HTTPStatus.OK, {
                "ok": True,
                "released": True,
            }

    def status(self, serial: str | None = None) -> dict[str, Any]:
        with self.lock:
            self._cleanup_expired_sessions_locked(now_ts())
            licenses: list[dict[str, Any]] = []
            for license_record in self.data["licenses"].values():
                if serial and license_record["serial"] != serial:
                    continue
                active_sessions = []
                for session in self.data["sessions"].values():
                    if session["serial"] != license_record["serial"]:
                        continue
                    active_sessions.append(
                        {
                            "session_id": session["session_id"],
                            "user_name": session["user_name"],
                            "status": session["status"],
                            "updated_at": session["updated_at"],
                            "recovery_required": session.get("recovery_required", False),
                            "release_reason": session.get("release_reason"),
                        }
                    )
                current_active = [item for item in active_sessions if item["status"] == "active"]
                licenses.append(
                    {
                        "serial": license_record["serial"],
                        "admin_user": license_record["admin_user"],
                        "max_users": license_record["max_users"],
                        "active_count": len(current_active),
                        "sessions": active_sessions,
                    }
                )
            return {
                "server_time": iso_time(),
                "heartbeat_timeout": self.heartbeat_timeout,
                "recovery_grace": self.recovery_grace,
                "licenses": licenses,
            }


class LicenseHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "LicenseLab/1.0"

    def do_GET(self) -> None:
        if self.path.startswith("/status"):
            self._handle_status()
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"ok": False, "reason": "unknown_route"})

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"ok": False, "reason": "invalid_json"})
            return

        if self.path == "/authorize":
            status, data = self.server.store.authorize(
                serial=str(payload.get("serial", "")).strip(),
                user_name=str(payload.get("user_name", "")).strip(),
                session_id=(str(payload["session_id"]).strip() if payload.get("session_id") else None),
            )
            self._write_json(status, data)
            return

        if self.path == "/heartbeat":
            status, data = self.server.store.heartbeat(
                session_id=str(payload.get("session_id", "")).strip(),
            )
            self._write_json(status, data)
            return

        if self.path == "/release":
            status, data = self.server.store.release(
                session_id=str(payload.get("session_id", "")).strip(),
                reason=str(payload.get("reason", "client_exit")).strip() or "client_exit",
            )
            self._write_json(status, data)
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"ok": False, "reason": "unknown_route"})

    def log_message(self, fmt: str, *args: Any) -> None:
        print_line(f"[{iso_time()}] {self.address_string()} {fmt % args}")

    def _handle_status(self) -> None:
        serial = None
        if "?" in self.path and "serial=" in self.path:
            serial = self.path.split("serial=", 1)[1].split("&", 1)[0]
        payload = self.server.store.status(serial)
        self._write_json(HTTPStatus.OK, payload)

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class LicenseHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_cls: type[LicenseHTTPRequestHandler], store: LicenseStore):
        super().__init__(server_address, handler_cls)
        self.store = store


def parse_json_response(response: request.addinfourl) -> dict[str, Any]:
    return json.loads(response.read().decode("utf-8"))


def post_json(server_url: str, route: str, payload: dict[str, Any], timeout: int = 5) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=server_url.rstrip("/") + route,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.status, parse_json_response(response)
    except error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def get_json(server_url: str, route: str, timeout: int = 5) -> tuple[int, dict[str, Any]]:
    req = request.Request(url=server_url.rstrip("/") + route, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.status, parse_json_response(response)
    except error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


@dataclass
class ClientState:
    serial: str
    user_name: str
    session_id: str | None = None

    @classmethod
    def load(cls, path: Path, serial: str, user_name: str) -> "ClientState":
        if not path.exists():
            return cls(serial=serial, user_name=user_name)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("serial") != serial or payload.get("user_name") != user_name:
            return cls(serial=serial, user_name=user_name)
        return cls(
            serial=serial,
            user_name=user_name,
            session_id=payload.get("session_id"),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "serial": self.serial,
                    "user_name": self.user_name,
                    "session_id": self.session_id,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def clear_session(self, path: Path) -> None:
        self.session_id = None
        self.save(path)


def run_server(args: argparse.Namespace) -> int:
    store = LicenseStore(Path(args.db), args.heartbeat_timeout, args.recovery_grace)
    server = LicenseHTTPServer((args.host, args.port), LicenseHTTPRequestHandler, store)
    print_line(f"许可证服务器已启动: http://{args.host}:{args.port}")
    print_line(
        f"数据库={Path(args.db).resolve()} 心跳超时={args.heartbeat_timeout}s 重启保留={args.recovery_grace}s"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print_line("收到中断信号，服务器退出。")
    finally:
        server.server_close()
    return 0


def run_issue(args: argparse.Namespace) -> int:
    store = LicenseStore(Path(args.db), args.heartbeat_timeout, args.recovery_grace)
    record = store.issue_license(args.admin, args.password, args.max_users)
    print_line("发证成功")
    print_line(f"管理员: {record['admin_user']}")
    print_line(f"许可证人数: {record['max_users']}")
    print_line(f"序列号: {record['serial']}")
    return 0


def run_status(args: argparse.Namespace) -> int:
    if args.server:
        status_code, payload = get_json(args.server, f"/status?serial={args.serial}" if args.serial else "/status")
        print_line(json.dumps({"status_code": status_code, "payload": payload}, indent=2, ensure_ascii=False))
        return 0 if status_code == HTTPStatus.OK else 1

    store = LicenseStore(Path(args.db), args.heartbeat_timeout, args.recovery_grace)
    payload = store.status(args.serial)
    print_line(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def authorize_once(server_url: str, state: ClientState) -> tuple[bool, dict[str, Any]]:
    status_code, payload = post_json(
        server_url,
        "/authorize",
        {
            "serial": state.serial,
            "user_name": state.user_name,
            "session_id": state.session_id,
        },
    )
    if status_code == HTTPStatus.OK and payload.get("ok"):
        state.session_id = payload["session_id"]
        return True, payload
    return False, payload


def release_once(server_url: str, session_id: str | None, reason: str) -> tuple[bool, dict[str, Any]]:
    if not session_id:
        return True, {"ok": True, "skipped": True}
    status_code, payload = post_json(
        server_url,
        "/release",
        {
            "session_id": session_id,
            "reason": reason,
        },
    )
    return status_code == HTTPStatus.OK and payload.get("ok", False), payload


def heartbeat_once(server_url: str, session_id: str | None) -> tuple[bool, dict[str, Any]]:
    if not session_id:
        return False, {"ok": False, "reason": "missing_session_id"}
    status_code, payload = post_json(
        server_url,
        "/heartbeat",
        {
            "session_id": session_id,
        },
    )
    return status_code == HTTPStatus.OK and payload.get("ok", False), payload


def run_client(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file) if args.state_file else Path("data") / f"client_{args.user}.json"
    state = ClientState.load(state_path, args.serial, args.user)
    stop_event = threading.Event()
    start_time = now_ts()

    def on_signal(signum: int, _frame: Any) -> None:
        print_line(f"收到信号 {signum}，准备释放会话。")
        stop_event.set()

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, on_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, on_signal)

    while not stop_event.is_set():
        try:
            ok, payload = authorize_once(args.server, state)
        except Exception as exc:  # noqa: BLE001
            print_line(f"连接服务器失败，稍后重试: {exc}")
            time.sleep(args.retry_interval)
            continue

        if ok:
            state.save(state_path)
            action = "恢复成功" if payload.get("recovered") else "授权成功"
            print_line(
                f"{action}: user={state.user_name} session={state.session_id} "
                f"占用={payload['active_count']}/{payload['max_users']}"
            )
            break

        reason = payload.get("reason", "unknown_error")
        if reason == "session_mismatch" and payload.get("expected_session_id"):
            state.session_id = payload["expected_session_id"]
            state.save(state_path)
            print_line("检测到旧会话仍然有效，改用服务器记录的会话号重试。")
            time.sleep(1)
            continue
        if reason == "capacity_exceeded":
            print_line(
                f"授权被拒绝: 当前占用={payload['active_count']}/{payload['max_users']}，"
                f"其中重启保留={payload['reserved_count']}"
            )
            return 2
        print_line(f"授权失败: {json.dumps(payload, ensure_ascii=False)}")
        return 1

    if stop_event.is_set():
        return 1

    try:
        while not stop_event.is_set():
            if args.hold_seconds and now_ts() - start_time >= args.hold_seconds:
                print_line("达到保持时长，准备退出。")
                break
            time.sleep(args.heartbeat_interval)
            try:
                ok, payload = heartbeat_once(args.server, state.session_id)
            except Exception as exc:  # noqa: BLE001
                print_line(f"心跳失败，进入恢复模式: {exc}")
                while not stop_event.is_set():
                    try:
                        ok, payload = authorize_once(args.server, state)
                    except Exception as recover_exc:  # noqa: BLE001
                        print_line(f"等待服务器恢复: {recover_exc}")
                        time.sleep(args.retry_interval)
                        continue
                    if ok:
                        state.save(state_path)
                        print_line(
                            f"服务器恢复完成: session={state.session_id} "
                            f"占用={payload['active_count']}/{payload['max_users']}"
                        )
                        break
                    print_line(f"恢复失败，继续重试: {json.dumps(payload, ensure_ascii=False)}")
                    time.sleep(args.retry_interval)
                continue

            if ok:
                print_line(
                    f"心跳正常: session={state.session_id} "
                    f"占用={payload['active_count']}/{payload['max_users']}"
                )
                continue

            if payload.get("reason") == "unknown_or_expired_session":
                print_line("服务器已丢失或回收当前会话，尝试重新授权。")
                state.clear_session(state_path)
                continue

            print_line(f"心跳返回异常: {json.dumps(payload, ensure_ascii=False)}")
            time.sleep(args.retry_interval)
    finally:
        if args.release_on_exit and state.session_id:
            try:
                ok, payload = release_once(args.server, state.session_id, "client_exit")
                if ok:
                    print_line("会话已正常释放。")
                    state.clear_session(state_path)
                else:
                    print_line(f"释放会话失败: {json.dumps(payload, ensure_ascii=False)}")
            except Exception as exc:  # noqa: BLE001
                print_line(f"退出时释放会话失败: {exc}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="许可证实验程序")
    parser.set_defaults(func=None)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=str(DEFAULT_DB_PATH), help="许可证数据库文件")
    common.add_argument("--heartbeat-timeout", type=int, default=15, help="心跳超时秒数")
    common.add_argument("--recovery-grace", type=int, default=30, help="服务端重启后的保留秒数")

    subparsers = parser.add_subparsers(dest="command")

    issue_parser = subparsers.add_parser("issue", parents=[common], help="发放许可证")
    issue_parser.add_argument("--admin", required=True, help="管理员用户名")
    issue_parser.add_argument("--password", required=True, help="管理员口令")
    issue_parser.add_argument("--max-users", type=int, required=True, help="许可证人数上限")
    issue_parser.set_defaults(func=run_issue)

    server_parser = subparsers.add_parser("server", parents=[common], help="启动许可证服务器")
    server_parser.add_argument("--host", default=DEFAULT_HOST, help="监听地址")
    server_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="监听端口")
    server_parser.set_defaults(func=run_server)

    status_parser = subparsers.add_parser("status", parents=[common], help="查看许可证状态")
    status_parser.add_argument("--serial", help="指定序列号")
    status_parser.add_argument("--server", help="直接从 HTTP 服务器读取状态，如 http://127.0.0.1:8765")
    status_parser.set_defaults(func=run_status)

    client_parser = subparsers.add_parser("client", help="模拟软件 A 客户端")
    client_parser.add_argument("--server", default=f"http://{DEFAULT_HOST}:{DEFAULT_PORT}", help="许可证服务器地址")
    client_parser.add_argument("--serial", required=True, help="10 位许可证序列号")
    client_parser.add_argument("--user", required=True, help="当前组织用户")
    client_parser.add_argument("--state-file", help="客户端状态文件")
    client_parser.add_argument("--heartbeat-interval", type=int, default=5, help="心跳周期秒数")
    client_parser.add_argument("--retry-interval", type=int, default=3, help="重试周期秒数")
    client_parser.add_argument("--hold-seconds", type=int, default=0, help="保持连接的时长，0 表示直到手动中断")
    client_parser.add_argument(
        "--release-on-exit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="退出时是否主动释放会话",
    )
    client_parser.set_defaults(func=run_client)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.func is None:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
