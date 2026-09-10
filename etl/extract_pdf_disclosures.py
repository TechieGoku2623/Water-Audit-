from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Iterable

import pdfplumber

from etl.logging_utils import log_transformation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DISCLOSURES_DIR = PROJECT_ROOT / "data" / "raw" / "disclosures"
SOURCE_INDEX_PATH = RAW_DISCLOSURES_DIR / "source_index.csv"
EXTRACTED_OUTPUT_PATH = PROJECT_ROOT / "data" / "staging" / "disclosures.csv"
MANUAL_TEMPLATE_PATH = (
    PROJECT_ROOT / "data" / "staging" / "disclosures_manual_entry_template.csv"
)

REQUIRED_COLUMNS = ["facility_id", "year", "wue_l_per_kwh", "pue", "source_url"]
MANUAL_TEMPLATE_COLUMNS = REQUIRED_COLUMNS + ["source_pdf_path", "notes"]


def load_source_index(path: Path) -> dict[str, str]:
    """Load mapping: pdf_filename -> source_url."""
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"pdf_filename", "source_url"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(
                f"{path} must contain columns: {sorted(required)} "
                f"(found: {reader.fieldnames})"
            )
        mapping = {}
        for row in reader:
            pdf_filename = (row.get("pdf_filename") or "").strip()
            source_url = (row.get("source_url") or "").strip()
            if pdf_filename and source_url:
                mapping[pdf_filename] = source_url
        return mapping


def parse_number(cell: str | None) -> float | None:
    if not cell:
        return None
    normalized = re.sub(r"[^0-9.\-]", "", cell)
    if not normalized:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def parse_year(cell: str | None) -> int | None:
    if not cell:
        return None
    match = re.search(r"(19|20)\d{2}", cell)
    if not match:
        return None
    return int(match.group(0))


def facility_id_from_filename(path: Path) -> str:
    # Expected convention: <facility_id>__anything.pdf; fallback to stem.
    return path.stem.split("__", maxsplit=1)[0].strip().lower().replace(" ", "_")


def extract_candidate_rows(pdf_path: Path) -> Iterable[dict[str, object]]:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 2:
                    continue
                header = [str(col or "").strip().lower() for col in table[0]]
                header_text = " ".join(header)
                if "wue" not in header_text and "pue" not in header_text:
                    continue

                for raw_row in table[1:]:
                    row_cells = [str(cell or "").strip() for cell in raw_row]
                    if not any(row_cells):
                        continue

                    year = None
                    wue = None
                    pue = None
                    for idx, cell in enumerate(row_cells):
                        col_name = header[idx] if idx < len(header) else ""
                        if year is None and ("year" in col_name or re.search(r"(19|20)\d{2}", cell)):
                            year = parse_year(cell)
                        if wue is None and "wue" in col_name:
                            wue = parse_number(cell)
                        if pue is None and "pue" in col_name:
                            pue = parse_number(cell)

                    if year is not None and (wue is not None or pue is not None):
                        yield {"year": year, "wue_l_per_kwh": wue, "pue": pue}


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run(disclosures_dir: Path = RAW_DISCLOSURES_DIR) -> None:
    source_index = load_source_index(SOURCE_INDEX_PATH)
    pdf_paths = sorted(disclosures_dir.glob("*.pdf"))

    extracted_rows: list[dict[str, object]] = []
    manual_rows: list[dict[str, object]] = []

    for pdf_path in pdf_paths:
        source_url = source_index.get(pdf_path.name, "").strip()
        facility_id = facility_id_from_filename(pdf_path)
        candidates = list(extract_candidate_rows(pdf_path))

        if not source_url:
            manual_rows.append(
                {
                    "facility_id": facility_id,
                    "year": "",
                    "wue_l_per_kwh": "",
                    "pue": "",
                    "source_url": "",
                    "source_pdf_path": str(pdf_path),
                    "notes": "Missing source_url in data/raw/disclosures/source_index.csv",
                }
            )
            continue

        if not candidates:
            manual_rows.append(
                {
                    "facility_id": facility_id,
                    "year": "",
                    "wue_l_per_kwh": "",
                    "pue": "",
                    "source_url": source_url,
                    "source_pdf_path": str(pdf_path),
                    "notes": "No parseable WUE/PUE table found; manual entry required",
                }
            )
            continue

        for row in candidates:
            extracted_rows.append(
                {
                    "facility_id": facility_id,
                    "year": row["year"],
                    "wue_l_per_kwh": row["wue_l_per_kwh"],
                    "pue": row["pue"],
                    "source_url": source_url,
                }
            )

    write_csv(EXTRACTED_OUTPUT_PATH, extracted_rows, REQUIRED_COLUMNS)
    write_csv(MANUAL_TEMPLATE_PATH, manual_rows, MANUAL_TEMPLATE_COLUMNS)

    log_transformation(
        step="extract_pdf_disclosures",
        status="success",
        details={
            "pdf_count": len(pdf_paths),
            "extracted_row_count": len(extracted_rows),
            "manual_row_count": len(manual_rows),
            "source_index_path": str(SOURCE_INDEX_PATH),
            "output_path": str(EXTRACTED_OUTPUT_PATH),
            "manual_template_path": str(MANUAL_TEMPLATE_PATH),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract WUE/PUE disclosure rows from PDFs in data/raw/disclosures using "
            "pdfplumber. If extraction is not possible, scaffold manual-entry rows."
        )
    )
    parser.add_argument(
        "--disclosures-dir",
        type=Path,
        default=RAW_DISCLOSURES_DIR,
        help="Directory containing source disclosure PDFs.",
    )
    args = parser.parse_args()
    run(args.disclosures_dir)


if __name__ == "__main__":
    main()
