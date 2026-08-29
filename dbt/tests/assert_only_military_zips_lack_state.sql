select zip5, place
from {{ ref('stg_zip_reference') }}
where state is null
  and place not like 'APO%'
  and place not like 'FPO%'
  and place not like 'DPO%'