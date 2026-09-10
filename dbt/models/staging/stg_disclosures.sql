select
    facility_id::text as facility_id,
    year::int as disclosure_year,
    wue_l_per_kwh::float as wue_l_per_kwh,
    pue::float as pue,
    source_url::text as source_url
from {{ source('raw', 'disclosures') }}
