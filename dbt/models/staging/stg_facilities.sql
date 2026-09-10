select
    facility_id::text as facility_id,
    company::text as company,
    name::text as facility_name,
    region::text as region,
    lat::float as lat,
    lon::float as lon,
    it_capacity_mw::float as it_capacity_mw,
    cooling_type::text as cooling_type,
    source_url::text as source_url
from {{ source('raw', 'facilities') }}
