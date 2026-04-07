from rest_framework import serializers


class NormalizeSuggestRequestSerializer(serializers.Serializer):
    source_file = serializers.CharField()
    source_type = serializers.ChoiceField(choices=["local", "s3"])
    source_file_name = serializers.CharField()
    source_file_format = serializers.ChoiceField(choices=["csv", "excel", "json"])
    source_checksum = serializers.RegexField(regex=r"^[0-9a-f]{64}$")


class NormalizeInstanceSerializer(serializers.Serializer):
    """
    Validates and maps a normalize service InstanceModel response onto Dataset fields.
    Source field names match the normalize InstanceModel exactly.
    """

    id = serializers.UUIDField(source="instance_id")
    status = serializers.CharField()
    tenant_id = serializers.CharField()
    source_file_name = serializers.CharField()
    source_file_format = serializers.CharField()
    source_type = serializers.CharField()
    source_file = serializers.CharField()
    source_checksum = serializers.CharField()
    suggested_config = serializers.JSONField()
    suggestion_display = serializers.JSONField(required=False, allow_null=True)
    confirmed_config = serializers.JSONField(allow_null=True, required=False)
    profiling_output = serializers.JSONField(allow_null=True, required=False)
    normalization_output = serializers.JSONField(allow_null=True, required=False)
