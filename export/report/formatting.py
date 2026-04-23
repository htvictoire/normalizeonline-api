from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from django.utils import timezone
from django.utils.dateparse import parse_datetime


def fmt(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def format_score(value: Any) -> str:
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "0.0"


def format_percent(value: Any) -> str:
    try:
        ratio = float(value)
    except (TypeError, ValueError):
        ratio = 0.0

    ratio = max(0.0, min(1.0, ratio))
    if ratio >= 1:
        return "100%"
    if ratio <= 0:
        return "0%"
    return f"{ratio * 100:.1f}%"


def format_file_size_mb(value: Any) -> str:
    try:
        return f"{float(value):.2f} MB"
    except (TypeError, ValueError):
        return "0.00 MB"


def format_label(value: str) -> str:
    words = value.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words) if words else value


def format_status(status: str | None) -> str:
    labels = {
        "READY": "Ready",
        "READY_WITH_WARNINGS": "Ready with warnings",
        "FAILED": "Failed",
        "BLOCKED": "Blocked",
    }
    return labels.get(status or "", "Processing complete")


def status_key(status: str | None) -> str:
    if status == "READY":
        return "success"
    if status == "READY_WITH_WARNINGS":
        return "warning"
    if status in {"FAILED", "BLOCKED"}:
        return "danger"
    return "info"


def bool_label(value: Any) -> str:
    return "Yes" if bool(value) else "No"


def join_tokens(values: Iterable[Any], limit: int = 6) -> str:
    tokens = [render_token(value) for value in values if value is not None]
    if not tokens:
        return "—"
    if len(tokens) <= limit:
        return ", ".join(tokens)
    shown = ", ".join(tokens[:limit])
    return f"{shown}, +{len(tokens) - limit} more"


def render_token(value: Any) -> str:
    text = str(value)
    return '""' if text == "" else text


def format_datetime(value: Any) -> str:
    dt = _coerce_datetime(value)
    if dt is None:
        return str(value) if value else "—"
    return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M %Z")


def format_duration(seconds: Any) -> str:
    try:
        total_seconds = max(int(float(seconds)), 0)
    except (TypeError, ValueError):
        return "—"

    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def duration_between(start: Any, end: Any) -> str:
    start_dt = _coerce_datetime(start)
    end_dt = _coerce_datetime(end)
    if start_dt is None or end_dt is None:
        return "—"
    return format_duration((end_dt - start_dt).total_seconds())


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = parse_datetime(value)
    else:
        return None

    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt
