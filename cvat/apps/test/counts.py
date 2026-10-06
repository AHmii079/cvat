# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from collections import defaultdict

from django.db.models import Count, Q

from cvat.apps.engine.models import Label, LabeledShape, Task


def count_shapes_per_label(task: Task, by_shape_type: bool = False) -> list[dict]:
    """
    Returns one row per top-level label of the task, ordered by count (highest first).

    Shapes are linked to a task only through their job: shape.job -> job.segment -> segment.task.
    Labels can belong to the task or to its project, so the label list is read separately
    and labels without shapes are reported with a count of 0.
    Skeleton points (shapes with a parent) are not counted, so a skeleton counts once.

    With by_shape_type, each row also gets "by_shape_type": {shape type: count}, computed in
    the same query by adding the shape type to the GROUP BY.
    """
    label_owner = Q(task_id=task.id)
    if task.project_id:
        label_owner |= Q(project_id=task.project_id)
    labels = Label.objects.filter(label_owner, parent__isnull=True).values_list("id", "name")

    group_fields = ("label_id", "type") if by_shape_type else ("label_id",)
    counts = (
        LabeledShape.objects.filter(job__segment__task_id=task.id, parent__isnull=True)
        .values(*group_fields)
        .annotate(count=Count("id"))
    )

    count_by_label = defaultdict(int)
    types_by_label = defaultdict(dict)
    for row in counts:
        count_by_label[row["label_id"]] += row["count"]
        if by_shape_type:
            types_by_label[row["label_id"]][row["type"]] = row["count"]

    rows = []
    for label_id, name in labels:
        row = {"id": label_id, "name": name, "count": count_by_label[label_id]}
        if by_shape_type:
            row["by_shape_type"] = types_by_label[label_id]
        rows.append(row)

    rows.sort(key=lambda row: (-row["count"], row["name"]))
    return rows
