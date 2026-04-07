import re

from rest_framework import serializers
from apps.normalization.models import Dataset


SOURCE_CHECKSUM_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class DatasetSerializer(serializers.ModelSerializer):
    def validate_source_checksum(self, value):
        if not value:
            raise serializers.ValidationError("This field is required.")
        if not SOURCE_CHECKSUM_PATTERN.fullmatch(value):
            raise serializers.ValidationError(
                "source_checksum must be a lowercase 64-character SHA256 hex string."
            )
        return value

    class Meta:
        model = Dataset
        fields = [
            "id",
            "owner",
            "name",
            "original_name",
            "file_type",
            "s3_key",
            "size_mb",
            "instance_id",
            "status",
            "tenant_id",
            "source_file_name",
            "source_file_format",
            "source_type",
            "source_file",
            "source_checksum",
            "suggested_config",
            "suggestion_display",
            "confirmed_config",
            "profiling_output",
            "normalization_output",
        ]
        read_only_fields = [
            "id",
            "owner",
            "instance_id",
            "status",
            "tenant_id",
            "source_file_name",
            "source_file_format",
            "source_type",
            "suggested_config",
            "suggestion_display",
            "confirmed_config",
            "profiling_output",
            "normalization_output",
        ]
        extra_kwargs = {
            "s3_key": {"write_only": True},
            "source_checksum": {"required": True, "allow_blank": False},
        }
