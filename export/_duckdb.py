from __future__ import annotations

import tempfile
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

import duckdb
from duckdb import DuckDBPyConnection
from django.conf import settings


def _esc(value: str) -> str:
    return value.replace("'", "''")


@contextmanager
def s3_connection() -> Iterator[DuckDBPyConnection]:
    parsed = urlparse(settings.S3_ENDPOINT_URL)
    endpoint = parsed.netloc or parsed.path
    use_ssl = "true" if parsed.scheme == "https" else "false"

    with tempfile.TemporaryDirectory(prefix="normalizeonline-export-") as tmp:
        with duckdb.connect() as con:
            con.execute(f"SET temp_directory='{_esc(tmp)}'")
            con.execute(f"SET memory_limit='{_esc(settings.DUCKDB_EXPORT_MEMORY_LIMIT)}'")
            con.execute(f"SET threads={int(settings.DUCKDB_EXPORT_THREADS)}")
            con.execute(f"""
                CREATE SECRET (
                    TYPE S3,
                    KEY_ID '{_esc(settings.S3_ACCESS_KEY_ID)}',
                    SECRET '{_esc(settings.S3_SECRET_ACCESS_KEY)}',
                    ENDPOINT '{_esc(endpoint)}',
                    REGION '{_esc(settings.S3_REGION)}',
                    URL_STYLE 'path',
                    USE_SSL {use_ssl}
                )
            """)
            yield con


def s3_url(key: str) -> str:
    return _esc(f"s3://{settings.S3_BUCKET_NAME}/{key}")
