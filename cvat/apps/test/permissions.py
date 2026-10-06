# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from cvat.apps.engine.permissions import TaskPermission
from cvat.apps.iam.permissions import OpenPolicyAgentPermission


class TaskLabelCountsPermission:
    """
    Reading the counts is treated exactly like reading the task's annotations,
    so CVAT's existing OPA rules for tasks decide who may see them.
    """

    @classmethod
    def create(cls, request, view, obj, iam_context) -> list[OpenPolicyAgentPermission]:
        if obj is None:
            return []

        return [
            TaskPermission.create_base_perm(
                request, view, TaskPermission.Scopes.VIEW_ANNOTATIONS, iam_context, obj
            )
        ]
