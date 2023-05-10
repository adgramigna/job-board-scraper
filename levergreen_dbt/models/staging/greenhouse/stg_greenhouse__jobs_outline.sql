with greenhouse_outlines_by_levergreen_id as (
    select
        *,
        row_number() over(
            partition by levergreen_id
            order by
                updated_at
        ) as earliest_levergreen_id_row
    from
        {{ source(
            'greenhouse',
            'greenhouse_jobs_outline'
        ) }}
)

select
    id,
    levergreen_id,
    to_timestamp(created_at) at time zone 'UTC' as created_at_utc,
    to_timestamp(updated_at) at time zone 'UTC' as updated_at_utc,
    source,
    department_ids,
    location,
    office_ids,
    opening_link, 
    opening_title
from
    greenhouse_outlines_by_levergreen_id
where
    earliest_levergreen_id_row = 1
