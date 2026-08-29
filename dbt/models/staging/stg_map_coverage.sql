select
    sort_center,
    sort_center_state,
    map_index,
    state,
    outcome,
    case
        when outcome in ('unserved', 'no_data') then null
        else try_to_number(outcome)
    end as transit_days,
    outcome not in ('unserved', 'no_data') as is_served,
    split = 'yes' as is_split,
    points_total,
    points_agreeing,
    provenance,
    confidence,
    dt as captured_on,
    source_key,
    source_file
from {{ source('raw', 'map_coverage') }}