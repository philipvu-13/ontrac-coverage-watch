select
    captured_on,
    characters,
    provenance,
    confidence,
    source_key,
    alert_text
from {{ source('raw', 'service_alerts') }}