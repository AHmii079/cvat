# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

"""
Live label counts over WebSocket: /api/tasks/{id}/label-counts/live

CVAT already serves Django through uvicorn, so a WebSocket route only needs an ASGI wrapper.
Every tick, the wrapper calls the existing REST endpoint inside the process with the socket's
own headers (session cookie, query string). Login, permissions and counting therefore follow
exactly the same code as GET /api/tasks/{id}/label-counts, and access is re-checked each time.
The socket receives the endpoint's JSON whenever it differs from the last message sent.
"""

import asyncio
import re

LIVE_PATH = re.compile(r"^/api/tasks/(?P<task_id>\d+)/label-counts/live$")
POLL_SECONDS = 2.0
SERVER_ERROR_CLOSE_CODE = 1011
HANDSHAKE_HEADERS = {
    b"connection",
    b"upgrade",
    b"sec-websocket-key",
    b"sec-websocket-version",
    b"sec-websocket-extensions",
    b"sec-websocket-protocol",
    b"accept",
}


def with_label_counts_websocket(django_app):
    async def application(scope, receive, send):
        if scope["type"] == "websocket" and (match := LIVE_PATH.match(scope["path"])):
            await _serve(django_app, scope, receive, send, int(match["task_id"]))
            return

        await django_app(scope, receive, send)

    return application


async def _serve(django_app, scope, receive, send, task_id: int) -> None:
    if (await receive())["type"] != "websocket.connect":
        return
    await send({"type": "websocket.accept"})

    disconnected = asyncio.ensure_future(_wait_for_disconnect(receive))
    last_body = None
    try:
        while not disconnected.done():
            status, body = await _get_label_counts(django_app, scope, task_id)
            if status != 200:
                code = 4000 + status if 400 <= status < 500 else SERVER_ERROR_CLOSE_CODE
                await send({"type": "websocket.close", "code": code})
                return

            if body != last_body:
                await send({"type": "websocket.send", "text": body.decode()})
                last_body = body

            await asyncio.wait({disconnected}, timeout=POLL_SECONDS)
    finally:
        disconnected.cancel()


async def _wait_for_disconnect(receive) -> None:
    while (await receive())["type"] != "websocket.disconnect":
        pass


async def _get_label_counts(django_app, ws_scope, task_id: int) -> tuple[int, bytes]:
    path = f"/api/tasks/{task_id}/label-counts"
    headers = [(k, v) for k, v in ws_scope["headers"] if k not in HANDSHAKE_HEADERS]
    headers.append((b"accept", b"application/json"))
    http_scope = {
        "type": "http",
        "asgi": ws_scope.get("asgi", {"version": "3.0"}),
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https" if ws_scope.get("scheme") == "wss" else "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": ws_scope.get("root_path", ""),
        "query_string": ws_scope.get("query_string", b""),
        "headers": headers,
        "client": ws_scope.get("client"),
        "server": ws_scope.get("server"),
    }

    request_sent = False

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        # Django waits here for a client disconnect and cancels the wait once it has responded.
        await asyncio.Event().wait()

    status = 500
    body = bytearray()

    async def send(message):
        nonlocal status
        if message["type"] == "http.response.start":
            status = message["status"]
        elif message["type"] == "http.response.body":
            body.extend(message.get("body", b""))

    await django_app(http_scope, receive, send)
    return status, bytes(body)
