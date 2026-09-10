# DC Water Attribution Audit — Methodology (Phase 0)

## 1) Scope and objective

This project estimates **workload-level water usage** for AI compute in data centers using only publicly sourced evidence and explicit assumptions.

- Primary output unit: **liters of water per kWh (L/kWh)** and workload-attributed liters.
- Priority: traceability and credibility over coverage.
- Non-negotiable rule: if a number cannot be sourced, it remains `null` and is surfaced as **"no public data"**.

## 2) What WUE means and how it is disclosed

**Water Usage Effectiveness (WUE)** is typically expressed as:

`WUE = annual water consumed for cooling/humidification / annual IT energy (kWh)`

Common disclosure patterns:

1. **Corporate sustainability reports**: often provide annual fleet-level averages, sometimes regional or facility-level metrics.
2. **Local environmental permits**: may disclose withdrawal/discharge limits and operating constraints, but not always normalized WUE.
3. **Facility filings/impact statements**: can include cooling system type and water management details needed to interpret WUE values.

Important caveat: published WUE can vary by climate, cooling design, and accounting boundary (site-only vs upstream), so all derived outputs will include confidence labels and sample-size context.

## 3) What workload-level attribution requires

Workload-level attribution requires mapping workload energy demand to facility water intensity under seasonal and design constraints.

Minimum required inputs:

1. **Facility and capacity context**
   - IT capacity (MW) or proxy
   - Hardware/power profile assumptions for workload conversion (GPU-hours -> kWh)
2. **Cooling system characteristics**
   - Cooling type (evaporative, chilled water, hybrid, air-cooled where disclosed)
   - Water dependence implications per cooling type
3. **Regional climate profile**
   - Monthly temperature and humidity by facility region
   - Seasonal scaling factors for water intensity
4. **Disclosures and permits**
   - Disclosed WUE/PUE where available
   - Withdrawal/discharge bounds from permits where available
5. **Attribution model metadata**
   - Confidence tier (`high`/`low`)
   - Peer sample size (`N`)
   - Source URLs used in each estimate

## 4) Target facilities (required before Phase 1)

Please provide the 3 facilities in this format:

| Company | Facility name | Region |
|---|---|---|
| TBD | TBD | TBD |
| TBD | TBD | TBD |
| TBD | TBD | TBD |

Phase 1 depends on these values for schema population, climate pulls, and peer-group definitions.

## 5) Assumptions register (versioned)

All assumptions are versioned and auditable. Any change increments the methodology version and appends an entry in this table.

### Assumption set: `v0.1-draft` (current)

| Assumption ID | Statement | Rationale | Impact if wrong | Status |
|---|---|---|---|---|
| A-001 | If facility-level WUE is unavailable, use peer average from same climate bucket + cooling type. | Preserves comparability while avoiding invented values. | Attribution bias in sparse peer groups. | Draft |
| A-002 | Peer fallback must report sample size (`N`) and low confidence when `N < 3`. | Makes weak evidence explicit. | Overconfidence risk if omitted. | Draft |
| A-003 | Seasonal adjustment uses monthly temperature/humidity as linear modifiers to baseline WUE. | Transparent first-order correction with available public climate data. | Underfits nonlinear cooling behavior. | Draft |
| A-004 | Workload energy is computed from hardware TDP lookup and GPU-hours; lookup values require user confirmation before use. | Prevents hidden model assumptions for hardware power. | Energy estimate drift if TDP mismatched to real utilization. | Draft |
| A-005 | Any unsourced field remains `null` and is presented as "no public data". | Enforces no-hallucination policy. | Data sparsity increases but preserves integrity. | Draft |
| A-006 | Every input and derived table row must preserve at least one `source_url` lineage reference. | Enables auditability to original evidence. | Traceability breaks if lineage lost. | Draft |

## 6) Data quality and provenance policy

1. No fabricated values, permit IDs, or inferred citations.
2. `source_url` is mandatory in all relevant rows; rows without it fail validation.
3. Derived estimates must include:
   - confidence label
   - peer sample size (`N`)
   - assumptions used
   - contributing source URLs
4. Every transformation step is logged for reproducibility and backtracing.

## 7) Phase gate

**Stop condition:** Do not begin Phase 1 until:

1. You confirm this methodology, and
2. You provide the three target facilities (company, facility name, region), and
3. You confirm or adjust the initial assumptions in `v0.1-draft`.
