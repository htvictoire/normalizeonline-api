from logging import getLogger
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from drf_commons.response import success_response, error_response
from drf_commons.views import CreateModelMixin, RetrieveModelMixin
from apps.accounts.utils import get_current_owner
from core.decorators import ensure_owner
from apps.normalization.models import Dataset
from apps.normalization.serializers import DatasetSerializer
from normalization.client import NormalizeClient, NormalizeClientError
from storage.s3 import generate_upload_url

logger = getLogger(__name__)


class DatasetViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    filterset_fields = ["status", "file_type"]

    def get_queryset(self):
        owner = get_current_owner(self.request)
        if not owner:
            return super().get_queryset().none()
        return super().get_queryset().filter(owner=owner).order_by("-created_at")

    def get_permissions(self):
        if self.action in ["create", "retrieve", "upload_url"]:
            return [permissions.AllowAny()]
        return super().get_permissions()

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

        normalize_client = NormalizeClient()
        try:
            response = normalize_client.suggest(
                source_file=dataset.s3_key,
                source_file_name=dataset.original_name,
                file_type=dataset.file_type,
                source_checksum=dataset.source_checksum,
            )
            logger.info(
                "Normalization suggestion response for dataset %s: %s",
                dataset.id,
                response,
            )
        except serializers.ValidationError as exc:
            logger.warning(
                "Invalid normalization payload for dataset %s: %s",
                dataset.id,
                exc.detail,
            )
            dataset.delete()
            return error_response(
                message="Invalid normalization payload.",
                errors=exc.detail,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except NormalizeClientError as exc:
            logger.warning(
                "Normalization request failed for dataset %s with status %s: %s",
                dataset.id,
                exc.status_code,
                exc.message,
            )
            dataset.delete()
            return error_response(
                message=exc.message,
                status_code=exc.status_code,
            )
        except Exception:
            logger.exception(
                "Error getting normalization suggestion for dataset %s", dataset.id
            )
            dataset.delete()
            return error_response(
                message="Failed to get normalization suggestion, please try again later.",
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        for attr, value in response.items():
            setattr(dataset, attr, value)
        dataset.save()
        dataset.refresh_from_db()
        return success_response(
            data=self.get_serializer(dataset).data,
            message="Dataset created successfully.",
            status_code=status.HTTP_201_CREATED,
        )
