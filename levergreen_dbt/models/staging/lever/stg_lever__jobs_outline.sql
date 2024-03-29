with convert_unix_to_ts as (
    select 
        *,
        to_timestamp(created_at) at time zone 'UTC' as created_at_utc,
        to_timestamp(updated_at) at time zone 'UTC' as updated_at_utc
    from {{ source(
            'lever',
            'lever_jobs_outline'
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

lever_outlines_by_levergreen_id as (
    select
        *,
        split_part(source,'.',2) as job_board,
        cast(existing_html_used as boolean) as uses_existing, 
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
    uses_existing,
    raw_html_file_location, 
    run_hash,
    department_names,
    location,
    workplace_type,
    opening_link as full_opening_link,
    opening_title,
    company_name,
    job_board
from
    lever_outlines_by_levergreen_id
where
    earliest_opening_link_row = 1
