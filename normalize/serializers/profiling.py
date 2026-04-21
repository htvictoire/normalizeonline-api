from rest_framework import serializers
from .base import DiscriminatedField, ISSUE_SEVERITY_CHOICES, COLUMN_TYPE_CHOICES
from .suggestion import ColumnCountsSerializer


class NormalizationIssueSerializer(serializers.Serializer):
    code            = serializers.CharField()
    severity        = serializers.ChoiceField(choices=ISSUE_SEVERITY_CHOICES)
    message         = serializers.CharField()
    location        = serializers.CharField(allow_null=True, required=False)
    evidence        = serializers.DictField(required=False, allow_null=True)
    pattern_context = serializers.DictField(required=False, allow_null=True)


class StringColumnProfileSerializer(serializers.Serializer):
    profile_type   = serializers.ChoiceField(choices=["string"])
    distinct_count = serializers.IntegerField()
    distinct_ratio = serializers.FloatField()
    min_length     = serializers.IntegerField()
    max_length     = serializers.IntegerField()


class BooleanColumnProfileSerializer(serializers.Serializer):
    profile_type       = serializers.ChoiceField(choices=["boolean"])
    true_token_count   = serializers.IntegerField()
    false_token_count  = serializers.IntegerField()
    unrecognized_count = serializers.IntegerField()
    recognized_ratio   = serializers.FloatField()


class _ParseMatchProfileSerializer(serializers.Serializer):
    parse_match_count = serializers.IntegerField()
    parse_match_ratio = serializers.FloatField()


class _SeparatorMismatchProfileSerializer(_ParseMatchProfileSerializer):
    swapped_match_count         = serializers.IntegerField()
    swapped_match_ratio         = serializers.FloatField()
    separator_mismatch_detected = serializers.BooleanField()


class IntegerColumnProfileSerializer(_ParseMatchProfileSerializer):
    profile_type = serializers.ChoiceField(choices=["integer"])


class DecimalColumnProfileSerializer(_SeparatorMismatchProfileSerializer):
    profile_type = serializers.ChoiceField(choices=["decimal"])


class PercentageColumnProfileSerializer(_SeparatorMismatchProfileSerializer):
    profile_type = serializers.ChoiceField(choices=["percentage"])


class SignedColumnProfileSerializer(_SeparatorMismatchProfileSerializer):
    profile_type = serializers.ChoiceField(choices=["signed"])


class _SymbolDistributionProfileSerializer(serializers.Serializer):
    symbol_distribution   = serializers.DictField(child=serializers.IntegerField())
    symbol_detected_count = serializers.IntegerField()
    symbol_detected_ratio = serializers.FloatField()
    missing_symbol_count  = serializers.IntegerField()
    missing_symbol_ratio  = serializers.FloatField()
    dominant_symbol       = serializers.CharField(allow_null=True)
    dominant_symbol_ratio = serializers.FloatField()
    has_mixed_symbols     = serializers.BooleanField()


class CurrencyColumnProfileSerializer(
    _SeparatorMismatchProfileSerializer,
    _SymbolDistributionProfileSerializer,
):
    profile_type                       = serializers.ChoiceField(choices=["currency"])
    symbol_position_distribution       = serializers.DictField(child=serializers.IntegerField())
    dominant_symbol_position           = serializers.CharField(allow_null=True)
    dominant_symbol_position_ratio     = serializers.FloatField()
    has_mixed_symbol_positions         = serializers.BooleanField()
    currency_token_form_distribution   = serializers.DictField(child=serializers.IntegerField())
    dominant_currency_token_form       = serializers.CharField(allow_null=True)
    dominant_currency_token_form_ratio = serializers.FloatField()
    has_mixed_currency_token_forms     = serializers.BooleanField()


class AccountingColumnProfileSerializer(
    _SeparatorMismatchProfileSerializer,
    _SymbolDistributionProfileSerializer,
):
    profile_type                 = serializers.ChoiceField(choices=["accounting"])
    sign_notation_distribution   = serializers.DictField(child=serializers.IntegerField())
    dominant_sign_notation       = serializers.CharField(allow_null=True)
    dominant_sign_notation_ratio = serializers.FloatField()
    has_mixed_sign_notations     = serializers.BooleanField()
    negative_marker_distribution = serializers.DictField(child=serializers.IntegerField())
    positive_marker_distribution = serializers.DictField(child=serializers.IntegerField())
    parentheses_negative_count   = serializers.IntegerField()
    leading_sign_count           = serializers.IntegerField()
    trailing_sign_count          = serializers.IntegerField()
    explicit_sign_count          = serializers.IntegerField()
    unsigned_non_nullish_count   = serializers.IntegerField()


class DateColumnProfileSerializer(serializers.Serializer):
    profile_type       = serializers.ChoiceField(choices=["date"])
    format_match_count = serializers.IntegerField()
    format_match_ratio = serializers.FloatField()


class ColumnProfileField(DiscriminatedField):
    discriminant_key = "profile_type"
    serializer_map   = {
        "string":     StringColumnProfileSerializer,
        "boolean":    BooleanColumnProfileSerializer,
        "integer":    IntegerColumnProfileSerializer,
        "decimal":    DecimalColumnProfileSerializer,
        "percentage": PercentageColumnProfileSerializer,
        "signed":     SignedColumnProfileSerializer,
        "currency":   CurrencyColumnProfileSerializer,
        "accounting": AccountingColumnProfileSerializer,
        "date":       DateColumnProfileSerializer,
    }


class ColumnProfileStatsSerializer(serializers.Serializer):
    label         = serializers.CharField()
    column_type   = serializers.ChoiceField(choices=COLUMN_TYPE_CHOICES)
    counts        = ColumnCountsSerializer()
    null_ratio    = serializers.FloatField()
    nullish_ratio = serializers.FloatField()
    type_profile  = ColumnProfileField()


class ProfilingOutputSerializer(serializers.Serializer):
    source_checksum           = serializers.CharField()
    row_count                 = serializers.IntegerField()
    empty_row_count           = serializers.IntegerField()
    column_count              = serializers.IntegerField()
    pattern_consistency_ratio = serializers.FloatField()
    completeness_ratio        = serializers.FloatField()
    column_stats              = serializers.DictField(child=ColumnProfileStatsSerializer())
    issues                    = serializers.ListField(child=NormalizationIssueSerializer())
