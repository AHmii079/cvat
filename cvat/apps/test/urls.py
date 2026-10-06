# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from rest_framework import routers

from .views import TaskLabelCountsViewSet

router = routers.SimpleRouter(trailing_slash=False)
router.register("tasks", TaskLabelCountsViewSet, basename="task-label-counts")

urlpatterns = router.urls
