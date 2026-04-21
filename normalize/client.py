import requests
from logging import getLogger
from django.conf import settings
from normalize.serializers import NormalizeInstanceSerializer

logger = getLogger(__name__)


class NormalizeClientError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NormalizeClient:
    def __init__(self):
        self.base_url = settings.NORMALIZE_SERVICE_URL

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            return requests.request(method, f"{self.base_url}{path}", **kwargs)
        except requests.RequestException as exc:
            logger.error("Normalize service unreachable [%s %s]: %s", method, path, exc)
            raise NormalizeClientError("Failed to reach normalize service.", status_code=502) from exc

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.status_code >= 500:
            logger.error("Normalize service internal error [%s]: %s", response.status_code, response.text[:200])
            raise NormalizeClientError("Normalize service returned an internal error.", status_code=502)
        if response.status_code >= 400:
            logger.warning("Normalize service error [%s]: %s", response.status_code, response.text[:200])
            raise NormalizeClientError("Normalize service returned an error.", status_code=response.status_code)

    def _parse_instance(self, response: requests.Response) -> dict:
        self._raise_for_status(response)
        serializer = NormalizeInstanceSerializer(data=response.json())
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def suggest(self, *, payload: dict) -> dict:
        """POST /normalize/suggest"""
        return self._parse_instance(self._request("POST", "/normalize/suggest", json=payload, timeout=30))

    def confirm(self, *, instance_id: str, payload: dict) -> dict:
        """PUT /normalize/instances/{id}/confirm"""
        return self._parse_instance(self._request("PUT", f"/normalize/instances/{instance_id}/confirm", json=payload, timeout=30))

    def fetch_instance(self, *, instance_id: str) -> dict:
        """GET /normalize/instances/{id}"""
        return self._parse_instance(self._request("GET", f"/normalize/instances/{instance_id}", timeout=15))
