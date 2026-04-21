from rest_framework import serializers
from core.serializers import ISODateTimeStringField
from .base import FILE_FORMAT_CHOICES, FILE_SOURCE_CHOICES, INSTANCE_STATUS_CHOICES
from .config import InstanceConfigSerializer
from .suggestion import SuggestionDisplaySerializer
from .profiling import ProfilingOutputSerializer
from .result import NormalizationOutputSerializer


class StageTimingsSerializer(serializers.Serializer):
    suggest_started_at         = ISODateTimeStringField(allow_null=True, required=False)
    suggest_ended_at           = ISODateTimeStringField(allow_null=True, required=False)
    profile_started_at         = ISODateTimeStringField(allow_null=True, required=False)
    profile_ended_at           = ISODateTimeStringField(allow_null=True, required=False)
    convert_started_at         = ISODateTimeStringField(allow_null=True, required=False)
    convert_ended_at           = ISODateTimeStringField(allow_null=True, required=False)
    estimated_pipeline_seconds = serializers.IntegerField(allow_null=True, required=False)


class NormalizeInstanceSerializer(serializers.Serializer):
    """
    Validates a normalize service InstanceModel response and maps it onto Dataset fields.
    Source field names match the normalize InstanceModel exactly.
    """

    instance_id          = serializers.UUIDField()
    status               = serializers.ChoiceField(choices=INSTANCE_STATUS_CHOICES)
    tenant_id            = serializers.CharField()
    source_file_name     = serializers.CharField()
    source_file_format   = serializers.ChoiceField(choices=FILE_FORMAT_CHOICES)
    source_type          = serializers.ChoiceField(choices=FILE_SOURCE_CHOICES)
    source_file          = serializers.CharField()
    source_checksum      = serializers.CharField()
    webhook_url          = serializers.URLField(allow_null=True, required=False)
    suggested_config     = InstanceConfigSerializer(allow_null=True, required=False)
    suggestion_display   = SuggestionDisplaySerializer(allow_null=True, required=False)
    confirmed_config     = InstanceConfigSerializer(allow_null=True, required=False)
    profiling_output     = ProfilingOutputSerializer(allow_null=True, required=False)
    normalization_output = NormalizationOutputSerializer(allow_null=True, required=False)
    timings              = StageTimingsSerializer(required=False)


class NormalizeSuggestRequestSerializer(serializers.Serializer):
    source_file        = serializers.CharField()
    source_type        = serializers.ChoiceField(choices=FILE_SOURCE_CHOICES)
    source_file_name   = serializers.CharField()
    source_file_format = serializers.ChoiceField(choices=FILE_FORMAT_CHOICES)
    source_checksum    = serializers.RegexField(regex=r"^[0-9a-f]{64}$")


class NormalizeConfirmRequestSerializer(serializers.Serializer):
    config                 = InstanceConfigSerializer()
    proceed_with_pipeline  = serializers.BooleanField(default=False)
    webhook_url            = serializers.URLField(allow_null=True, required=False)
