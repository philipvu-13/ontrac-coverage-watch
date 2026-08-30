with surcharge as (
    select
        captured_on,
        compared_to,
        'area_surcharge_pdf' as source,
        'confirmed' as confidence,
        count_if(change_type = 'added') as added,
        count_if(change_type = 'removed') as removed,
        count_if(change_type = 'tier_changed') as changed,
        count(*) as total_changes
    from {{ ref('fct_zip_surcharge_changes') }}
    group by 1, 2, 3, 4
),

maps as (
    select
        captured_on,
        compared_to,
        'coverage_map_png' as source,
        'inferred' as confidence,
        count_if(change_type = 'origin_added') as added,
        count_if(change_type = 'origin_removed') as removed,
        count_if(change_type = 'outcome_changed') as changed,
        count(*) as total_changes
    from {{ ref('fct_map_coverage_changes') }}
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