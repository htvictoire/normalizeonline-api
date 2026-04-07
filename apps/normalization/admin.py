from django.contrib import admin
from apps.normalization.models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "file_type", "status", "created_at")
    search_fields = ("id", "name", "original_name", "owner", "status")
    list_filter = ("file_type", "status", "created_at")
