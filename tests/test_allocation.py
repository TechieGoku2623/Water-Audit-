from __future__ import annotations

import math

import pandas as pd
import pytest

from model.allocation import (
    DataBundle,
    estimate_water_cost,
    facility_wue,
    seasonal_adjustment,
    workload_kwh,
)


def _bundle() -> DataBundle:
    facilities = pd.DataFrame(
        [
            {
                "facility_id": "f1",
                "company": "alpha",
                "name": "alpha-1",
                "region": "r1",
                "lat": 0.0,
                "lon": 0.0,
                "it_capacity_mw": 10.0,
                "cooling_type": "evaporative",
                "source_url": "https://example.com/f1",
            },
            {
                "facility_id": "f2",
                "company": "beta",
                "name": "beta-1",
                "region": "r1",
                "lat": 0.0,
                "lon": 0.0,
                "it_capacity_mw": 8.0,
                "cooling_type": "evaporative",
                "source_url": "https://example.com/f2",
            },
            {
                "facility_id": "f3",
                "company": "gamma",
                "name": "gamma-1",
                "region": "r1",
                "lat": 0.0,
                "lon": 0.0,
                "it_capacity_mw": 9.0,
                "cooling_type": "evaporative",
                "source_url": "https://example.com/f3",
            },
            {
                "facility_id": "f4",
                "company": "delta",
                "name": "delta-1",
                "region": "r2",
                "lat": 0.0,
                "lon": 0.0,
                "it_capacity_mw": 7.0,
                "cooling_type": "air",
                "source_url": "https://example.com/f4",
            },
        ]
    )
    disclosures = pd.DataFrame(
        [
            {
                "facility_id": "f1",
                "year": 2024,
                "wue_l_per_kwh": 1.0,
                "pue": 1.2,
                "source_url": "https://example.com/d1",
            },
            {
                "facility_id": "f2",
                "year": 2024,
                "wue_l_per_kwh": 1.2,
                "pue": 1.3,
                "source_url": "https://example.com/d2",
            },
            {
                "facility_id": "f4",
                "year": 2024,
                "wue_l_per_kwh": 0.6,
                "pue": 1.1,
                "source_url": "https://example.com/d4",
            },
        ]
    )
    climate = pd.DataFrame(
        [
            {
                "region": "r1",
                "month": 1,
                "avg_temp_f": 50.0,
                "avg_humidity_pct": 40.0,
                "source_url": "https://noaa.example/r1",
            },
            {
                "region": "r1",
                "month": 7,
                "avg_temp_f": 70.0,
                "avg_humidity_pct": 60.0,
                "source_url": "https://noaa.example/r1",
            },
            {
                "region": "r2",
                "month": 1,
                "avg_temp_f": 80.0,
                "avg_humidity_pct": 55.0,
                "source_url": "https://noaa.example/r2",
            },
            {
                "region": "r2",
                "month": 7,
                "avg_temp_f": 90.0,
                "avg_humidity_pct": 70.0,
                "source_url": "https://noaa.example/r2",
            },
        ]
    )
    return DataBundle(facilities=facilities, disclosures=disclosures, climate=climate)


def test_facility_wue_prefers_direct_disclosure() -> None:
    result = facility_wue("f1", data=_bundle())
    assert result["method"] == "direct_disclosure"
    assert result["confidence"] == "high"
    assert result["sample_size"] == 1
    assert result["wue_l_per_kwh"] == 1.0


def test_facility_wue_fallback_to_peers_and_downgrades_confidence() -> None:
    result = facility_wue("f3", data=_bundle())
    assert result["method"] == "peer_climate_cooling_fallback"
    assert result["confidence"] == "low"
    assert result["sample_size"] == 2
    assert pytest.approx(result["wue_l_per_kwh"], rel=1e-9) == 1.1
    assert result["interval_u"] > result["wue_l_per_kwh"]
    assert result["interval_l"] < result["wue_l_per_kwh"]


def test_facility_wue_returns_no_public_data_when_no_peers() -> None:
    bundle = _bundle()
    bundle.facilities = bundle.facilities[bundle.facilities["facility_id"].isin(["f4"])]
    result = facility_wue("f4", data=bundle)
    assert result["method"] == "no_public_data"
    assert result["wue_l_per_kwh"] is None
    assert result["sample_size"] == 0


def test_workload_kwh_uses_tdp_lookup() -> None:
    result = workload_kwh(gpu_hours=100, hardware_type="H100")
    assert result["kwh"] == 70.0
    assert result["tdp_watts"] == 700.0
    assert result["source_url"].startswith("https://")


def test_workload_kwh_rejects_unknown_hardware() -> None:
    with pytest.raises(ValueError):
        workload_kwh(gpu_hours=100, hardware_type="unknown-gpu")


def test_seasonal_adjustment_linear_factor_math() -> None:
    result = seasonal_adjustment(wue=1.0, region="r1", month=7, data=_bundle())
    # Annual averages for r1 in fixture are temp=60, humidity=50; month 7 is 70/60.
    # factor = 1 + (0.003*10) + (0.001*10) = 1.04
    assert pytest.approx(result["factor"], rel=1e-9) == 1.04
    assert pytest.approx(result["adjusted_wue_l_per_kwh"], rel=1e-9) == 1.04


def test_seasonal_adjustment_graceful_when_month_missing() -> None:
    result = seasonal_adjustment(wue=1.2, region="r1", month=12, data=_bundle())
    assert result["method"] == "climate_data_missing"
    assert result["factor"] == 1.0
    assert result["adjusted_wue_l_per_kwh"] == 1.2


def test_estimate_water_cost_direct_path_high_confidence() -> None:
    result = estimate_water_cost(
        {
            "facility_id": "f1",
            "region": "r1",
            "hardware_type": "h100",
            "gpu_hours": 100,
            "month": 7,
        },
        data=_bundle(),
    )
    assert result["confidence"] == "high"
    assert result["sample_size"] == 1
    assert pytest.approx(result["estimate_liters"], rel=1e-9) == 72.8


def test_estimate_water_cost_regional_path_low_signal_when_sample_small() -> None:
    result = estimate_water_cost(
        {
            "region": "r2",
            "hardware_type": "a100",
            "gpu_hours": 100,
            "month": 7,
        },
        data=_bundle(),
    )
    assert result["confidence"] == "low"
    assert result["sample_size"] == 1
    assert result["estimate_liters"] is not None
    assert not math.isnan(result["estimate_liters"])
