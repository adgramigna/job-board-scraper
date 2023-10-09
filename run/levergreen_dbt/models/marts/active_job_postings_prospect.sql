
  
    

  create  table "neondb"."core"."active_job_postings_prospect__dbt_tmp"
  
  
    as
  
  (
    select active_job_postings.* from "neondb"."core"."active_job_postings" active_job_postings
inner join "neondb"."public"."job_board_urls" job_board_urls 
    on active_job_postings.source = job_board_urls.url
where job_board_urls.is_prospect
  );
  