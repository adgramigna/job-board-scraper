with greenhouse_jobs_outline as (
    select * from {{ ref('stg_greenhouse__jobs_outline') }}
),

greenhouse_job_departments as (
    select * from {{ ref('stg_greenhouse__job_departments') }}
),

    --TODO:
    --is_active
    --days_active

jobs_outline_unnested as (
    select
        id,
        levergreen_id,
        DATE(created_at_utc) as created_at_date,
        DATE(updated_at_utc) as updated_at_date,
        source,
        uses_existing_html,
        raw_html_file_location,
        run_hash,
        unnest(string_to_array(department_ids, ',')) as department_id,
        location,
        office_ids,
        full_opening_link, 
        opening_title    
    from greenhouse_jobs_outline
),

outline_joined_to_depts as (
    select 
        jobs_outline_unnested.*,
        case when department_category = 'level-0' then department_name end as primary_department,
        case when department_category = 'level-1' then department_name end as secondary_department,
        case when department_category = 'level-2' then department_name end as tertiary_department
    from jobs_outline_unnested
    left join greenhouse_job_departments on jobs_outline_unnested.source = greenhouse_job_departments.source
        and jobs_outline_unnested.department_id = greenhouse_job_departments.department_id
        and jobs_outline_unnested.run_hash = greenhouse_job_departments.run_hash
),

departments_aggregated as (
    select 
        id,
        max(primary_department) as primary_department,
        max(secondary_department) as secondary_department,
        max(tertiary_department) as tertiary_department
    from outline_joined_to_depts
    group by 1
)

select distinct
    outline_joined_to_depts.id,
    outline_joined_to_depts.levergreen_id,
    outline_joined_to_depts.created_at_date,
    outline_joined_to_depts.updated_at_date,
    outline_joined_to_depts.source,
    outline_joined_to_depts.uses_existing_html,
    outline_joined_to_depts.location,
    outline_joined_to_depts.office_ids,
    outline_joined_to_depts.full_opening_link, 
    outline_joined_to_depts.opening_title,
    departments_aggregated.primary_department,
    departments_aggregated.secondary_department,
    departments_aggregated.tertiary_department
from outline_joined_to_depts
inner join departments_aggregated on outline_joined_to_depts.id = departments_aggregated.id