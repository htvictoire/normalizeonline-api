from __future__ import annotations

from pathlib import PurePosixPath

from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.normalization.models import Dataset
from storage.s3 import delete_object, get_client

from .context import build_report_context


class PDFExportError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_report_export_key(parquet_key: str) -> str:
    parquet_path = PurePosixPath(parquet_key)
    stem = parquet_path.stem if parquet_path.suffix == ".parquet" else parquet_path.name
    return str(parquet_path.with_name(f"{stem}_report.pdf"))


def export_report(dataset: Dataset) -> str:
    parquet_key = dataset.normalized_parquet
    if not parquet_key:
        raise PDFExportError("Failed to generate PDF report.", status_code=409)

    export_key = build_report_export_key(parquet_key)
    try:
        pdf = render_report(dataset)
        get_client().put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=export_key,
            Body=pdf,
            ContentType="application/pdf",
        )
    except Exception as exc:
        delete_object(export_key)
        raise PDFExportError("Failed to generate PDF report.") from exc
    return export_key


def render_report(dataset: Dataset) -> bytes:
    html = render_to_string("export/report.html", build_report_context(dataset))
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
