{# Nov 2023
    Adds a test which confirms that the expected number of job postings from the source is being 
displayed properly in active job postings. Added because of script error when lever changed around
their departments.

Jan 2024
    Changing the source count to be the distinct URL because Deel started posting multiple links
    which went to the same job
 #}

with unique_active_jobs_per_company as (
    select run_hash, source, job_board, count(*) as num_openings
    from {{ ref('active_job_postings') }}
    group by 1,2,3
),

sources as (
    select run_hash, source, 'greenhouse' as job_board, count(distinct opening_link) as num_source_openings 
    from {{ source('greenhouse', 'greenhouse_jobs_outline') }}
    group by 1,2,3
    union all
    select run_hash, source, 'lever' as job_board, count(distinct opening_link) as num_source_openings 
    from {{ source('lever', 'lever_jobs_outline') }}
    group by 1,2,3
    union all
    select run_hash, ashby_job_board_source, 'ashby' as job_board, count(distinct opening_link) as num_source_openings 
    from {{ source('ashby', 'ashby_jobs_outline') }}
    group by 1,2,3
)

select * from unique_active_jobs_per_company as unique_active_jobs
inner join sources on unique_active_jobs.run_hash = sources.run_hash
    and unique_active_jobs.source = sources.source
where num_openings != num_source_openings