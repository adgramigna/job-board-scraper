--  June 2023
-- This test will check for jobs with the same job_board_id that have dropped off and then returned.
-- My model will not treat these as 1 day active, and instead will use the earliest active date to determine when the job was first acrtive
-- If we find this behavior does occur, then we will reassess this days_active_calculation in our data model.

with expected_days as (
select distinct full_opening_link, days_active as expected_days_active from {{ ref('all_job_postings') }}
),

add_rn as (
select *, row_number() over(partition by full_opening_link, created_date_utc order by id) as earliest_daily from {{ ref('all_job_postings') }}
)

select * from add_rn
inner join expected_days on add_rn.full_opening_link = expected_days.full_opening_link
where add_rn.earliest_daily = 1
and add_rn.is_active
and expected_days_active != days_active