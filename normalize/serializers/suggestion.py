from rest_framework import serializers


class ColumnCountsSerializer(serializers.Serializer):
    null_count        = serializers.IntegerField()
    nullish_count     = serializers.IntegerField()
    non_null_count    = serializers.IntegerField()
    non_nullish_count = serializers.IntegerField()


class SuggestedColumnDisplaySerializer(serializers.Serializer):
    label         = serializers.CharField()
    counts        = ColumnCountsSerializer()
    sample_values = serializers.ListField(child=serializers.CharField())


class SuggestionDisplaySerializer(serializers.Serializer):
    row_count   = serializers.IntegerField()
    columns     = serializers.DictField(child=SuggestedColumnDisplaySerializer())
    sample_rows = serializers.ListField(child=serializers.ListField(child=serializers.CharField(allow_blank=True)))
