from __future__ import annotations

from pathlib import PurePosixPath

from storage.s3 import delete_object
from export._duckdb import s3_connection, s3_url


class CSVExportError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_export_key(parquet_key: str) -> str:
    parquet_path = PurePosixPath(parquet_key)
    stem = parquet_path.stem if parquet_path.suffix == ".parquet" else parquet_path.name
    return str(parquet_path.with_name(f"{stem}.csv"))


def export_csv(parquet_key: str) -> str:
    export_key = build_export_key(parquet_key)
    try:
        with s3_connection() as con:
            con.execute(f"""
                COPY (SELECT * FROM read_parquet('{s3_url(parquet_key)}'))
                TO '{s3_url(export_key)}' (FORMAT CSV, HEADER TRUE)
            """)
    except Exception as exc:
        delete_object(export_key)
        raise CSVExportError("Failed to generate CSV export.") from exc
    return export_key
