select
    zip5,
    origin_sort_center,
    provenance,
    count(*) as rows_found
from {{ ref('fct_zip_coverage') }}
group by 1, 2, 3
having count(*) > 1