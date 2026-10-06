# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

"""
Compares the label-count endpoint with the COCO annotation file that was imported.

Usage:
    python3 check_counts.py <coco_json> <task_id> <username> <password> [server]

Prints, per category, the number of COCO instances, the number of shapes CVAT is
expected to create (a COCO polygon split into several parts becomes several polygons),
and the count returned by the endpoint.
"""

import json
import sys
from collections import Counter
from urllib.request import Request, urlopen


def shapes_for(annotation: dict) -> int:
    segmentation = annotation.get("segmentation")
    if isinstance(segmentation, list) and segmentation:
        return len(segmentation)
    return 1


def login(server: str, username: str, password: str) -> str:
    body = json.dumps({"username": username, "password": password}).encode()
    request = Request(
        f"{server}/api/auth/login", data=body, headers={"Content-Type": "application/json"}
    )
    with urlopen(request) as response:
        return json.load(response)["key"]


def main() -> None:
    coco_path, task_id, username, password = sys.argv[1:5]
    server = sys.argv[5] if len(sys.argv) > 5 else "http://localhost:8080"

    coco = json.load(open(coco_path))
    names = {category["id"]: category["name"] for category in coco["categories"]}
    instances = Counter(names[a["category_id"]] for a in coco["annotations"])
    shapes = Counter()
    for annotation in coco["annotations"]:
        shapes[names[annotation["category_id"]]] += shapes_for(annotation)

    token = login(server, username, password)
    request = Request(
        f"{server}/api/tasks/{task_id}/label-counts",
        headers={"Authorization": f"Token {token}"},
    )
    with urlopen(request) as response:
        endpoint = {row["name"]: row["count"] for row in json.load(response)["labels"]}

    print(f"{'label':<16}{'instances':>10}{'shapes':>8}{'endpoint':>10}  match")
    mismatches = 0
    for name in sorted(names.values()):
        match = endpoint.get(name, 0) == shapes[name]
        mismatches += not match
        print(
            f"{name:<16}{instances[name]:>10}{shapes[name]:>8}{endpoint.get(name, 0):>10}"
            f"  {'yes' if match else 'NO'}"
        )
    print(
        f"{'TOTAL':<16}{sum(instances.values()):>10}{sum(shapes.values()):>8}"
        f"{sum(endpoint.values()):>10}  mismatched labels: {mismatches}"
    )


if __name__ == "__main__":
    main()
