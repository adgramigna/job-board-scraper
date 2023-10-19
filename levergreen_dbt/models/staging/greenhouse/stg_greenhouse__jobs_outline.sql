with convert_unix_to_ts as (
    select 
        *,
        to_timestamp(created_at) at time zone 'UTC' as created_at_utc,
        to_timestamp(updated_at) at time zone 'UTC' as updated_at_utc
    from {{ source(
            'greenhouse',
            'greenhouse_jobs_outline'
        ) }}
    {# where updated_at > 1684600000 #}
),

convert_ts_to_date as (
    select
        *,
        date(created_at_utc) as created_date_utc,
        date(updated_at_utc) as updated_date_utc,
        row_number() over(
            partition by levergreen_id
            order by
                updated_at
        ) as earliest_levergreen_id_row
    from convert_unix_to_ts
),

greenhouse_outlines_by_levergreen_id as (
    select
        *,
        split_part(source,'.',2) as job_board,
        concat(source,'/',split_part(opening_link,'/',3),'/',split_part(opening_link,'/',4)) as full_opening_link,
        cast(existing_html_used as boolean) as uses_existing_html,
        row_number() over(
            partition by opening_link, updated_date_utc
            order by
                updated_at
        ) as earliest_opening_link_row
    from convert_ts_to_date
    where earliest_levergreen_id_row = 1
)

select
    concat(job_board,'_',id) as id,
    levergreen_id,
    created_at_utc,
    updated_at_utc,
    created_date_utc,
    updated_date_utc,
    source,
    uses_existing_html,
    raw_html_file_location,
    run_hash,
    department_ids,
    location,
    office_ids,
    full_opening_link,
    opening_title,
    job_board
from
    greenhouse_outlines_by_levergreen_id
where
    earliest_opening_link_row = 1
