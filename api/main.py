from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model.allocation import estimate_water_cost, load_default_data


app = FastAPI(title="DC Water Attribution Audit API", version="0.1.0")


class EstimateRequest(BaseModel):
    region: str = Field(..., min_length=1)
    hardware_type: str = Field(..., min_length=1)
    gpu_hours: float = Field(..., gt=0)
    month: int = Field(..., ge=1, le=12)
    facility_id: str | None = None


@app.post("/estimate")
def post_estimate(payload: EstimateRequest) -> dict[str, Any]:
    try:
        result = estimate_water_cost(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@app.get("/facilities")
def get_facilities() -> list[dict[str, Any]]:
    data = load_default_data()
    facilities = data.facilities.copy()
    disclosures = data.disclosures.copy()
    if not facilities.empty and not disclosures.empty:
        disclosures["year"] = pd.to_numeric(disclosures["year"], errors="coerce")
        disclosures = disclosures.sort_values("year", ascending=False)
        latest_disclosures = disclosures.groupby("facility_id", as_index=False).first()
        facilities = facilities.merge(
            latest_disclosures[["facility_id", "year", "wue_l_per_kwh", "pue", "source_url"]],
            how="left",
            on="facility_id",
            suffixes=("", "_disclosure"),
        )
    else:
        facilities["year"] = pd.NA
        facilities["wue_l_per_kwh"] = pd.NA
        facilities["pue"] = pd.NA
        facilities["source_url_disclosure"] = pd.NA

    output: list[dict[str, Any]] = []
    for _, row in facilities.iterrows():
        output.append(
            {
                "facility_id": row.get("facility_id"),
                "company": row.get("company"),
                "name": row.get("name"),
                "region": row.get("region"),
                "cooling_type": row.get("cooling_type"),
                "it_capacity_mw": row.get("it_capacity_mw"),
                "disclosure_year": row.get("year"),
                "wue_l_per_kwh": row.get("wue_l_per_kwh"),
                "pue": row.get("pue"),
                "facility_source_url": row.get("source_url"),
                "disclosure_source_url": row.get("source_url_disclosure"),
            }
        )
    return output
