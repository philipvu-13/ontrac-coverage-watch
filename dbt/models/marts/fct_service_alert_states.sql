select
    alerts.captured_on,
    alerts.posted_date,
    alerts.event_type,
    alerts.cause,
    trim(state.value) as state,
    alerts.cities,
    alerts.summary,
    alerts.provenance,
    alerts.confidence,
    alerts.model
from {{ ref('stg_service_alerts_parsed') }} alerts,
lateral flatten(input => split(alerts.states, '|')) state
where trim(state.value) <> ''