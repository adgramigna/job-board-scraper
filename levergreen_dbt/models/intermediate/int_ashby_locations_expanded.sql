with job_locations as (
    select * from {{ ref('stg_ashby__job_locations') }}
),

jobs_outline as (
    select * from {{ ref('stg_ashby__jobs_outline') }}
),

all_secondary_locations as (
    select opening_id, run_hash, string_agg(secondary_location_name, ', ') as secondary_locations from job_locations
    group by 1,2
)

select
    jobs_outline.id,
    jobs_outline.opening_id,
    case 
        when all_secondary_locations.secondary_locations is null
            then jobs_outline.location_name
        else concat(jobs_outline.location_name, ', ', all_secondary_locations.secondary_locations) 
    end as location
from jobs_outline
left join all_secondary_locations on jobs_outline.opening_id = all_secondary_locations.opening_id
and jobs_outline.run_hash = all_secondary_locations.run_hash