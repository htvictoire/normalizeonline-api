from __future__ import annotations

from pathlib import PurePosixPath

from storage.s3 import delete_object
from export._duckdb import s3_connection, s3_url


class JSONExportError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_json_export_key(parquet_key: str) -> str:
    parquet_path = PurePosixPath(parquet_key)
    stem = parquet_path.stem if parquet_path.suffix == ".parquet" else parquet_path.name
    return str(parquet_path.with_name(f"{stem}.json"))


def export_json(parquet_key: str) -> str:
    export_key = build_json_export_key(parquet_key)
    try:
        with s3_connection() as con:
            con.execute(f"""
                COPY (SELECT * FROM read_parquet('{s3_url(parquet_key)}'))
                TO '{s3_url(export_key)}' (FORMAT JSON, ARRAY TRUE)
            """)
    except Exception as exc:
        delete_object(export_key)
        raise JSONExportError("Failed to generate JSON export.") from exc
    return export_key
