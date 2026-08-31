with surcharge_captures as (
    select distinct captured_on from {{ ref('stg_zip_surcharge') }}
),

surcharge_pairs as (
    select
        captured_on,
        lag(captured_on) over (order by captured_on) as compared_to
    from surcharge_captures
    qualify compared_to is not null
),

surcharge as (
    select
        pairs.captured_on,
        pairs.compared_to,
        'area_surcharge_pdf' as source,
        'confirmed' as confidence,
        count_if(changes.change_type = 'added') as added,
        count_if(changes.change_type = 'removed') as removed,
        count_if(changes.change_type = 'tier_changed') as changed,
        count(changes.zip5) as total_changes
    from surcharge_pairs pairs
    left join {{ ref('fct_zip_surcharge_changes') }} changes
      on changes.captured_on = pairs.captured_on
     and changes.compared_to = pairs.compared_to
    group by 1, 2, 3, 4
),

map_captures as (
    select distinct captured_on from {{ ref('stg_map_coverage') }}
),

map_pairs as (
    select
        captured_on,
        lag(captured_on) over (order by captured_on) as compared_to
    from map_captures
    qualify compared_to is not null
),

maps as (
    select
        pairs.captured_on,
        pairs.compared_to,
        'coverage_map_png' as source,
        'inferred' as confidence,
        count_if(changes.change_type = 'origin_added') as added,
        count_if(changes.change_type = 'origin_removed') as removed,
        count_if(changes.change_type = 'outcome_changed') as changed,
        count(changes.state) as total_changes
    from map_pairs pairs
    left join {{ ref('fct_map_coverage_changes') }} changes
      on changes.captured_on = pairs.captured_on
     and changes.compared_to = pairs.compared_to
    group by 1, 2, 3, 4
),

combined as (
    select * from surcharge
    union all
    select * from maps
)

select
    captured_on,
    compared_to,
    source,
    confidence,
    added,
    removed,
    changed,
    total_changes,
    case
        when source = 'area_surcharge_pdf'
            then 'Surcharge listing. '
                 || added || ' ZIP codes added, '
                 || removed || ' removed, and '
                 || changed || ' moved between the standard and extended bands.'
        else 'Coverage maps. '
             || changed || ' state and origin combinations changed transit outcome, '
             || added || ' appeared and '
             || removed || ' disappeared.'
    end as summary
from combined