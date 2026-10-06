# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

"""
Shows that the live endpoint pushes new counts when annotations change, and how long it takes.

Usage:
    pip install websockets
    python3 live_check.py <task_id> <username> <password> <label_name> [server]

Opens the WebSocket, adds one rectangle to the task's first job through CVAT's annotation API,
waits for the pushed total to grow by one, deletes the rectangle, and waits for it to drop back.
"""

import asyncio
import json
import sys
import time
from urllib.request import Request, urlopen

import websockets


def api(server, token, method, path, body=None):
    request = Request(
        f"{server}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
    )
    with urlopen(request) as response:
        return json.load(response)


def login(server, username, password):
    request = Request(
        f"{server}/api/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request) as response:
        return json.load(response)["key"]


async def wait_for_total(socket, expected, started):
    while True:
        message = json.loads(await asyncio.wait_for(socket.recv(), timeout=15))
        print(f"  pushed after {time.monotonic() - started:5.2f} s: total={message['total']}")
        if message["total"] == expected:
            return


async def main():
    task_id, username, password, label_name = sys.argv[1:5]
    server = sys.argv[5] if len(sys.argv) > 5 else "http://localhost:8080"
    token = login(server, username, password)

    job_id = api(server, token, "GET", f"/api/jobs?task_id={task_id}")["results"][0]["id"]
    labels = api(server, token, "GET", f"/api/labels?task_id={task_id}&page_size=500")["results"]
    label_id = next(label["id"] for label in labels if label["name"] == label_name)

    url = f"{server.replace('http', 'ws', 1)}/api/tasks/{task_id}/label-counts/live"
    async with websockets.connect(
        url, additional_headers={"Authorization": f"Token {token}"}
    ) as ws:
        before = json.loads(await ws.recv())["total"]
        print(f"connected, first message: total={before}")

        shape = {
            "type": "rectangle",
            "frame": 0,
            "label_id": label_id,
            "points": [10, 10, 60, 60],
            "attributes": [],
            "group": 0,
            "source": "manual",
            "occluded": False,
            "outside": False,
            "z_order": 0,
            "rotation": 0,
        }
        print(f"adding one '{label_name}' rectangle to job {job_id}")
        started = time.monotonic()
        created = api(
            server,
            token,
            "PATCH",
            f"/api/jobs/{job_id}/annotations?action=create",
            {"version": 0, "shapes": [shape], "tracks": [], "tags": []},
        )["shapes"]
        await wait_for_total(ws, before + 1, started)

        print("deleting it again")
        started = time.monotonic()
        api(
            server,
            token,
            "PATCH",
            f"/api/jobs/{job_id}/annotations?action=delete",
            {"version": 0, "shapes": created, "tracks": [], "tags": []},
        )
        await wait_for_total(ws, before, started)
        print("total is back to", before)


asyncio.run(main())
