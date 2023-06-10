
  
    

  create  table "postgres"."core"."active_job_postings__dbt_tmp"
  
  
    as
  
  (
    select * from "postgres"."core"."all_job_postings" where is_active
  );
  