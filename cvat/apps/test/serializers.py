# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from rest_framework import serializers


class LabelCountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()
    by_shape_type = serializers.DictField(child=serializers.IntegerField(), required=False)


class TaskLabelCountsSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    total = serializers.IntegerField()
    group_by = serializers.CharField(allow_null=True)
    labels = LabelCountSerializer(many=True)
