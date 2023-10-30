with jobs_outline as (
    select * from {{ ref('stg_ashby__jobs_outline') }}
),

job_locations_final as (
    select * from {{ ref('int_ashby_locations_expanded') }}
),

job_departments_final as (
    select * from {{ ref('int_ashby_departments_expanded') }}
)

select distinct
    jobs_outline.id,
    jobs_outline.levergreen_id,
    jobs_outline.created_date_utc,
    jobs_outline.updated_date_utc,
    jobs_outline.source,
    jobs_outline.company_name,
    jobs_outline.uses_existing,
    job_locations_final.location,
    jobs_outline.full_opening_link, 
    jobs_outline.opening_title,
    lower(job_locations_final.location) like '%remote%' as is_remote,
    job_departments_final.primary_department,
    job_departments_final.secondary_department,
    null as tertiary_department,
    null as quaternary_department,
    jobs_outline.run_hash,
    jobs_outline.job_board
from jobs_outline
inner join job_locations_final on jobs_outline.id = job_locations_final.id
inner join job_departments_final on jobs_outline.id = job_departments_final.id



