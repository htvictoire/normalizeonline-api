from __future__ import annotations

from collections import defaultdict
from typing import Any

from .formatting import (
    bool_label,
    duration_between,
    fmt,
    format_datetime,
    format_label,
    format_percent,
    join_tokens,
)

SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}


def build_metric_cards(
    row_count: int,
    column_count: int,
    total_cells: int,
    quality_score: float,
    completeness_ratio: float,
    parse_success_ratio: float,
    nullish_cells: int,
    parse_error_cells: int,
) -> list[dict[str, str]]:
    nullish_ratio = (nullish_cells / total_cells) if total_cells else 0
    error_ratio = (parse_error_cells / total_cells) if total_cells else 0

    return [
        {"label": "Rows", "value": fmt(row_count), "detail": "", "tone": "neutral"},
        {"label": "Columns", "value": fmt(column_count), "detail": "", "tone": "neutral"},
        {"label": "Total Cells", "value": fmt(total_cells), "detail": "", "tone": "neutral"},
        {
            "label": "Quality Score",
            "value": f"{quality_score:.1f}",
            "detail": "Overall normalization quality",
            "tone": score_tone(quality_score),
        },
        {
            "label": "Completeness",
            "value": format_percent(completeness_ratio),
            "detail": "Non-nullish value coverage",
            "tone": ratio_tone(completeness_ratio),
        },
        {
            "label": "Parse Success",
            "value": format_percent(parse_success_ratio),
            "detail": "Values parsed without errors",
            "tone": ratio_tone(parse_success_ratio),
        },
        {
            "label": "Nullish Cells",
            "value": fmt(nullish_cells),
            "detail": format_percent(nullish_ratio),
            "tone": inverse_ratio_tone(nullish_ratio),
        },
        {
            "label": "Parse Errors",
            "value": fmt(parse_error_cells),
            "detail": format_percent(error_ratio),
            "tone": inverse_ratio_tone(error_ratio),
        },
    ]


def build_issue_summary(issues: list[dict[str, Any]]) -> list[dict[str, str]]:
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    for issue in issues:
        severity = str(issue.get("severity") or "INFO").upper()
        counts[severity if severity in counts else "INFO"] += 1

    return [
        {"label": "Errors", "count": fmt(counts["ERROR"]), "tone": "danger"},
        {"label": "Warnings", "count": fmt(counts["WARNING"]), "tone": "warning"},
        {"label": "Info", "count": fmt(counts["INFO"]), "tone": "info"},
    ]


def build_issue_rows(issues: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ordered = sorted(
        issues,
        key=lambda issue: (
            SEVERITY_ORDER.get(str(issue.get("severity") or "INFO").upper(), 9),
            str(issue.get("location") or ""),
            str(issue.get("code") or ""),
        ),
    )

    for issue in ordered:
        severity = str(issue.get("severity") or "INFO").upper()
        rows.append(
            {
                "severity": severity.title(),
                "severity_key": severity.lower(),
                "code": str(issue.get("code") or "—"),
                "location": format_issue_location(issue.get("location")),
                "message": str(issue.get("message") or ""),
                "evidence": summarize_mapping(issue.get("evidence") or issue.get("pattern_context")),
            }
        )
    return rows


def build_pipeline_rows(timings: dict[str, Any]) -> list[dict[str, str]]:
    stages = [
        ("Suggestion", "suggest_started_at", "suggest_ended_at"),
        ("Profiling", "profile_started_at", "profile_ended_at"),
        ("Normalization", "convert_started_at", "convert_ended_at"),
    ]
    rows: list[dict[str, str]] = []
    for label, start_key, end_key in stages:
        started_at = timings.get(start_key)
        ended_at = timings.get(end_key)
        if not started_at and not ended_at:
            continue
        rows.append(
            {
                "stage": label,
                "started_at": format_datetime(started_at),
                "ended_at": format_datetime(ended_at),
                "duration": duration_between(started_at, ended_at),
            }
        )
    return rows


def build_config_sections(config: dict[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []

    source_format = config.get("source_format") or {}
    if source_format:
        rows = [
            {"label": format_label(key), "value": format_setting_value(key, value)}
            for key, value in source_format.items()
        ]
        sections.append({"title": "Source Format", "rows": rows})

    operation_config = config.get("operation_config") or {}
    if operation_config:
        rows: list[dict[str, str]] = []
        thresholds = operation_config.get("decision_thresholds") or {}
        for key, value in operation_config.items():
            if key == "decision_thresholds":
                continue
            rows.append({"label": format_label(key), "value": format_setting_value(key, value)})

        if thresholds:
            rows.append(
                {
                    "label": "Ready Threshold",
                    "value": format_percent(thresholds.get("ready")),
                }
            )
            rows.append(
                {
                    "label": "Warning Threshold",
                    "value": format_percent(thresholds.get("warning")),
                }
            )
        sections.append({"title": "Operation Config", "rows": rows})

    return sections


def build_column_rows(
    column_stats: dict[str, Any],
    row_count: int,
    issues: list[dict[str, Any]],
    column_config_map: dict[str, Any],
) -> list[dict[str, str]]:
    issue_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        location = issue.get("location")
        if location:
            issue_map[str(location)].append(issue)

    rows: list[dict[str, str]] = []
    for index, (key, stats) in enumerate(column_stats.items(), start=1):
        counts = stats.get("counts") or {}
        null_count = int(counts.get("null_count") or 0)
        nullish_count = int(counts.get("nullish_count") or 0)
        non_null_count = int(counts.get("non_null_count") or 0)
        fill_ratio = (non_null_count / row_count) if row_count else 0
        column_issues = issue_map.get(key, [])
        issue_codes = ", ".join(
            str(issue.get("code") or "")
            for issue in column_issues[:3]
            if issue.get("code")
        )
        if len(column_issues) > 3:
            issue_codes = f"{issue_codes}, +{len(column_issues) - 3} more" if issue_codes else f"{len(column_issues)} issues"

        rows.append(
            {
                "index": str(index),
                "name": str(stats.get("label") or key),
                "field": key,
                "column_type": format_label(str(stats.get("column_type") or "unknown")),
                "fill_rate": format_percent(fill_ratio),
                "non_null": fmt(non_null_count),
                "nulls": fmt(null_count),
                "nullish": fmt(nullish_count),
                "profile": summarize_profile(stats.get("type_profile") or {}),
                "config": summarize_column_config(column_config_map.get(key) or {}),
                "issue_count": fmt(len(column_issues)),
                "issue_codes": issue_codes or "—",
            }
        )
    return rows


def summarize_profile(profile: dict[str, Any]) -> str:
    profile_type = str(profile.get("profile_type") or "")
    if profile_type == "string":
        min_length = int(profile.get("min_length") or 0)
        max_length = int(profile.get("max_length") or 0)
        return " | ".join(
            [
                f"{fmt(int(profile.get('distinct_count') or 0))} distinct",
                f"{format_percent(profile.get('distinct_ratio') or 0)} unique",
                f"Length {min_length}" if min_length == max_length else f"Length {min_length} to {max_length}",
            ]
        )

    if profile_type == "boolean":
        true_count = int(profile.get("true_token_count") or 0)
        false_count = int(profile.get("false_token_count") or 0)
        unrecognized = int(profile.get("unrecognized_count") or 0)
        parts = [f"True {fmt(true_count)}", f"False {fmt(false_count)}"]
        if unrecognized:
            parts.append(f"Unrecognized {fmt(unrecognized)}")
        return " | ".join(parts)

    if profile_type == "date":
        return " | ".join(
            [
                f"Matched {fmt(int(profile.get('format_match_count') or 0))}",
                format_percent(profile.get("format_match_ratio") or 0),
            ]
        )

    if profile_type in {"integer", "decimal", "percentage", "signed", "currency", "accounting"}:
        parts = [
            f"Parsed {fmt(int(profile.get('parse_match_count') or 0))}",
            format_percent(profile.get("parse_match_ratio") or 0),
        ]
        if profile.get("separator_mismatch_detected"):
            parts.append(f"Separator mismatch {fmt(int(profile.get('swapped_match_count') or 0))}")
        if profile_type == "currency":
            parts.append(f"Symbols {fmt(int(profile.get('symbol_detected_count') or 0))}")
        if profile_type == "accounting":
            parts.append(
                f"Parentheses negatives {fmt(int(profile.get('parentheses_negative_count') or 0))}"
            )
        return " | ".join(parts)

    return "—"


def summarize_column_config(config: dict[str, Any]) -> str:
    if not config:
        return "—"

    column_type = str(config.get("type") or "")
    parts: list[str] = []

    if column_type and column_type != "string":
        parts.append(format_label(column_type))
    if "date_format" in config:
        parts.append(f"Format {config.get('date_format')}")
    if "decimal_separator" in config:
        parts.append(f"Decimal {render_separator(config.get('decimal_separator'))}")
    if "thousand_separator" in config:
        parts.append(f"Thousands {render_separator(config.get('thousand_separator'))}")
    if "grouping_style" in config:
        parts.append(f"Grouping {format_label(str(config.get('grouping_style') or ''))}")
    if "true_tokens" in config:
        parts.append(f"True tokens {join_tokens(config.get('true_tokens') or [])}")
    if "false_tokens" in config:
        parts.append(f"False tokens {join_tokens(config.get('false_tokens') or [])}")
    if "positive_markers" in config:
        parts.append(f"Positive {join_tokens(config.get('positive_markers') or [])}")
    if "negative_markers" in config:
        parts.append(f"Negative {join_tokens(config.get('negative_markers') or [])}")
    if "parentheses_as_negative" in config:
        parts.append(f"Parentheses negative {bool_label(config.get('parentheses_as_negative'))}")

    return " | ".join(parts[:3]) if parts else "Configured"


def format_issue_location(value: Any) -> str:
    if not value:
        return "Global"
    return format_label(str(value))


def summarize_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "—"

    parts: list[str] = []
    for index, (key, raw_value) in enumerate(value.items()):
        if index >= 4:
            parts.append(f"+{len(value) - 4} more")
            break
        if isinstance(raw_value, list):
            rendered = join_tokens(raw_value, limit=4)
        elif isinstance(raw_value, dict):
            rendered = summarize_mapping(raw_value)
        else:
            rendered = str(raw_value)
        parts.append(f"{format_label(str(key))}: {rendered}")
    return " | ".join(parts)


def format_setting_value(key: str, value: Any) -> str:
    if isinstance(value, bool):
        return bool_label(value)
    if value is None or value == "":
        return "—"
    if isinstance(value, list):
        return join_tokens(value)
    if isinstance(value, dict):
        return summarize_mapping(value)

    if key in {"header_mode", "grouping_style", "trace_mode", "format_type"}:
        return format_label(str(value))
    if key == "header_row_index":
        return f"Row {int(value) + 1}"
    if key in {"ready", "warning"}:
        return format_percent(value)
    if key in {"delimiter", "thousand_separator", "decimal_separator"}:
        return render_separator(value)
    return str(value)


def render_separator(value: Any) -> str:
    mapping = {
        ",": "Comma (,)",
        ".": "Dot (.)",
        ";": "Semicolon (;)",
        "|": "Pipe (|)",
        "\t": "Tab",
        " ": "Space",
        "": "None",
    }
    return mapping.get(str(value), str(value))


def ratio_tone(value: float) -> str:
    if value >= 0.95:
        return "positive"
    if value >= 0.75:
        return "neutral"
    if value >= 0.5:
        return "warning"
    return "danger"


def inverse_ratio_tone(value: float) -> str:
    if value <= 0.01:
        return "positive"
    if value <= 0.05:
        return "neutral"
    if value <= 0.15:
        return "warning"
    return "danger"


def score_tone(value: float) -> str:
    if value >= 90:
        return "positive"
    if value >= 75:
        return "neutral"
    if value >= 60:
        return "warning"
    return "danger"
