from rest_framework import serializers


class ISODateTimeStringField(serializers.Field):
    """
    Validate ISO 8601 datetimes while keeping serializer output JSON-safe.

    Use this when the API contract is a datetime string but the destination
    should remain a plain JSON-serializable value instead of a Python datetime.
    """

    default_error_messages = {
        "invalid": "Datetime has wrong format. Use ISO 8601.",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._datetime_field = serializers.DateTimeField()

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        parsed = self._datetime_field.to_internal_value(data)
        return self._datetime_field.to_representation(parsed)

    def to_representation(self, value):
        if isinstance(value, str):
            parsed = self._datetime_field.to_internal_value(value)
        else:
            parsed = value
        return self._datetime_field.to_representation(parsed)
