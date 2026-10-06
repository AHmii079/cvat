# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from django.db.models import Count, Q

from cvat.apps.engine.models import Label, LabeledShape, Task


def count_shapes_per_label(task: Task) -> list[dict]:
    """
    Returns one row per top-level label of the task, ordered by count (highest first).

    Shapes are linked to a task only through their job: shape.job -> job.segment -> segment.task.
    Labels can belong to the task or to its project, so the label list is read separately
    and labels without shapes are reported with a count of 0.
    Skeleton points (shapes with a parent) are not counted, so a skeleton counts once.
    """
    label_owner = Q(task_id=task.id)
    if task.project_id:
        label_owner |= Q(project_id=task.project_id)
    labels = Label.objects.filter(label_owner, parent__isnull=True).values_list("id", "name")

    counts = (
        LabeledShape.objects.filter(job__segment__task_id=task.id, parent__isnull=True)
        .values("label_id")
        .annotate(count=Count("id"))
    )
    count_by_label = {row["label_id"]: row["count"] for row in counts}

    rows = [
        {"id": label_id, "name": name, "count": count_by_label.get(label_id, 0)}
        for label_id, name in labels
    ]
    rows.sort(key=lambda row: (-row["count"], row["name"]))
    return rows
