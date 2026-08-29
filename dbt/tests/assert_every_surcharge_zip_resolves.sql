select s.zip5
from {{ ref('stg_zip_surcharge') }} s
left join {{ ref('stg_zip_reference') }} r
  on r.zip5 = s.zip5
where r.zip5 is null