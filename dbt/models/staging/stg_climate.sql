select
    region::text as region,
    month::int as month,
    avg_temp_f::float as avg_temp_f,
    avg_humidity_pct::float as avg_humidity_pct,
    source_url::text as source_url
from {{ source('raw', 'climate') }}
