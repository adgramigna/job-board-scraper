
  
    

  create  table "neondb"."core"."active_job_postings__dbt_tmp"
  
  
    as
  
  (
    select * from "neondb"."core"."all_job_postings" where is_active
  );
  