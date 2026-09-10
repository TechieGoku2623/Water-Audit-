# DC Water Attribution Audit — Summary for Writeup

## What this project does

This project estimates AI workload water usage using public evidence only. It converts
workload energy demand (GPU-hours) into estimated water use by combining:

- disclosed water efficiency data (WUE) when available,
- permit and facility context,
- regional monthly climate conditions,
- and a transparent fallback method when direct disclosure is missing.

## Method used

1. **Collect and stage source-backed inputs**
   - Facilities
   - Disclosures (WUE/PUE)
   - Permits
   - NOAA climate data (monthly temperature and humidity)
2. **Validate provenance**
   - Every row must include `source_url`
   - Any missing source fails validation
3. **Build cleaned model**
   - dbt joins the staged tables into `facility_water_profile`
   - Source lineage is preserved through transformation
4. **Estimate workload water usage**
   - Convert GPU-hours to kWh from hardware TDP references
   - Use direct facility WUE when disclosed
   - Otherwise use peer fallback (same climate bucket + cooling type) with downgraded confidence
   - Apply monthly climate adjustment
   - Return estimate with confidence, sample size, assumptions, and source URLs

## Current findings status

- The pipeline and model are implemented.
- Source validation currently passes.
- Unit tests currently pass.
- No facility-specific public rows have been added yet in this repository snapshot, so
  there are no numeric facility findings to publish yet.

## Confidence policy used in outputs

- **High confidence**: direct disclosed WUE plus available seasonal climate inputs.
- **Low confidence**: fallback WUE, sparse peer sample sizes, or missing climate detail.
- All estimated outputs include sample size (`N`) and assumptions used.

## Publication-safe statement at this stage

This artifact is ready for source-backed data entry and reproducible estimation, but
any public claims should wait until real facility disclosures/permits/climate records
are populated and cited in the staged datasets.
