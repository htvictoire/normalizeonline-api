from django.db import models
from drf_commons.models import BaseModelMixin


class Dataset(BaseModelMixin, models.Model):
    """
    Represents a single file uploaded by the user for normalization.

    Identity fields (name, file_type, s3_key, size_mb) are set on creation from
    data the frontend already has after the R2 upload.

    Normalize instance fields (instance_id through normalization_output) are a flat
    mirror of the normalize service InstanceModel. They are all null on creation and
    populated as the normalize lifecycle advances: suggest -> confirm -> profile -> normalize.
    """

    class FileType(models.TextChoices):
        CSV   = "csv",   "CSV"
        XLSX  = "xlsx",  "XLSX"
        JSON  = "json",  "JSON"

    owner = models.UUIDField(
        help_text="Guest ID or User ID depending on the authentication."
    )
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=16, choices=FileType.choices)
    s3_key = models.CharField(max_length=1024)
    size_mb = models.FloatField()
    instance_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=64, null=True, blank=True)
    tenant_id = models.CharField(max_length=255, null=True, blank=True)
    source_file_name = models.CharField(max_length=1024, null=True, blank=True)
    source_file_format = models.CharField(max_length=16, null=True, blank=True)
    source_type = models.CharField(max_length=16, default="s3")
    source_file = models.CharField(max_length=2048, null=True, blank=True)
    source_checksum = models.CharField(max_length=64, null=True, blank=True)
    suggested_config = models.JSONField(null=True, blank=True)
    suggestion_display = models.JSONField(null=True, blank=True)
    confirmed_config = models.JSONField(null=True, blank=True)
    profiling_output = models.JSONField(null=True, blank=True)
    normalization_output = models.JSONField(null=True, blank=True)
    timings = models.JSONField(null=True, blank=True)
    webhook_url = models.URLField(max_length=2048, null=True, blank=True)
    csv_exported_at   = models.DateTimeField(null=True, blank=True)
    xlsx_exported_at  = models.DateTimeField(null=True, blank=True)
    json_exported_at  = models.DateTimeField(null=True, blank=True)
    pdf_exported_at   = models.DateTimeField(null=True, blank=True)

    @property
    def normalized_parquet(self) -> str | None:
        return (self.normalization_output or {}).get("artifacts", {}).get("normalized_parquet")

    @property
    def manifest_json(self) -> str | None:
        return (self.normalization_output or {}).get("artifacts", {}).get("manifest_json")

    @property
    def trace_parquet(self) -> str | None:
        return (self.normalization_output or {}).get("artifacts", {}).get("trace_parquet")

    @property
    def normalized_row_count(self) -> int | None:
        return (self.normalization_output or {}).get("quality_output", {}).get("row_count")

    def __str__(self):
        return f"{self.name} ({self.status})"
