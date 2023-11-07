{{ config(enabled=true, severity = 'error') }}
--disable when all companies have has jobs

-- here we are checking if the scraper did correctly scrape jobs for each careers_page
-- If the scraper missed a page due to an unexpected error, we will have mismatches here

with expected_sources as (
    select distinct url as expected_source
    from {{ source('levergreen', 'job_board_urls') }}
    where is_enabled
    and url != 'https://boards.greenhouse.io/embed/job_board?for=openspace'
),

actual_sources as (
    select distinct source as actual_source
    from {{ ref('active_job_postings') }}
)

select * from expected_sources
full outer join actual_sources on expected_sources.expected_source = actual_sources.actual_source
where expected_sources.expected_source is null or actual_sources.actual_source is null