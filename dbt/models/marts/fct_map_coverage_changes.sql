with captures as (
    select distinct captured_on
    from {{ ref('stg_map_coverage') }}
),

pairs as (
    select
        captured_on,
        lag(captured_on) over (order by captured_on) as compared_to
    from captures
    qualify compared_to is not null
),

current_rows as (
    select p.captured_on, p.compared_to, m.sort_center, m.state, m.outcome, m.confidence
    from pairs p
    join {{ ref('stg_map_coverage') }} m on m.captured_on = p.captured_on
),

previous_rows as (
    select p.captured_on, p.compared_to, m.sort_center, m.state, m.outcome, m.confidence
    from pairs p
    join {{ ref('stg_map_coverage') }} m on m.captured_on = p.compared_to
),

joined as (
    select
        coalesce(c.captured_on, p.captured_on) as captured_on,
        coalesce(c.compared_to, p.compared_to) as compared_to,
        coalesce(c.sort_center, p.sort_center) as sort_center,
        coalesce(c.state, p.state) as state,
        p.outcome as previous_outcome,
        c.outcome as current_outcome,
        coalesce(c.confidence, p.confidence) as confidence
    from current_rows c
    full outer join previous_rows p
      on c.sort_center = p.sort_center
     and c.state = p.state
     and c.captured_on = p.captured_on
)

select
    captured_on,
    compared_to,
    sort_center,
    state,
    previous_outcome,
    current_outcome,
    case
        when previous_outcome is null then 'origin_added'
        when current_outcome is null then 'origin_removed'
        else 'outcome_changed'
    end as change_type,
    'coverage_map_png' as provenance,
    confidence
from joined
where previous_outcome is distinct from current_outcome