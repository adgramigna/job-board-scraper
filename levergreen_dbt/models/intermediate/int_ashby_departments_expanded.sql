with job_departments as (
    select 
        department_id,
        department_name,
        parent_department_id, 
        row_number() over(partition by department_id order by updated_at_utc desc) as rn
    from {{ ref('stg_ashby__job_departments') }}
),

{# Need this CTE because of Ashby updating dept names but keeping id. Example id 2442 and 2175 #}
job_departments_dedup as (
    select * from job_departments where rn = 1
),

jobs_outline as (
    select id, opening_id, department_id from {{ ref('stg_ashby__jobs_outline') }}
),

job_departments_joined as (
    select
    jobs_outline.id,
    jobs_outline.opening_id, 
    coalesce(parent_department.department_name, posting_department.department_name) as primary_department,
    case when parent_department.department_name is not null then posting_department.department_name end as secondary_department 
    from jobs_outline
    left join job_departments_dedup posting_department on jobs_outline.department_id = posting_department.department_id
    left join job_departments_dedup parent_department on posting_department.parent_department_id = parent_department.department_id
)

select * from job_departments_joined