with all_postings as (
    select * from {{ ref('int_greenhouse_departments_expanded_and_joined_with_outline') }}
    union all
    select * from {{ ref('int_lever_departments_expanded') }}
),

get_earliest_and_latest_dates as (
    select
        full_opening_link,
        min(created_date_utc) as earliest_opening_date,
        max(created_date_utc) as latest_opening_date
    from all_postings
    group by 1
),

all_postings_with_earliest_and_latest as (
    select 
        all_postings.*, 
        date(timezone('utc', now())) = all_postings.created_date_utc as is_active,
        earliest_and_latest.earliest_opening_date,
        earliest_and_latest.latest_opening_date,
        earliest_and_latest.latest_opening_date - earliest_and_latest.earliest_opening_date + 1 as days_active
    from all_postings
    inner join get_earliest_and_latest_dates as earliest_and_latest on all_postings.full_opening_link = earliest_and_latest.full_opening_link
)

select *,
    case
        when days_active > 90 then 'Stale'
        when days_active > 60 then 'Old'
        when days_active > 30 then 'Medium'
        when days_active > 7  then 'Recent'
    else 'New'
    end as posting_length_category
from all_postings_with_earliest_and_latest
