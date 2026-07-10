from rest_framework import serializers
from .base import (
    DiscriminatedField, GROUPING_STYLE_CHOICES, HEADER_MODE_CHOICES, TRACE_MODE_CHOICES,
    IDENTIFIER_KIND_CHOICES, CODE_FORMAT_CHOICES, IP_VERSION_CHOICES,
)


class CsvSourceFormatSerializer(serializers.Serializer):
    format_type      = serializers.ChoiceField(choices=["csv"])
    encoding         = serializers.CharField()
    delimiter        = serializers.CharField()
    header_mode      = serializers.ChoiceField(choices=HEADER_MODE_CHOICES)
    header_row_index = serializers.IntegerField(allow_null=True)


class ExcelSourceFormatSerializer(serializers.Serializer):
    format_type      = serializers.ChoiceField(choices=["excel"])
    sheet_name       = serializers.CharField(allow_null=True, required=False, allow_blank=True)
    header_mode      = serializers.ChoiceField(choices=HEADER_MODE_CHOICES)
    header_row_index = serializers.IntegerField(allow_null=True)


class JsonSourceFormatSerializer(serializers.Serializer):
    format_type = serializers.ChoiceField(choices=["json"])


class SourceFormatField(DiscriminatedField):
    discriminant_key = "format_type"
    serializer_map   = {
        "csv":   CsvSourceFormatSerializer,
        "excel": ExcelSourceFormatSerializer,
        "json":  JsonSourceFormatSerializer,
    }


class StringColumnConfigSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["string"])


class LocalizedReasonsSerializer(serializers.Serializer):
    en = serializers.ListField(child=serializers.CharField(), min_length=3, max_length=3)
    fr = serializers.ListField(child=serializers.CharField(), min_length=3, max_length=3)
    es = serializers.ListField(child=serializers.CharField(), min_length=3, max_length=3)
    ar = serializers.ListField(child=serializers.CharField(), min_length=3, max_length=3)


class IdentifierColumnConfigSerializer(serializers.Serializer):
    type            = serializers.ChoiceField(choices=["identifier"])
    identifier_kind = serializers.ChoiceField(choices=IDENTIFIER_KIND_CHOICES, default="opaque")
    reasons         = LocalizedReasonsSerializer(allow_null=True, required=False)


class DateTimeColumnConfigSerializer(serializers.Serializer):
    type            = serializers.ChoiceField(choices=["datetime"])
    datetime_format = serializers.CharField()


class TimeColumnConfigSerializer(serializers.Serializer):
    type         = serializers.ChoiceField(choices=["time"])
    time_format  = serializers.CharField()


class CountryCodeColumnConfigSerializer(serializers.Serializer):
    type        = serializers.ChoiceField(choices=["country_code"])
    code_format = serializers.ChoiceField(choices=CODE_FORMAT_CHOICES)


class CurrencyCodeColumnConfigSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["currency_code"])


class LanguageCodeColumnConfigSerializer(serializers.Serializer):
    type        = serializers.ChoiceField(choices=["language_code"])
    code_format = serializers.ChoiceField(choices=CODE_FORMAT_CHOICES)


class CategoricalColumnConfigSerializer(serializers.Serializer):
    type             = serializers.ChoiceField(choices=["categorical"])
    canonical_values = serializers.ListField(child=serializers.CharField())


class EmailColumnConfigSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["email"])


class UrlColumnConfigSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["url"])


class IpAddressColumnConfigSerializer(serializers.Serializer):
    type    = serializers.ChoiceField(choices=["ip_address"])
    version = serializers.ChoiceField(choices=IP_VERSION_CHOICES, default="any")


class PhoneColumnConfigSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["phone"])


class BooleanColumnConfigSerializer(serializers.Serializer):
    type         = serializers.ChoiceField(choices=["boolean"])
    true_tokens  = serializers.ListField(child=serializers.CharField())
    false_tokens = serializers.ListField(child=serializers.CharField())


class IntegerColumnConfigSerializer(serializers.Serializer):
    type               = serializers.ChoiceField(choices=["integer"])
    thousand_separator = serializers.CharField(allow_blank=True)
    grouping_style     = serializers.ChoiceField(choices=GROUPING_STYLE_CHOICES)


class _DecimalSyntaxColumnConfigSerializer(serializers.Serializer):
    thousand_separator          = serializers.CharField(allow_blank=True)
    grouping_style              = serializers.ChoiceField(choices=GROUPING_STYLE_CHOICES)
    decimal_separator           = serializers.CharField()
    allow_leading_decimal_point = serializers.BooleanField()


class DecimalColumnConfigSerializer(_DecimalSyntaxColumnConfigSerializer):
    type = serializers.ChoiceField(choices=["decimal"])


class CurrencyColumnConfigSerializer(_DecimalSyntaxColumnConfigSerializer):
    type = serializers.ChoiceField(choices=["currency"])


class PercentageColumnConfigSerializer(_DecimalSyntaxColumnConfigSerializer):
    type = serializers.ChoiceField(choices=["percentage"])


class _SignedNotationColumnConfigSerializer(_DecimalSyntaxColumnConfigSerializer):
    positive_markers        = serializers.ListField(child=serializers.CharField())
    negative_markers        = serializers.ListField(child=serializers.CharField())
    parentheses_as_negative = serializers.BooleanField()


class SignedColumnConfigSerializer(_SignedNotationColumnConfigSerializer):
    type = serializers.ChoiceField(choices=["signed"])


class AccountingColumnConfigSerializer(_SignedNotationColumnConfigSerializer):
    type = serializers.ChoiceField(choices=["accounting"])


class DateColumnConfigSerializer(serializers.Serializer):
    type        = serializers.ChoiceField(choices=["date"])
    date_format = serializers.CharField()


class ColumnConfigField(DiscriminatedField):
    discriminant_key = "type"
    serializer_map   = {
        "string":        StringColumnConfigSerializer,
        "identifier":    IdentifierColumnConfigSerializer,
        "boolean":       BooleanColumnConfigSerializer,
        "integer":       IntegerColumnConfigSerializer,
        "decimal":       DecimalColumnConfigSerializer,
        "currency":      CurrencyColumnConfigSerializer,
        "percentage":    PercentageColumnConfigSerializer,
        "signed":        SignedColumnConfigSerializer,
        "accounting":    AccountingColumnConfigSerializer,
        "date":          DateColumnConfigSerializer,
        "datetime":      DateTimeColumnConfigSerializer,
        "time":          TimeColumnConfigSerializer,
        "country_code":  CountryCodeColumnConfigSerializer,
        "currency_code": CurrencyCodeColumnConfigSerializer,
        "language_code": LanguageCodeColumnConfigSerializer,
        "categorical":   CategoricalColumnConfigSerializer,
        "email":         EmailColumnConfigSerializer,
        "url":           UrlColumnConfigSerializer,
        "ip_address":    IpAddressColumnConfigSerializer,
        "phone":         PhoneColumnConfigSerializer,
    }


class ColumnConfigMapField(serializers.Field):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Expected a dict.")
        result, errors = {}, {}
        field = ColumnConfigField()
        for key, value in data.items():
            try:
                result[key] = field.to_internal_value(value)
            except serializers.ValidationError as exc:
                errors[key] = exc.detail
        if errors:
            raise serializers.ValidationError(errors)
        return result

    def to_representation(self, value):
        return value


class DecisionThresholdsSerializer(serializers.Serializer):
    ready   = serializers.FloatField()
    warning = serializers.FloatField()


class OperationConfigSerializer(serializers.Serializer):
    null_tokens                           = serializers.ListField(child=serializers.CharField())
    assign_indices                        = serializers.BooleanField()
    drop_empty_rows                       = serializers.BooleanField()
    emit_raw_row                          = serializers.BooleanField()
    full_raw_row                          = serializers.BooleanField()
    emit_parse_issues                     = serializers.BooleanField()
    include_unique_ratio                  = serializers.BooleanField()
    include_per_column_parse_error_counts = serializers.BooleanField()
    approximate_unique                    = serializers.BooleanField()
    trace_mode                            = serializers.ChoiceField(choices=TRACE_MODE_CHOICES)
    decision_thresholds                   = DecisionThresholdsSerializer()


class InstanceConfigSerializer(serializers.Serializer):
    source_format    = SourceFormatField()
    column_config    = ColumnConfigMapField()
    operation_config = OperationConfigSerializer()
