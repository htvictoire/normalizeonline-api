import base64
from pathlib import Path
from typing import Any

from django.utils import timezone

from apps.normalization.models import Dataset

from .constants import (
    BORDER,
    BRAND,
    BRAND_SOFT,
    CANVAS,
    DANGER_BG,
    DANGER_FG,
    INFO_BG,
    INFO_FG,
    INK,
    INK_MUTED,
    STRIPE,
    SUCCESS_BG,
    SUCCESS_FG,
    SURFACE,
    WARNING_BG,
    WARNING_FG,
)
from .formatting import (
    format_datetime,
    format_duration,
    format_file_size_mb,
    format_status,
    status_key,
)
from .sections import (
    build_column_rows,
    build_config_sections,
    build_issue_rows,
    build_issue_summary,
    build_metric_cards,
    build_pipeline_rows,
)


def build_report_context(dataset: Dataset) -> dict[str, Any]:
    profiling = dataset.profiling_output or {}
    quality = (dataset.normalization_output or {}).get("quality_output", {})
    issues = profiling.get("issues") or []
    column_stats = profiling.get("column_stats") or {}
    confirmed_config = dataset.confirmed_config or {}
    timings = dataset.timings or {}
    row_count = int(profiling.get("row_count") or quality.get("row_count") or dataset.normalized_row_count or 0)
    column_count = int(
        profiling.get("column_count")
        or len(column_stats)
        or len((confirmed_config.get("column_config") or {}))
    )
    completeness_ratio = float(quality.get("completeness_ratio") or profiling.get("completeness_ratio") or 0)
    parse_success_ratio = float(quality.get("parse_success_ratio") or 0)
    total_cells = int(quality.get("total_cells") or row_count * column_count)
    total_nullish = int(quality.get("total_nullish_cells") or 0)
    total_parse_errors = int(quality.get("total_parse_error_cells") or 0)
    quality_score = float(quality.get("quality_score") or 0)
    generated_at = timezone.localtime().strftime("%Y-%m-%d %H:%M %Z")
    estimated_pipeline = timings.get("estimated_pipeline_seconds")

    return {
        "brand": BRAND,
        "brand_soft": BRAND_SOFT,
        "canvas": CANVAS,
        "surface": SURFACE,
        "ink": INK,
        "ink_muted": INK_MUTED,
        "border": BORDER,
        "stripe": STRIPE,
        "success_bg": SUCCESS_BG,
        "success_fg": SUCCESS_FG,
        "warning_bg": WARNING_BG,
        "warning_fg": WARNING_FG,
        "danger_bg": DANGER_BG,
        "danger_fg": DANGER_FG,
        "info_bg": INFO_BG,
        "info_fg": INFO_FG,
        "dataset_name": dataset.name,
        "original_name": dataset.original_name,
        "dataset_id": str(dataset.id),
        "instance_id": str(dataset.instance_id) if dataset.instance_id else "—",
        "generated_at": generated_at,
        "status_label": format_status(dataset.status),
        "status_key": status_key(dataset.status),
        "logo_data_uri": logo_data_uri(),
        "metadata_rows": [
            {"label": "Dataset Name", "value": dataset.name},
            {"label": "Original File", "value": dataset.original_name},
            {"label": "File Type", "value": dataset.get_file_type_display()},
            {"label": "File Size", "value": format_file_size_mb(dataset.size_mb)},
            {"label": "Dataset ID", "value": str(dataset.id)},
            {"label": "Normalization Instance", "value": str(dataset.instance_id) if dataset.instance_id else "—"},
            {"label": "Status", "value": format_status(dataset.status)},
            {"label": "Generated At", "value": generated_at},
            {"label": "Source File Name", "value": dataset.source_file_name or dataset.original_name},
            {"label": "Source Format", "value": dataset.source_file_format or dataset.file_type},
            {"label": "Source Checksum", "value": dataset.source_checksum or "—"},
            {"label": "Manifest Artifact", "value": dataset.manifest_json or "—"},
        ],
        "metric_cards": build_metric_cards(
            row_count=row_count,
            column_count=column_count,
            total_cells=total_cells,
            quality_score=quality_score,
            completeness_ratio=completeness_ratio,
            parse_success_ratio=parse_success_ratio,
            nullish_cells=total_nullish,
            parse_error_cells=total_parse_errors,
        ),
        "issue_summary": build_issue_summary(issues),
        "issues": build_issue_rows(issues),
        "pipeline_rows": build_pipeline_rows(timings),
        "estimated_pipeline": format_duration(estimated_pipeline) if estimated_pipeline is not None else "—",
        "config_sections": build_config_sections(confirmed_config),
        "columns": build_column_rows(
            column_stats=column_stats,
            row_count=row_count,
            issues=issues,
            column_config_map=confirmed_config.get("column_config") or {},
        ),
        "source_file_updated_at": format_datetime(dataset.updated_at),
        "footer_year": timezone.localtime().year,
        "report_subtitle": "Backend-generated summary of the processed dataset, data quality results, and column profile.",
    }


def logo_data_uri() -> str:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "normalizelogo.png"
    if not logo_path.exists():
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
