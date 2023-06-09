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
    end as posting_length_category,
    case
        when lower(primary_department) like '%data%' 
            or lower(primary_department) like '%analytics%'
            or lower(secondary_department) like '%data%' 
            or lower(secondary_department) like '%analytics%'
            or lower(opening_title) like '%data%' 
            or lower(opening_title) like '%analytics%'
            then 'Data'
        when lower(primary_department) like '%engineer%' 
            or lower(secondary_department) like '%engineer%' 
            or lower(opening_title) like '%engineer%' 
            then 'Software Engineering'
        when lower(primary_department) like '%sales%' 
            or lower(secondary_department) like '%sales%' 
            or lower(opening_title) like '%sales%' 
            or lower(opening_title) like '%account executive'
            then 'Sales'
        when lower(primary_department) like '%finance%' 
            or lower(primary_department) like '%accounting%' 
            or lower(secondary_department) like '%finance%' 
            or lower(secondary_department) like '%accounting%' 
            or lower(opening_title) like '%finance%'
            or lower(opening_title) like '%accounting%' 
            then 'Finance & Accounting'
        when lower(primary_department) like '%operations%' 
            or lower(secondary_department) like '%operations%' 
            or lower(opening_title) like '%operations%' 
            then 'Operations'
        when lower(primary_department) like '%product%' 
            or lower(secondary_department) like '%product%' 
            or lower(opening_title) like '%product%'
            then 'Product'
        else 'Other'
    end as opening_category
from all_postings_with_earliest_and_latest