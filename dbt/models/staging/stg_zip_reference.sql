select
    zip5,
    state,
    state_name,
    place,
    state is null
        and (place like 'APO%' or place like 'FPO%' or place like 'DPO%')
        as is_military,
    dt as captured_on,
    source_file
from {{ source('raw', 'zip_reference') }}