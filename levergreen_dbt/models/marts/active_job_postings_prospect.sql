select
    active_job_postings.*
from
    {{ ref('active_job_postings') }}
    active_job_postings
    inner join {{ source(
        'levergreen',
        'job_board_urls'
    ) }}
    job_board_urls
    on active_job_postings.source = job_board_urls.url
where
    job_board_urls.is_prospect
