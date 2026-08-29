select
    zip5,
    tier,
    effective_date,
    page as source_page,
    provenance,
    confidence,
    dt as captured_on,
    source_file
from {{ source('raw', 'zip_surcharge') }}