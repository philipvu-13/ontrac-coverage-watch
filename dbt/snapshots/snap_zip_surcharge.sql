{% snapshot snap_zip_surcharge %}

{{
    config(
        target_schema='snapshots',
        unique_key='zip5',
        strategy='check',
        check_cols=['tier'],
        hard_deletes='invalidate',
    )
}}

select
    zip5,
    tier,
    effective_date,
    captured_on
from {{ ref('stg_zip_surcharge') }}
where captured_on = (select max(captured_on) from {{ ref('stg_zip_surcharge') }})

{% endsnapshot %}