with greenhouse_outlines_by_levergreen_id as (
    select
        *,
        to_timestamp(created_at) at time zone 'UTC' as created_at_utc,
        to_timestamp(updated_at) at time zone 'UTC' as updated_at_utc,
        concat(source,'/',split_part(opening_link,'/',3),'/',split_part(opening_link,'/',4)) as full_opening_link,
        cast(cast(existing_html_used as int) as boolean) as uses_existing_html, 
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
    where updated_at > 1684294508
)

select
    id,
    levergreen_id,
    created_at_utc,
    updated_at_utc,
    source,
    uses_existing_html,
    raw_html_file_location,
    run_hash,
    department_ids,
    location,
    office_ids,
    full_opening_link,
    opening_title
    --TODO:
    --is_active
    --days_active
from
    greenhouse_outlines_by_levergreen_id
where
    earliest_levergreen_id_row = 1
