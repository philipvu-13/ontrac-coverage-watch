with map_rows as (
    select
        r.zip5,
        m.sort_center as origin_sort_center,
        m.transit_days,
        cast(null as varchar) as surcharge_tier,
        m.is_served,
        m.outcome as map_outcome,
        m.provenance,
        m.confidence,
        m.captured_on
    from {{ ref('stg_map_coverage') }} m
    join {{ ref('stg_zip_reference') }} r
      on r.state = m.state
    where m.captured_on = (select max(captured_on) from {{ ref('stg_map_coverage') }})
),

surcharge_rows as (
    select
        zip5,
        cast(null as varchar) as origin_sort_center,
        cast(null as number) as transit_days,
        tier as surcharge_tier,
        cast(null as boolean) as is_served,
        cast(null as varchar) as map_outcome,
        provenance,
        confidence,
        captured_on
    from {{ ref('stg_zip_surcharge') }}
    where captured_on = (select max(captured_on) from {{ ref('stg_zip_surcharge') }})
)

select * from map_rows
union all
select * from surcharge_rows