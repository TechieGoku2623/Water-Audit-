from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from etl.logging_utils import log_transformation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGING_DIR = PROJECT_ROOT / "data" / "staging"

TABLE_TO_FILE = {
    "facilities": STAGING_DIR / "facilities.csv",
    "disclosures": STAGING_DIR / "disclosures.csv",
    "permits": STAGING_DIR / "permits.csv",
    "climate": STAGING_DIR / "climate.csv",
}


def validate_csv_source_urls(table_name: str, file_path: Path) -> tuple[int, list[int]]:
    if not file_path.exists():
        raise FileNotFoundError(f"Expected staging file for {table_name}: {file_path}")

    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if "source_url" not in (reader.fieldnames or []):
            raise ValueError(
                f"{file_path} is missing required `source_url` column. "
                "Every data row must preserve provenance."
            )
        null_rows: list[int] = []
        row_count = 0
        for idx, row in enumerate(reader, start=2):  # header is row 1
            row_count += 1
            source_url = (row.get("source_url") or "").strip()
            if not source_url:
                null_rows.append(idx)
        return row_count, null_rows


def run(fail_on_missing_climate: bool = False) -> int:
    failures: list[str] = []
    summary: dict[str, dict[str, int]] = {}

    for table_name in ("facilities", "disclosures", "permits", "climate"):
        file_path = TABLE_TO_FILE[table_name]
        if table_name == "climate" and not fail_on_missing_climate and not file_path.exists():
            summary[table_name] = {"row_count": 0, "missing_source_rows": 0}
            continue

        row_count, null_rows = validate_csv_source_urls(table_name=table_name, file_path=file_path)
        summary[table_name] = {
            "row_count": row_count,
            "missing_source_rows": len(null_rows),
        }
        if null_rows:
            failures.append(
                f"{table_name}: {len(null_rows)} rows missing source_url at CSV line(s) {null_rows}"
            )

    if failures:
        log_transformation(
            step="validate_sources",
            status="failed",
            details={"summary": summary, "failures": failures},
        )
        print("SOURCE VALIDATION FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1

    log_transformation(
        step="validate_sources",
        status="success",
        details={"summary": summary},
    )
    print("SOURCE VALIDATION PASSED: no null source_url values found.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fail if any facilities/disclosures/permits/climate row has null source_url."
    )
    parser.add_argument(
        "--fail-on-missing-climate",
        action="store_true",
        help="Treat missing climate.csv as an error.",
    )
    args = parser.parse_args()
    exit_code = run(fail_on_missing_climate=args.fail_on_missing_climate)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
