from rest_framework import serializers
from apps.normalization.models import Dataset
from normalize.serializers import NormalizeInstanceSerializer


class DatasetSerializer(NormalizeInstanceSerializer, serializers.ModelSerializer):
    class Meta:
        model = Dataset
        exclude = ["created_by", "deleted_at", "is_active"]
        read_only_fields = ["id", "owner"]
        extra_kwargs = {"s3_key": {"write_only": True}}
