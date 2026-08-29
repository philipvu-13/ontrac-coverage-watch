with captures as (
    select distinct captured_on
    from {{ ref('stg_zip_surcharge') }}
),

pairs as (
    select
        captured_on,
        lag(captured_on) over (order by captured_on) as compared_to
    from captures
    qualify compared_to is not null
),

current_rows as (
    select
        p.captured_on,
        p.compared_to,
        s.zip5,
        s.tier
    from pairs p
    join {{ ref('stg_zip_surcharge') }} s
      on s.captured_on = p.captured_on
),

previous_rows as (
    select
        p.captured_on,
        p.compared_to,
        s.zip5,
        s.tier
    from pairs p
    join {{ ref('stg_zip_surcharge') }} s
      on s.captured_on = p.compared_to
),

joined as (
    select
        coalesce(c.captured_on, p.captured_on) as captured_on,
        coalesce(c.compared_to, p.compared_to) as compared_to,
        coalesce(c.zip5, p.zip5) as zip5,
        p.tier as previous_tier,
        c.tier as current_tier
    from current_rows c
    full outer join previous_rows p
      on c.zip5 = p.zip5
     and c.captured_on = p.captured_on
)

select
    captured_on,
    compared_to,
    zip5,
    previous_tier,
    current_tier,
    case
        when previous_tier is null then 'added'
        when current_tier is null then 'removed'
        else 'tier_changed'
    end as change_type,
    'area_surcharge_pdf' as provenance,
    'confirmed' as confidence
from joined
where previous_tier is null
   or current_tier is null
   or previous_tier <> current_tier