with greenhouse_departments_by_levergreen_id as (
    select
        *,
        to_timestamp(created_at) at time zone 'UTC' as created_at_utc,
        to_timestamp(updated_at) at time zone 'UTC' as updated_at_utc,
        cast(cast(existing_html_used as int) as boolean) as uses_existing_html, 
        row_number() over(
            partition by levergreen_id
            order by
                updated_at
        ) as earliest_levergreen_id_row
    from
        {{ source(
            'greenhouse',
            'greenhouse_job_departments'
        ) }}
    where updated_at > 1684600000
)
select
    id,
    levergreen_id,
    created_at_utc,
    updated_at_utc,
    DATE(created_at_utc) as created_date_utc,
    DATE(updated_at_utc) as updated_date_utc,
    source,
    uses_existing_html,
    raw_html_file_location,
    run_hash,
    company_name,
    department_id,
    department_category,
    department_name,
    split_part(source,'.',2) as job_board
from
    greenhouse_departments_by_levergreen_id
where
    earliest_levergreen_id_row = 1
