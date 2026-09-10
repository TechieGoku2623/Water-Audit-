with facilities as (
    select * from {{ ref('stg_facilities') }}
),
latest_disclosures as (
    select
        d.facility_id,
        d.disclosure_year,
        d.wue_l_per_kwh,
        d.pue,
        d.source_url as disclosure_source_url
    from (
        select
            *,
            row_number() over (partition by facility_id order by disclosure_year desc) as rn
        from {{ ref('stg_disclosures') }}
    ) d
    where d.rn = 1
),
permit_rollup as (
    select
        p.facility_id,
        max(p.withdrawal_limit_gpd) as withdrawal_limit_gpd,
        max(p.discharge_limit_gpd) as discharge_limit_gpd,
        string_agg(distinct p.permit_id, ',') as permit_ids,
        string_agg(distinct p.issuing_agency, ',') as issuing_agencies,
        string_agg(distinct p.source_url, ',') as permit_source_url
    from {{ ref('stg_permits') }} p
    group by p.facility_id
),
climate as (
    select * from {{ ref('stg_climate') }}
)
select
    f.facility_id,
    f.company,
    f.facility_name,
    f.region,
    f.lat,
    f.lon,
    f.it_capacity_mw,
    f.cooling_type,
    c.month,
    c.avg_temp_f,
    c.avg_humidity_pct,
    d.disclosure_year,
    d.wue_l_per_kwh,
    d.pue,
    p.withdrawal_limit_gpd,
    p.discharge_limit_gpd,
    p.permit_ids,
    p.issuing_agencies,
    f.source_url as facility_source_url,
    d.disclosure_source_url,
    p.permit_source_url,
    c.source_url as climate_source_url,
    coalesce(
        d.disclosure_source_url,
        p.permit_source_url,
        c.source_url,
        f.source_url
    ) as source_url
from facilities f
left join latest_disclosures d on f.facility_id = d.facility_id
left join permit_rollup p on f.facility_id = p.facility_id
left join climate c on f.region = c.region
