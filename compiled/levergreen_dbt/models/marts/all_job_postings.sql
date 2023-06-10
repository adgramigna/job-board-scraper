with  __dbt__cte__int_greenhouse_departments_expanded_with_outline as (
with greenhouse_jobs_outline as (
    select * from "postgres"."public"."stg_greenhouse__jobs_outline"
),

greenhouse_job_departments as (
    select * from "postgres"."public"."stg_greenhouse__job_departments"
),

    --TODO:
    --is_active
    --days_active

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
),  __dbt__cte__int_lever_departments_expanded as (
with lever_jobs_outline as (
    select * from "postgres"."public"."stg_lever__jobs_outline"
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



departments_aggregated as (
    select 
        id,
        max(case when department_level = 1 then department_name end) as primary_department,
        max(case when department_level = 2 then department_name end) as secondary_department,
        max(case when department_level = 3 then department_name end) as tertiary_department
    from jobs_outline_unnested
    group by 1
)



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
),all_postings as (
    select * from __dbt__cte__int_greenhouse_departments_expanded_with_outline
    union all
    select * from __dbt__cte__int_lever_departments_expanded
),

get_earliest_and_latest_dates as (
    select
        full_opening_link,
        min(created_date_utc) as earliest_opening_date,
        max(created_date_utc) as latest_opening_date
    from all_postings
    group by 1
),

all_postings_with_earliest_and_latest as (
    select 
        all_postings.*, 
        date(timezone('utc', '2023-06-08')) = all_postings.created_date_utc as is_active,
        earliest_and_latest.earliest_opening_date,
        earliest_and_latest.latest_opening_date,
        earliest_and_latest.latest_opening_date - earliest_and_latest.earliest_opening_date + 1 as days_active
    from all_postings
    inner join get_earliest_and_latest_dates as earliest_and_latest on all_postings.full_opening_link = earliest_and_latest.full_opening_link
)

select *,
    case
        when not is_active then 'Inactive'
        when days_active > 90 then 'Stale'
        when days_active > 60 then 'Old'
        when days_active > 30 then 'Medium'
        when days_active > 7  then 'Recent'
    else 'New'
    end as posting_length_category,
    case
        when lower(primary_department) like '%data%' 
            or lower(primary_department) like '%analytics%'
            or lower(secondary_department) like '%data%' 
            or lower(secondary_department) like '%analytics%'
            or lower(opening_title) like '%data%' 
            or lower(opening_title) like '%analytics%'
            then 'Data'
        when lower(primary_department) like '%engineer%' 
            or lower(secondary_department) like '%engineer%' 
            or lower(opening_title) like '%engineer%' 
            then 'Software Engineering'
        when lower(primary_department) like '%sales%' 
            or lower(secondary_department) like '%sales%' 
            or lower(opening_title) like '%sales%' 
            or lower(opening_title) like '%account executive'
            then 'Sales'
        when lower(primary_department) like '%finance%' 
            or lower(primary_department) like '%accounting%' 
            or lower(secondary_department) like '%finance%' 
            or lower(secondary_department) like '%accounting%' 
            or lower(opening_title) like '%finance%'
            or lower(opening_title) like '%accounting%' 
            then 'Finance & Accounting'
        when lower(primary_department) like '%operations%' 
            or lower(secondary_department) like '%operations%' 
            or lower(opening_title) like '%operations%' 
            then 'Operations'
        when lower(primary_department) like '%product%' 
            or lower(secondary_department) like '%product%' 
            or lower(opening_title) like '%product%'
            then 'Product'
        else 'Other'
    end as opening_category
from all_postings_with_earliest_and_latest