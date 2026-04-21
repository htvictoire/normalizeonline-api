from rest_framework import serializers


class ArtifactPathsSerializer(serializers.Serializer):
    normalized_parquet = serializers.CharField()
    manifest_json      = serializers.CharField()
    trace_parquet      = serializers.CharField()


class QualityOutputSerializer(serializers.Serializer):
    row_count               = serializers.IntegerField()
    total_cells             = serializers.IntegerField()
    total_nullish_cells     = serializers.IntegerField()
    total_parse_error_cells = serializers.IntegerField()
    parse_success_ratio     = serializers.FloatField()
    completeness_ratio      = serializers.FloatField()
    quality_score           = serializers.CharField()
    column_null_counts      = serializers.DictField(child=serializers.IntegerField())


class NormalizationOutputSerializer(serializers.Serializer):
    quality_output = QualityOutputSerializer()
    artifacts      = ArtifactPathsSerializer()
