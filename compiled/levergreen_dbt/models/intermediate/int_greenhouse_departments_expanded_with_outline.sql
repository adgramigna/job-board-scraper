with greenhouse_jobs_outline as (
    select * from "postgres"."public"."stg_greenhouse__jobs_outline"
),

greenhouse_job_departments as (
    select * from "postgres"."public"."stg_greenhouse__job_departments"
),

jobs_outline_unnested as (
    select
        greenhouse_jobs_outline.id,
        greenhouse_jobs_outline.levergreen_id,
        greenhouse_jobs_outline.created_date_utc,
        greenhouse_jobs_outline.updated_date_utc,
        greenhouse_jobs_outline.source,
        greenhouse_jobs_outline.uses_existing_html,
        greenhouse_jobs_outline.raw_html_file_location,
        greenhouse_jobs_outline.run_hash,
        greenhouse_jobs_outline.location,
        greenhouse_jobs_outline.office_ids,
        greenhouse_jobs_outline.full_opening_link, 
        greenhouse_jobs_outline.opening_title,
        greenhouse_jobs_outline.job_board,
        lower(greenhouse_jobs_outline.location) like '%remote%' as is_remote,
        department_ids_unnested.department_id
    from greenhouse_jobs_outline, unnest(string_to_array(department_ids, ',')) as department_ids_unnested(department_id)
),

outline_joined_to_depts as (
    select 
        jobs_outline_unnested.*,
        greenhouse_job_departments.company_name,
        case when greenhouse_job_departments.department_category = 'level-0' then greenhouse_job_departments.department_name end as primary_department,
        case when greenhouse_job_departments.department_category = 'level-1' then greenhouse_job_departments.department_name end as secondary_department,
        case when greenhouse_job_departments.department_category = 'level-2' then greenhouse_job_departments.department_name end as tertiary_department
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
    outline_joined_to_depts.created_date_utc,
    outline_joined_to_depts.updated_date_utc,
    outline_joined_to_depts.source,
    outline_joined_to_depts.company_name,
    outline_joined_to_depts.uses_existing_html,
    outline_joined_to_depts.location,
    outline_joined_to_depts.full_opening_link, 
    outline_joined_to_depts.opening_title,
    outline_joined_to_depts.is_remote,
    departments_aggregated.primary_department,
    departments_aggregated.secondary_department,
    departments_aggregated.tertiary_department,
    outline_joined_to_depts.run_hash,
    outline_joined_to_depts.job_board
from outline_joined_to_depts
inner join departments_aggregated on outline_joined_to_depts.id = departments_aggregated.id