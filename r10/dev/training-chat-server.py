#!/usr/bin/env python3
"""Local browser chat for R10 OpenBSP cloud training (service=local)."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "r10" / "routing"))
from resolver import strip_routing_context, wrap_user_message  # noqa: E402

ORG_ID = "a1111111-1111-4111-8111-111111111111"
AGENT_ID = "a2222222-2222-4222-8222-222222222222"
CONV_ID = os.environ.get(
    "R10_TRAINING_CONV_ID", "c3333333-3333-4333-8333-333333333333"
)
HOST = os.environ.get("R10_TRAINING_CHAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("R10_TRAINING_CHAT_PORT", "8787"))
HTML = Path(__file__).with_name("training-chat.html")
POLL_SECS = int(os.environ.get("R10_TRAINING_POLL_SECS", "90"))
WAIT_AFTER_SEND = float(os.environ.get("R10_TRAINING_WAIT_AFTER_SEND", "6"))


def connect():
    import psycopg2

    project = os.environ.get("SUPABASE_PROJECT_ID", "sywrcfyhbdnpferfeama")
    password = os.environ.get("SUPABASE_DB_PASSWORD", "")
    host = os.environ.get(
        "SUPABASE_SESSION_POOLER_HOST",
        "aws-1-ap-northeast-2.pooler.supabase.com",
    )
    if not password:
        raise RuntimeError("SUPABASE_DB_PASSWORD not set")
    dsn = (
        f"host={host} port=5432 dbname=postgres "
        f"user=postgres.{project} password={password} sslmode=require"
    )
    return psycopg2.connect(dsn)


def message_text(content) -> str:
    if isinstance(content, str):
        content = json.loads(content)
    if not content:
        return ""
    return content.get("text") or content.get("body") or ""


def fetch_history():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select direction, content, created_at
                from public.messages
                where conversation_id = %s
                order by timestamp asc, created_at asc
                limit 100
                """,
                (CONV_ID,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    messages = []
    for direction, content, _created in rows:
        text = strip_routing_context(message_text(content))
        if not text:
            continue
        role = "user" if direction == "incoming" else "bot"
        messages.append({"role": role, "text": text})
    return messages


def send_and_wait(user_text: str) -> tuple[str | None, str | None]:
    history = fetch_history()
    history_texts = [m["text"] for m in history if m["role"] == "user"]
    payload_text = wrap_user_message(user_text, history_texts)

    msg_id = str(uuid.uuid4())
    content = json.dumps(
        {
            "kind": "text",
            "text": payload_text,
            "type": "text",
            "version": "1",
        }
    )
    status = json.dumps({"pending": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})

    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into public.messages (
                      id, organization_id, conversation_id, service,
                      organization_address, contact_address, direction,
                      agent_id, content, status, timestamp
                    ) values (
                      %s, %s, %s, 'local',
                      %s, null, 'incoming',
                      null, %s::jsonb, %s::jsonb, now()
                    )
                    """,
                    (msg_id, ORG_ID, CONV_ID, ORG_ID, content, status),
                )
                sent_at = time.time()
    finally:
        conn.close()

    time.sleep(WAIT_AFTER_SEND)
    deadline = time.time() + POLL_SECS

    while time.time() < deadline:
        conn = connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select direction, content
                    from public.messages
                    where conversation_id = %s
                      and created_at >= to_timestamp(%s)
                    order by created_at asc
                    """,
                    (CONV_ID, sent_at - 1),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        texts = []
        for direction, content in rows:
            text = message_text(content)
            if not text:
                continue
            if direction == "internal":
                err = text if isinstance(text, str) else str(text)
                if "OPENAI" in err.upper() or "API" in err.upper():
                    return None, err
                return None, f"Ошибка бота: {err}"
            if direction == "outgoing":
                texts.append(text)
        if texts:
            return "\n\n".join(texts), None
        time.sleep(1.5)

    return None, "Таймаут: бот не ответил. Проверьте OPENAI_API_KEY в Supabase Edge secrets."


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self):
        body = HTML.read_bytes()
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._html()
            return
        if path == "/api/history":
            try:
                messages = fetch_history()
                self._json(
                    200,
                    {
                        "conversation_id": CONV_ID,
                        "agent_id": AGENT_ID,
                        "messages": messages,
                    },
                )
            except Exception as exc:
                self._json(500, {"error": str(exc)})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/chat":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
            text = (payload.get("text") or "").strip()
            if not text:
                self._json(400, {"error": "text required"})
                return
            reply, err = send_and_wait(text)
            if err:
                self._json(200, {"error": err, "reply": None})
                return
            self._json(200, {"reply": reply})
        except Exception as exc:
            self._json(500, {"error": str(exc)})


def main():
    if not HTML.is_file():
        raise SystemExit(f"missing {HTML}")
    print(f"R10 training chat: http://{HOST}:{PORT}")
    print("Ctrl+C to stop")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
