from __future__ import annotations

import csv
from pathlib import Path

from src.schemas import CSV_FIELDS, InvoiceRecord


def write_csv(records: list[InvoiceRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for record in records:
            row = record.model_dump()
            writer.writerow({field: _csv_value(row.get(field)) for field in CSV_FIELDS})


def _csv_value(value: object) -> object:
    if value is None:
        return ""
    return value
