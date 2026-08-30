select
    captured_on,
    posted_date,
    event_type,
    cause,
    states,
    cities,
    summary,
    provenance,
    confidence,
    model,
    source_key
from {{ source('raw', 'service_alerts_parsed') }}