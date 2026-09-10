from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from etl.logging_utils import log_transformation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_REGIONS_PATH = PROJECT_ROOT / "data" / "staging" / "target_regions.csv"
CLIMATE_OUTPUT_PATH = PROJECT_ROOT / "data" / "staging" / "climate.csv"

CDO_BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"
ACCESS_BASE_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
REQUIRED_COLUMNS = {"region", "lat", "lon", "source_url"}


def c_to_f(value_c: float) -> float:
    return (value_c * 9.0 / 5.0) + 32.0


def relative_humidity_from_temp_dewpoint(temp_c: float, dewpoint_c: float) -> float:
    # Magnus approximation.
    a = 17.625
    b = 243.04
    alpha_td = (a * dewpoint_c) / (b + dewpoint_c)
    alpha_t = (a * temp_c) / (b + temp_c)
    rh = 100.0 * math.exp(alpha_td - alpha_t)
    return max(0.0, min(100.0, rh))


def read_target_regions(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing target regions file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        if not REQUIRED_COLUMNS.issubset(fieldnames):
            raise ValueError(
                f"{path} must contain columns {sorted(REQUIRED_COLUMNS)}; found {sorted(fieldnames)}"
            )
        rows = []
        for row in reader:
            cleaned = {k: (row.get(k) or "").strip() for k in REQUIRED_COLUMNS}
            if not cleaned["region"]:
                continue
            rows.append(cleaned)
        return rows


def find_nearest_station(
    lat: float,
    lon: float,
    token: str,
    search_radius_deg: float = 1.5,
) -> str | None:
    extent = f"{lat-search_radius_deg},{lon-search_radius_deg},{lat+search_radius_deg},{lon+search_radius_deg}"
    params = {
        "extent": extent,
        "datasetid": "GSOM",
        "limit": 1000,
    }
    resp = requests.get(
        f"{CDO_BASE_URL}/stations",
        params=params,
        headers={"token": token},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    stations = payload.get("results", [])
    if not stations:
        return None

    def sq_distance(item: dict[str, Any]) -> float:
        return (float(item["latitude"]) - lat) ** 2 + (float(item["longitude"]) - lon) ** 2

    return min(stations, key=sq_distance).get("id")


def fetch_monthly_noaa_data(
    station_id: str,
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], str]:
    params = {
        "dataset": "global-summary-of-the-month",
        "stations": station_id,
        "startDate": f"{start_year}-01",
        "endDate": f"{end_year}-12",
        "format": "json",
        "includeAttributes": "false",
        "units": "metric",
    }
    url = f"{ACCESS_BASE_URL}?{urlencode(params)}"
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    return resp.json(), url


def _parse_float(candidate: Any) -> float | None:
    if candidate is None or candidate == "":
        return None
    try:
        return float(candidate)
    except (TypeError, ValueError):
        return None


def normalize_monthly_records(raw_records: list[dict[str, Any]]) -> dict[int, dict[str, float | None]]:
    temp_values: dict[int, list[float]] = defaultdict(list)
    humidity_values: dict[int, list[float]] = defaultdict(list)

    for row in raw_records:
        date_text = str(row.get("DATE", "")).strip()
        if len(date_text) < 7:
            continue
        month = int(date_text[5:7])

        temp_c = (
            _parse_float(row.get("TAVG"))
            or _parse_float(row.get("TMP"))
            or _parse_float(row.get("TEMP"))
        )
        dew_c = (
            _parse_float(row.get("DEWP"))
            or _parse_float(row.get("DEW"))
            or _parse_float(row.get("DPTP"))
        )
        humidity_direct = _parse_float(row.get("RHAV")) or _parse_float(row.get("HUMIDITY"))

        if temp_c is not None:
            temp_values[month].append(temp_c)
        if humidity_direct is not None:
            humidity_values[month].append(humidity_direct)
        elif temp_c is not None and dew_c is not None:
            humidity_values[month].append(
                relative_humidity_from_temp_dewpoint(temp_c=temp_c, dewpoint_c=dew_c)
            )

    output: dict[int, dict[str, float | None]] = {}
    for month in range(1, 13):
        month_temps = temp_values.get(month, [])
        month_humidity = humidity_values.get(month, [])
        output[month] = {
            "avg_temp_f": c_to_f(sum(month_temps) / len(month_temps)) if month_temps else None,
            "avg_humidity_pct": (
                sum(month_humidity) / len(month_humidity) if month_humidity else None
            ),
        }
    return output


def write_climate_rows(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["region", "month", "avg_temp_f", "avg_humidity_pct", "source_url"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run(start_year: int, end_year: int) -> None:
    token = os.getenv("NOAA_API_TOKEN")
    if not token:
        raise RuntimeError(
            "NOAA_API_TOKEN is required to query station metadata from NOAA CDO API."
        )

    regions = read_target_regions(TARGET_REGIONS_PATH)
    all_rows: list[dict[str, Any]] = []
    missing_regions: list[str] = []

    for region in regions:
        name = region["region"]
        lat = float(region["lat"])
        lon = float(region["lon"])
        station_id = find_nearest_station(lat=lat, lon=lon, token=token)
        if not station_id:
            missing_regions.append(name)
            continue

        raw_records, source_url = fetch_monthly_noaa_data(
            station_id=station_id,
            start_year=start_year,
            end_year=end_year,
        )
        monthly = normalize_monthly_records(raw_records)
        for month, climate_row in monthly.items():
            all_rows.append(
                {
                    "region": name,
                    "month": month,
                    "avg_temp_f": climate_row["avg_temp_f"],
                    "avg_humidity_pct": climate_row["avg_humidity_pct"],
                    "source_url": source_url,
                }
            )

    write_climate_rows(all_rows, CLIMATE_OUTPUT_PATH)
    log_transformation(
        step="fetch_noaa_climate",
        status="success",
        details={
            "region_count": len(regions),
            "written_row_count": len(all_rows),
            "missing_regions": missing_regions,
            "start_year": start_year,
            "end_year": end_year,
            "output_path": str(CLIMATE_OUTPUT_PATH),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch monthly regional temperature/humidity from NOAA public APIs "
            "and write data/staging/climate.csv"
        )
    )
    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int, default=2025)
    args = parser.parse_args()
    run(start_year=args.start_year, end_year=args.end_year)


if __name__ == "__main__":
    main()
