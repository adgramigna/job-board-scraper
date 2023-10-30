with job_departments as (
    select * from {{ ref('stg_ashby__job_departments') }}
),

jobs_outline as (
    select * from {{ ref('stg_ashby__jobs_outline') }}
),

job_departments_joined as (
    select
    jobs_outline.id,
    jobs_outline.opening_id, 
    coalesce(parent_department.department_name, posting_department.department_name) as primary_department,
    case when parent_department.department_name is not null then posting_department.department_name end as secondary_department 
    from jobs_outline
    left join job_departments posting_department on jobs_outline.department_id = posting_department.department_id
    left join job_departments parent_department on posting_department.parent_department_id = parent_department.department_id
)

select * from job_departments_joined