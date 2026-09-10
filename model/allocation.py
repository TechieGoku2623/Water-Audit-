from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from etl.logging_utils import log_transformation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGING_DIR = PROJECT_ROOT / "data" / "staging"

FACILITIES_PATH = STAGING_DIR / "facilities.csv"
DISCLOSURES_PATH = STAGING_DIR / "disclosures.csv"
CLIMATE_PATH = STAGING_DIR / "climate.csv"

TEMP_COEFF = 0.003
HUMIDITY_COEFF = 0.001

ASSUMPTIONS_USED = [
    "A-001 peer average fallback for missing facility WUE",
    "A-002 confidence downgrade for sparse peer groups",
    "A-003 linear seasonal climate adjustment",
    "A-004 workload energy from hardware TDP lookup",
    "A-005 unsourced/missing data remains null",
]

# Source URLs are public manufacturer specification pages.
HARDWARE_TDP_WATTS = {
    "h100": {
        "tdp_watts": 700.0,
        "source_url": "https://www.nvidia.com/en-us/data-center/h100/",
    },
    "a100": {
        "tdp_watts": 400.0,
        "source_url": "https://www.nvidia.com/en-us/data-center/a100/",
    },
    "l40s": {
        "tdp_watts": 350.0,
        "source_url": "https://www.nvidia.com/en-us/data-center/l40s/",
    },
}


@dataclass
class DataBundle:
    facilities: pd.DataFrame
    disclosures: pd.DataFrame
    climate: pd.DataFrame


def _safe_read_csv(path: Path, expected_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=expected_columns)
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=expected_columns)
    for column in expected_columns:
        if column not in df.columns:
            df[column] = pd.NA
    return df


def load_default_data() -> DataBundle:
    return DataBundle(
        facilities=_safe_read_csv(
            FACILITIES_PATH,
            [
                "facility_id",
                "company",
                "name",
                "region",
                "lat",
                "lon",
                "it_capacity_mw",
                "cooling_type",
                "source_url",
            ],
        ),
        disclosures=_safe_read_csv(
            DISCLOSURES_PATH,
            ["facility_id", "year", "wue_l_per_kwh", "pue", "source_url"],
        ),
        climate=_safe_read_csv(
            CLIMATE_PATH,
            ["region", "month", "avg_temp_f", "avg_humidity_pct", "source_url"],
        ),
    )


def _climate_bucket_for_region(region: str, climate_df: pd.DataFrame) -> str:
    subset = climate_df[climate_df["region"] == region]
    if subset.empty:
        return "unknown"
    avg_temp = pd.to_numeric(subset["avg_temp_f"], errors="coerce").dropna().mean()
    if pd.isna(avg_temp):
        return "unknown"
    if avg_temp < 55:
        return "cool"
    if avg_temp < 70:
        return "temperate"
    return "hot"


def _combine_sources(*source_lists: list[str]) -> list[str]:
    combined: list[str] = []
    for source_list in source_lists:
        for source in source_list:
            if source and source not in combined:
                combined.append(source)
    return combined


def facility_wue(facility_id: str, data: DataBundle | None = None) -> dict[str, Any]:
    data = data or load_default_data()
    facilities = data.facilities.copy()
    disclosures = data.disclosures.copy()
    climate = data.climate.copy()

    target = facilities[facilities["facility_id"] == facility_id]
    if target.empty:
        result = {
            "facility_id": facility_id,
            "wue_l_per_kwh": None,
            "confidence": "low",
            "sample_size": 0,
            "interval_l": None,
            "interval_u": None,
            "method": "facility_not_found",
            "sources": [],
        }
        log_transformation("facility_wue", "success", result)
        return result

    disclosures["year"] = pd.to_numeric(disclosures["year"], errors="coerce")
    disclosures["wue_l_per_kwh"] = pd.to_numeric(disclosures["wue_l_per_kwh"], errors="coerce")
    direct_rows = disclosures[
        (disclosures["facility_id"] == facility_id) & disclosures["wue_l_per_kwh"].notna()
    ]
    if not direct_rows.empty:
        direct_row = direct_rows.sort_values("year", ascending=False).iloc[0]
        value = float(direct_row["wue_l_per_kwh"])
        result = {
            "facility_id": facility_id,
            "wue_l_per_kwh": value,
            "confidence": "high",
            "sample_size": 1,
            "interval_l": value,
            "interval_u": value,
            "method": "direct_disclosure",
            "sources": [str(direct_row.get("source_url", ""))],
        }
        log_transformation("facility_wue", "success", result)
        return result

    region = str(target.iloc[0]["region"])
    cooling_type = str(target.iloc[0].get("cooling_type", ""))
    target_bucket = _climate_bucket_for_region(region=region, climate_df=climate)

    peers = facilities[facilities["facility_id"] != facility_id].copy()
    if cooling_type:
        peers = peers[peers["cooling_type"] == cooling_type]

    peer_ids = set(peers["facility_id"].dropna().astype(str).tolist())
    peer_disclosures = disclosures[
        disclosures["facility_id"].astype(str).isin(peer_ids) & disclosures["wue_l_per_kwh"].notna()
    ].copy()

    if not peer_disclosures.empty and target_bucket != "unknown":
        peer_region_map = (
            facilities.set_index("facility_id")["region"].dropna().astype(str).to_dict()
        )
        peer_disclosures["region"] = peer_disclosures["facility_id"].map(peer_region_map)
        peer_disclosures["climate_bucket"] = peer_disclosures["region"].map(
            lambda r: _climate_bucket_for_region(region=r, climate_df=climate)
        )
        peer_disclosures = peer_disclosures[peer_disclosures["climate_bucket"] == target_bucket]

    sample_size = int(len(peer_disclosures))
    if sample_size == 0:
        result = {
            "facility_id": facility_id,
            "wue_l_per_kwh": None,
            "confidence": "low",
            "sample_size": 0,
            "interval_l": None,
            "interval_u": None,
            "method": "no_public_data",
            "sources": target["source_url"].dropna().astype(str).tolist()[:1],
        }
        log_transformation("facility_wue", "success", result)
        return result

    values = pd.to_numeric(peer_disclosures["wue_l_per_kwh"], errors="coerce").dropna()
    mean_value = float(values.mean())
    std_value = float(values.std(ddof=0)) if len(values) > 1 else 0.0
    widened_margin = max(mean_value * 0.20, 2.0 * std_value)
    result = {
        "facility_id": facility_id,
        "wue_l_per_kwh": mean_value,
        "confidence": "low",
        "sample_size": sample_size,
        "interval_l": max(0.0, mean_value - widened_margin),
        "interval_u": mean_value + widened_margin,
        "method": "peer_climate_cooling_fallback",
        "sources": peer_disclosures["source_url"].dropna().astype(str).unique().tolist(),
    }
    log_transformation("facility_wue", "success", result)
    return result


def workload_kwh(gpu_hours: float, hardware_type: str) -> dict[str, Any]:
    key = hardware_type.strip().lower()
    if key not in HARDWARE_TDP_WATTS:
        raise ValueError(
            f"Unsupported hardware_type `{hardware_type}`. "
            f"Supported: {sorted(HARDWARE_TDP_WATTS.keys())}"
        )
    tdp = HARDWARE_TDP_WATTS[key]["tdp_watts"]
    kwh = float(gpu_hours) * float(tdp) / 1000.0
    result = {
        "hardware_type": key,
        "gpu_hours": float(gpu_hours),
        "tdp_watts": tdp,
        "kwh": kwh,
        "source_url": HARDWARE_TDP_WATTS[key]["source_url"],
    }
    log_transformation("workload_kwh", "success", result)
    return result


def seasonal_adjustment(
    wue: float | None,
    region: str,
    month: int,
    data: DataBundle | None = None,
) -> dict[str, Any]:
    data = data or load_default_data()
    climate = data.climate.copy()

    if wue is None:
        result = {
            "adjusted_wue_l_per_kwh": None,
            "factor": None,
            "method": "no_base_wue",
            "sources": [],
        }
        log_transformation("seasonal_adjustment", "success", result)
        return result

    climate["month"] = pd.to_numeric(climate["month"], errors="coerce")
    climate["avg_temp_f"] = pd.to_numeric(climate["avg_temp_f"], errors="coerce")
    climate["avg_humidity_pct"] = pd.to_numeric(climate["avg_humidity_pct"], errors="coerce")

    region_rows = climate[climate["region"] == region]
    month_row = region_rows[region_rows["month"] == int(month)]
    if region_rows.empty or month_row.empty:
        result = {
            "adjusted_wue_l_per_kwh": float(wue),
            "factor": 1.0,
            "method": "climate_data_missing",
            "sources": [],
        }
        log_transformation("seasonal_adjustment", "success", result)
        return result

    annual_temp = region_rows["avg_temp_f"].dropna().mean()
    annual_humidity = region_rows["avg_humidity_pct"].dropna().mean()
    month_temp = month_row.iloc[0]["avg_temp_f"]
    month_humidity = month_row.iloc[0]["avg_humidity_pct"]

    delta_temp = 0.0 if pd.isna(annual_temp) or pd.isna(month_temp) else (month_temp - annual_temp)
    delta_humidity = (
        0.0
        if pd.isna(annual_humidity) or pd.isna(month_humidity)
        else (month_humidity - annual_humidity)
    )
    factor = max(0.1, 1.0 + (TEMP_COEFF * float(delta_temp)) + (HUMIDITY_COEFF * float(delta_humidity)))
    adjusted = float(wue) * factor

    result = {
        "adjusted_wue_l_per_kwh": adjusted,
        "factor": factor,
        "method": "linear_temp_humidity_adjustment",
        "sources": region_rows["source_url"].dropna().astype(str).unique().tolist(),
    }
    log_transformation("seasonal_adjustment", "success", result)
    return result


def _regional_wue(region: str, data: DataBundle) -> dict[str, Any]:
    facilities = data.facilities.copy()
    disclosures = data.disclosures.copy()
    disclosures["wue_l_per_kwh"] = pd.to_numeric(disclosures["wue_l_per_kwh"], errors="coerce")

    merged = disclosures.merge(
        facilities[["facility_id", "region"]],
        how="left",
        on="facility_id",
    )
    subset = merged[(merged["region"] == region) & merged["wue_l_per_kwh"].notna()]
    sample_size = int(len(subset))
    if sample_size == 0:
        return {
            "wue_l_per_kwh": None,
            "confidence": "low",
            "sample_size": 0,
            "method": "no_public_data",
            "sources": [],
        }

    return {
        "wue_l_per_kwh": float(subset["wue_l_per_kwh"].mean()),
        "confidence": "high" if sample_size >= 3 else "low",
        "sample_size": sample_size,
        "method": "regional_disclosure_average",
        "sources": subset["source_url"].dropna().astype(str).unique().tolist(),
    }


def estimate_water_cost(workload: dict[str, Any], data: DataBundle | None = None) -> dict[str, Any]:
    """
    Expected workload payload:
      {
        "region": str,
        "hardware_type": str,
        "gpu_hours": float,
        "month": int,
        "facility_id": optional str
      }
    """
    data = data or load_default_data()

    facility_id = workload.get("facility_id")
    region = str(workload["region"])
    month = int(workload["month"])

    if facility_id:
        wue_result = facility_wue(facility_id=str(facility_id), data=data)
    else:
        wue_result = _regional_wue(region=region, data=data)

    kwh_result = workload_kwh(
        gpu_hours=float(workload["gpu_hours"]),
        hardware_type=str(workload["hardware_type"]),
    )

    seasonal_result = seasonal_adjustment(
        wue=wue_result.get("wue_l_per_kwh"),
        region=region,
        month=month,
        data=data,
    )

    adjusted_wue = seasonal_result.get("adjusted_wue_l_per_kwh")
    estimate_liters = (
        None if adjusted_wue is None else float(kwh_result["kwh"]) * float(adjusted_wue)
    )

    confidence = "high"
    if (
        wue_result.get("confidence") != "high"
        or seasonal_result.get("method") != "linear_temp_humidity_adjustment"
    ):
        confidence = "low"

    result = {
        "estimate_liters": estimate_liters,
        "confidence": confidence,
        "sample_size": int(wue_result.get("sample_size", 0)),
        "assumptions_used": ASSUMPTIONS_USED,
        "sources": _combine_sources(
            wue_result.get("sources", []),
            seasonal_result.get("sources", []),
            [kwh_result.get("source_url", "")],
        ),
        "details": {
            "base_wue_l_per_kwh": wue_result.get("wue_l_per_kwh"),
            "seasonal_factor": seasonal_result.get("factor"),
            "adjusted_wue_l_per_kwh": adjusted_wue,
            "kwh": kwh_result["kwh"],
            "wue_method": wue_result.get("method"),
            "seasonal_method": seasonal_result.get("method"),
        },
    }
    log_transformation("estimate_water_cost", "success", result)
    return result
