select
    *
from
    {{ ref('all_job_postings') }}
where
    is_active
