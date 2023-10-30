with ashby_departments_by_levergreen_id as (
    select
        *,
        to_timestamp(created_at) at time zone 'UTC' as created_at_utc,
        to_timestamp(updated_at) at time zone 'UTC' as updated_at_utc,
        cast(existing_json_used as boolean) as uses_existing, 
        row_number() over(
            partition by levergreen_id
            order by
                updated_at
        ) as earliest_levergreen_id_row
    from
        {{ source(
            'ashby',
            'ashby_job_departments'
        ) }}
)
select
    id,
    levergreen_id,
    created_at_utc,
    updated_at_utc,
    DATE(created_at_utc) as created_date_utc,
    DATE(updated_at_utc) as updated_date_utc,
    ashby_job_board_source as source,
    uses_existing,
    raw_json_file_location,
    run_hash,
    company_name,
    department_id,
    department_name,
    parent_department_id,
    'ashby' as job_board
from
    ashby_departments_by_levergreen_id
where
    earliest_levergreen_id_row = 1
