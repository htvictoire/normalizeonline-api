from rest_framework import serializers


INSTANCE_STATUS_CHOICES = [
    "PENDING", "AWAITING_CONFIRMATION", "CONFIRMED", "PROFILING",
    "PROFILED", "NORMALIZING", "READY", "READY_WITH_WARNINGS", "BLOCKED", "FAILED",
]
FILE_FORMAT_CHOICES    = ["csv", "excel", "json"]
FILE_SOURCE_CHOICES    = ["local", "s3"]
COLUMN_TYPE_CHOICES    = ["string", "boolean", "integer", "decimal", "currency", "percentage", "signed", "accounting", "date"]
GROUPING_STYLE_CHOICES = ["western", "indian"]
HEADER_MODE_CHOICES    = ["present", "absent"]
ISSUE_SEVERITY_CHOICES = ["ERROR", "WARNING", "INFO"]
TRACE_MODE_CHOICES     = ["full", "sparse"]


class DiscriminatedField(serializers.Field):
    """
    Validates a polymorphic dict by picking a sub-serializer based on a discriminant key.

    Subclasses must set:
      - discriminant_key: the field name inside the incoming dict that selects the serializer
      - serializer_map: mapping from discriminant value to the serializer class to use

    Example: if discriminant_key = "type" and the data is {"type": "date", ...},
    the field looks up serializer_map["date"] and validates the full dict against it.
    On read, the stored value is returned as-is.
    """

    discriminant_key: str
    serializer_map: dict[str, type[serializers.Serializer]]

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Expected a dict.")
        discriminant = data.get(self.discriminant_key)
        serializer_class = self.serializer_map.get(discriminant)
        if serializer_class is None:
            raise serializers.ValidationError(
                f"Unknown {self.discriminant_key!r}: {discriminant!r}. "
                f"Valid: {list(self.serializer_map)}"
            )
        s = serializer_class(data=data)
        s.is_valid(raise_exception=True)
        return s.validated_data

    def to_representation(self, value):
        return value
