select 
    'rippling_' || id as id,
    job_id as levergreen_id,
    date(created_at) as created_date_utc,
    date(created_at) as updated_date_utc,
    api_endpoint as source,
    board_token as company_name,
    false as uses_existing,
    location,
    url as full_opening_link, 
    title as opening_title,
    lower(location) like '%remote%' as is_remote,
    department as primary_department,
    null as secondary_department,
    null as tertiary_department,
    null as quaternary_department,
    run_hash,
    'rippling' as job_board_provider
from {{ source('rippling', 'rippling_jobs_outline') }}