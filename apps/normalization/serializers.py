from django.conf import settings
from rest_framework import serializers
from apps.normalization.models import Dataset
from normalize.serializers import NormalizeInstanceSerializer
from normalize.serializers.base import INSTANCE_STATUS_CHOICES, FILE_FORMAT_CHOICES, FILE_SOURCE_CHOICES


class DatasetSerializer(NormalizeInstanceSerializer, serializers.ModelSerializer):
    # Re-declare inherited normalize-instance fields when the Dataset DB contract is
    # looser than the normalize service contract. NormalizeClient keeps the service
    # response strict; this serializer should match the Dataset model contract.
    instance_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=INSTANCE_STATUS_CHOICES,
        required=False,
        allow_null=True,
    )
    tenant_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source_file_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source_file_format = serializers.ChoiceField(
        choices=FILE_FORMAT_CHOICES,
        required=False,
        allow_null=True,
    )
    source_type = serializers.ChoiceField(
        choices=FILE_SOURCE_CHOICES,
        required=False,
    )
    source_file = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source_checksum = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Dataset
        exclude = ["created_by", "deleted_at", "is_active"]
        read_only_fields = ["id", "owner"]
        extra_kwargs = {"s3_key": {"write_only": True}}

    def validate_size_mb(self, value):
        file_type = self.initial_data.get("file_type")
        limit = settings.UPLOAD_MAX_FILE_SIZE_MB.get(file_type)
        if limit is not None and value > limit:
            raise serializers.ValidationError(
                f"{file_type.upper()} files must not exceed {limit} MB (got {value} MB)."
            )
        return value
