select
    zip5,
    state,
    state_name,
    place,
    dt as captured_on,
    source_file
from {{ source('raw', 'zip_reference') }}