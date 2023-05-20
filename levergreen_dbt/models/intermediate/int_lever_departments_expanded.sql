with lever_jobs_outline as (
    select * from {{ ref('stg_lever__jobs_outline') }}
),

jobs_outline_unnested as (
    select
        lever_jobs_outline.id,
        lever_jobs_outline.levergreen_id,
        lever_jobs_outline.created_date_utc,
        lever_jobs_outline.updated_date_utc,
        lever_jobs_outline.source,
        lever_jobs_outline.uses_existing_html,
        lever_jobs_outline.raw_html_file_location,
        lever_jobs_outline.run_hash,
        lever_jobs_outline.location,
        lever_jobs_outline.full_opening_link, 
        lever_jobs_outline.opening_title,
        lever_jobs_outline.workplace_type = 'Remote' as is_remote,
        lever_jobs_outline.company_name,
        lever_jobs_outline.job_board,
        trim(department_ids_unnested.department_name) as department_name,
        department_ids_unnested.department_level
    from lever_jobs_outline, unnest(string_to_array(lever_jobs_outline.department_names, U&'\2013')) with ordinality as department_ids_unnested(department_name, department_level)
    --uses unicode character for dash from lever, different than normal dash. Normal: -, Lever: –.
),

{# select * from jobs_outline_unnested #}

departments_aggregated as (
    select 
        id,
        max(case when department_level = 1 then department_name end) as primary_department,
        max(case when department_level = 2 then department_name end) as secondary_department,
        max(case when department_level = 3 then department_name end) as tertiary_department
    from jobs_outline_unnested
    group by 1
)

{# departments_aggregated as (
    select 
        id,
        max(primary_department) as primary_department,
        max(secondary_department) as secondary_department,
        max(tertiary_department) as tertiary_department
    from outline_joined_to_depts
    group by 1
) #}

select distinct
    jobs_outline_unnested.id,
    jobs_outline_unnested.levergreen_id,
    jobs_outline_unnested.created_date_utc,
    jobs_outline_unnested.updated_date_utc,
    jobs_outline_unnested.source,
    jobs_outline_unnested.company_name,
    jobs_outline_unnested.uses_existing_html,
    jobs_outline_unnested.location,
    jobs_outline_unnested.full_opening_link, 
    jobs_outline_unnested.opening_title,
    jobs_outline_unnested.is_remote,
    departments_aggregated.primary_department,
    departments_aggregated.secondary_department,
    departments_aggregated.tertiary_department,
    jobs_outline_unnested.run_hash,
    jobs_outline_unnested.job_board
from jobs_outline_unnested
inner join departments_aggregated on jobs_outline_unnested.id = departments_aggregated.id