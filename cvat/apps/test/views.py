# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cvat.apps.engine.models import Task

from .counts import count_shapes_per_label
from .permissions import TaskLabelCountsPermission
from .serializers import TaskLabelCountsSerializer


@extend_schema(tags=["tasks"])
class TaskLabelCountsViewSet(viewsets.GenericViewSet):
    queryset = Task.objects.select_related("organization", "project")
    iam_permission_class = TaskLabelCountsPermission
    iam_supports_organization_params = False
    filter_backends = []

    @extend_schema(
        summary="Count annotations per label in a task",
        responses={200: TaskLabelCountsSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="label-counts")
    def label_counts(self, request, pk):
        task = self.get_object()
        labels = count_shapes_per_label(task)
        data = {
            "task_id": task.id,
            "total": sum(row["count"] for row in labels),
            "labels": labels,
        }
        return Response(TaskLabelCountsSerializer(data).data)
