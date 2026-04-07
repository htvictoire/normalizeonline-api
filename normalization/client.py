import requests
from django.conf import settings
from normalization.serializers import (
    NormalizeInstanceSerializer,
    NormalizeSuggestRequestSerializer,
)


class NormalizeClientError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NormalizeClient:
    FILE_TYPE_TO_SOURCE_FILE_FORMAT = {
        "CSV": "csv",
        "XLSX": "excel",
        "JSON": "json",
    }

    def __init__(self):
        self.base_url = settings.NORMALIZE_SERVICE_URL

    def _extract_error_message(self, response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str):
                return detail
            if detail is not None:
                return str(detail)
            message = payload.get("message")
            if isinstance(message, str):
                return message

        return response.text.strip() or "Normalize service returned an error."

    def suggest(
        self,
        *,
        source_file: str,
        source_file_name: str,
        file_type: str,
        source_checksum: str,
    ) -> dict:
        """
        POST /normalize/suggest
        Returns validated and mapped instance data ready to apply to a Dataset.
        """
        try:
            source_file_format = self.FILE_TYPE_TO_SOURCE_FILE_FORMAT[file_type]
        except KeyError as exc:
            raise NormalizeClientError(
                f"Unsupported dataset file type: {file_type}",
                status_code=400,
            ) from exc

        payload_serializer = NormalizeSuggestRequestSerializer(
            data={
                "source_file": source_file,
                "source_type": "s3",
                "source_file_name": source_file_name,
                "source_file_format": source_file_format,
                "source_checksum": source_checksum,
            }
        )
        payload_serializer.is_valid(raise_exception=True)

        try:
            response = requests.post(
                f"{self.base_url}/normalize/suggest",
                json=payload_serializer.validated_data,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise NormalizeClientError(
                "Failed to reach normalize service.",
                status_code=502,
            ) from exc

        if response.status_code >= 500:
            raise NormalizeClientError(
                "Normalize service returned an internal error.",
                status_code=502,
            )
        if response.status_code >= 400:
            raise NormalizeClientError(
                self._extract_error_message(response),
                status_code=response.status_code,
            )

        serializer = NormalizeInstanceSerializer(data=response.json())
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
