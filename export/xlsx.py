from __future__ import annotations

import math
import tempfile
from pathlib import Path, PurePosixPath

from pyexcelerate import Workbook

from export._duckdb import s3_connection, s3_url
from storage.s3 import delete_object, get_client
from django.conf import settings

ROWS_PER_SHEET  = 1_000_000
MAX_SHEETS      = 5
FETCH_BATCH_SIZE = 10_000


class XLSXExportError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_xlsx_export_key(parquet_key: str) -> str:
    parquet_path = PurePosixPath(parquet_key)
    stem = parquet_path.stem if parquet_path.suffix == ".parquet" else parquet_path.name
    return str(parquet_path.with_name(f"{stem}.xlsx"))


def export_xlsx(parquet_key: str, row_count: int) -> str:
    export_key = build_xlsx_export_key(parquet_key)
    try:
        _convert(parquet_key, export_key, row_count)
    except Exception as exc:
        delete_object(export_key)
        raise XLSXExportError("Failed to generate XLSX export.") from exc
    return export_key


def _convert(parquet_key: str, export_key: str, row_count: int) -> None:
    src = s3_url(parquet_key)
    n_sheets = min(math.ceil(row_count / ROWS_PER_SHEET), MAX_SHEETS)

    with tempfile.TemporaryDirectory(prefix="normalizeonline-xlsx-") as tmp_dir:
        tmp_path = Path(tmp_dir) / "export.xlsx"
        with s3_connection() as con:
            headers = [desc[0] for desc in con.execute(f"SELECT * FROM read_parquet('{src}') LIMIT 0").description]
            wb = Workbook()
            for i in range(n_sheets):
                wb.new_sheet(f"Sheet {i + 1}", data=_rows(con, src, headers, offset=i * ROWS_PER_SHEET))
            wb.save(str(tmp_path))
        get_client().upload_file(str(tmp_path), settings.S3_BUCKET_NAME, export_key)


def _rows(con, src: str, headers: list[str], offset: int):
    yield headers
    result = con.execute(f"""
        SELECT * FROM read_parquet('{src}')
        LIMIT {ROWS_PER_SHEET} OFFSET {offset}
    """)
    while batch := result.fetchmany(FETCH_BATCH_SIZE):
        yield from batch
