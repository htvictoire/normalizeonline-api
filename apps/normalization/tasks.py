from __future__ import annotations

from collections.abc import Callable
from logging import getLogger
from typing import cast

from celery import shared_task
from django.utils import timezone

from export import (
    CSVExportError, export_csv,
    JSONExportError, export_json,
    XLSXExportError, export_xlsx,
    PDFExportError, export_report,
)
from apps.normalization.models import Dataset

logger = getLogger(__name__)

_EXPORT_LOCK_TTL = 3600


def queue_export(dataset_id: int, fmt: str) -> None:
    from django.core.cache import cache
    if cache.add(f"export:{fmt}:{dataset_id}", 1, timeout=_EXPORT_LOCK_TTL):
        generate_export.delay(dataset_id, fmt)


def queue_report(dataset_id: int) -> None:
    from django.core.cache import cache
    if cache.add(f"export:pdf:{dataset_id}", 1, timeout=_EXPORT_LOCK_TTL):
        generate_report.delay(dataset_id)


def get_report_key(dataset: Dataset) -> str:
    """Return the S3 key for the dataset report, generating it synchronously if needed."""
    from export import build_report_export_key
    if not dataset.pdf_exported_at:
        export_report(dataset)
        Dataset.objects.filter(id=dataset.id).update(pdf_exported_at=timezone.now())
    return build_report_export_key(cast(str, dataset.normalized_parquet))

_EXPORTERS: dict[str, tuple[Callable[[Dataset], object], type[Exception], str]] = {
    "csv":   (lambda ds: export_csv(cast(str, ds.normalized_parquet)),                                          CSVExportError,   "csv_exported_at"),
    "json":  (lambda ds: export_json(cast(str, ds.normalized_parquet)),                                         JSONExportError,  "json_exported_at"),
    "xlsx":  (lambda ds: export_xlsx(cast(str, ds.normalized_parquet), cast(int, ds.normalized_row_count)),     XLSXExportError,  "xlsx_exported_at"),
}


@shared_task
def generate_export(dataset_id: int, fmt: str) -> None:
    if fmt not in _EXPORTERS:
        logger.error("generate_export: unsupported format %r for dataset %s", fmt, dataset_id)
        return

    try:
        dataset = Dataset.objects.get(id=dataset_id)
    except Dataset.DoesNotExist:
        logger.error("generate_export: dataset %s not found", dataset_id)
        return

    if not dataset.normalized_parquet:
        logger.error("generate_export: no parquet key for dataset %s", dataset_id)
        return

    export_fn, error_cls, timestamp_field = _EXPORTERS[fmt]

    if getattr(dataset, timestamp_field):
        return

    try:
        export_fn(dataset)
    except error_cls:
        logger.exception("generate_export: %s failed for dataset %s", fmt, dataset_id)
        return

    Dataset.objects.filter(id=dataset_id).update(**{timestamp_field: timezone.now()})


@shared_task
def generate_report(dataset_id: int) -> None:
    try:
        dataset = Dataset.objects.get(id=dataset_id)
    except Dataset.DoesNotExist:
        logger.error("generate_report: dataset %s not found", dataset_id)
        return

    if not dataset.normalized_parquet:
        logger.error("generate_report: no parquet key for dataset %s", dataset_id)
        return

    if dataset.pdf_exported_at:
        return

    try:
        export_report(dataset)
    except PDFExportError:
        logger.exception("generate_report: failed for dataset %s", dataset_id)
        return

    Dataset.objects.filter(id=dataset_id).update(pdf_exported_at=timezone.now())
