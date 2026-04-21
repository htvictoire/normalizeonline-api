import os
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from drf_commons.response import success_response, error_response
from drf_commons.views import CreateModelMixin, RetrieveModelMixin
from apps.accounts.utils import get_current_owner
from core.decorators import ensure_owner, ensure_is_owner
from apps.normalization.models import Dataset
from apps.normalization.serializers import DatasetSerializer
from normalize import NormalizeClient, NormalizeClientError, NormalizeConfirmRequestSerializer
from storage.s3 import generate_upload_url, generate_download_url


class DatasetViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    filterset_fields = ["status", "file_type"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        owner = get_current_owner(self.request)
        if not owner:
            return super().get_queryset().none()
        return super().get_queryset().filter(owner=owner).order_by("-created_at")

    @action(detail=False, methods=["get"], url_path="upload-url")
    @ensure_owner
    def upload_url(self, request):
        filename = request.query_params.get("filename")
        if not filename:
            return error_response(
                message="filename query parameter is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        owner = get_current_owner(request)
        url, s3_key = generate_upload_url(owner_id=str(owner), filename=filename)
        return success_response(data={"url": url, "s3_key": s3_key})

    @ensure_owner
    def create(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = serializer.save(owner=get_current_owner(request))

        suggest_payload = {
            "source_file":        dataset.s3_key,
            "source_type":        "s3",
            "source_file_name":   dataset.original_name,
            "source_file_format": dataset.file_type,
            "source_checksum":    dataset.source_checksum,
        }

        normalize_client = NormalizeClient()
        try:
            response = normalize_client.suggest(payload=suggest_payload)
        except NormalizeClientError as exc:
            dataset.soft_delete()
            return error_response(message=exc.message, status_code=exc.status_code)

        serializer = self.get_serializer(dataset, data=response, partial=True)
        serializer.is_valid(raise_exception=True)
        dataset = serializer.save()
        return success_response(
            data=serializer.validated_data,
            message="Dataset created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="download")
    @ensure_is_owner
    def download(self, request, pk=None):
        dataset = self.get_object()

        if not dataset.normalization_output:
            return error_response(
                message="Dataset normalization output is not available.",
                status_code=status.HTTP_409_CONFLICT,
            )

        s3_key = dataset.normalization_output.get("artifacts", {}).get("normalized_parquet")
        if not s3_key:
            return error_response(
                message="Output file not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        base_name = os.path.splitext(dataset.original_name)[0]
        filename = f"{base_name}_normalized.parquet"
        url = generate_download_url(s3_key=s3_key, filename=filename)
        return success_response(data={"url": url, "filename": filename})

    @action(detail=True, methods=["post"], url_path="confirm")
    @ensure_is_owner
    def confirm(self, request, pk=None):
        dataset = self.get_object()

        if not dataset.instance_id:
            return error_response(
                message="Dataset has no associated instance.",
            )

        webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/normalization/webhook/instance-status/"

        confirm_serializer = NormalizeConfirmRequestSerializer(data={
            "config":                request.data.get("confirmed_config"),
            "proceed_with_pipeline": True,
            "webhook_url":           webhook_url,
        })
        if not confirm_serializer.is_valid():
            return error_response(
                message="Invalid confirmation payload.",
                errors=confirm_serializer.errors,
            )

        normalize_client = NormalizeClient()
        try:
            response = normalize_client.confirm(
                instance_id=str(dataset.instance_id),
                payload=confirm_serializer.validated_data,
            )
        except NormalizeClientError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)

        serializer = self.get_serializer(dataset, data=response, partial=True)
        serializer.is_valid(raise_exception=True)
        dataset = serializer.save()
        return success_response(data=serializer.data, message="Dataset confirmed successfully and normalization started.")


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def instance_status_webhook(request):
    instance_id = request.data.get("instance_id")
    if not instance_id:
        return error_response(message="instance_id is required in the payload.")

    try:
        dataset = Dataset.objects.get(instance_id=instance_id)
    except Dataset.DoesNotExist:
        logger.error("Webhook received for unknown instance %s", instance_id)
        return error_response(message="Dataset not found for the given instance_id.", status_code=status.HTTP_404_NOT_FOUND)

    normalize_client = NormalizeClient()
    try:
        instance_data = normalize_client.fetch_instance(instance_id=str(instance_id))
    except NormalizeClientError as exc:
        return error_response(message="Failed to fetch instance data.", status_code=exc.status_code)

    serializer = DatasetSerializer(dataset, data=instance_data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return success_response(message="OK")
