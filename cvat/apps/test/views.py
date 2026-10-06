# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from cvat.apps.engine.models import Task

from .counts import count_shapes_per_label
from .permissions import TaskLabelCountsPermission
from .serializers import TaskLabelCountsSerializer

GROUP_BY_SHAPE_TYPE = "shape_type"


@extend_schema(tags=["tasks"])
class TaskLabelCountsViewSet(viewsets.GenericViewSet):
    queryset = Task.objects.select_related("organization", "project")
    iam_permission_class = TaskLabelCountsPermission
    iam_supports_organization_params = False
    filter_backends = []

    @extend_schema(
        summary="Count annotations per label in a task",
        parameters=[
            OpenApiParameter(
                "group_by",
                type=OpenApiTypes.STR,
                enum=[GROUP_BY_SHAPE_TYPE],
                description="Also split each label's count by shape type",
            ),
        ],
        responses={200: TaskLabelCountsSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="label-counts")
    def label_counts(self, request, pk):
        task = self.get_object()

        group_by = request.query_params.get("group_by")
        if group_by not in (None, GROUP_BY_SHAPE_TYPE):
            raise ValidationError({"group_by": f"Supported values: {GROUP_BY_SHAPE_TYPE}"})

        labels = count_shapes_per_label(task, by_shape_type=group_by == GROUP_BY_SHAPE_TYPE)
        data = {
            "task_id": task.id,
            "total": sum(row["count"] for row in labels),
            "group_by": group_by,
            "labels": labels,
        }
        return Response(TaskLabelCountsSerializer(data).data)
