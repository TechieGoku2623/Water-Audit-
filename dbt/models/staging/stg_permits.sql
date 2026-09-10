select
    facility_id::text as facility_id,
    permit_id::text as permit_id,
    withdrawal_limit_gpd::float as withdrawal_limit_gpd,
    discharge_limit_gpd::float as discharge_limit_gpd,
    issuing_agency::text as issuing_agency,
    source_url::text as source_url
from {{ source('raw', 'permits') }}
