# !/bin/bash
cd ..
total_size=${1-200}
chunk_size=${2-20} #default to chunks of 20
lowest_id=1 #first serial id is 1.
for ((i=$lowest_id;i<=$total_size;i++))
do
    if [ $(($i % $chunk_size)) -eq 0 ]
    then
       highest_id=$i
       python run_job_scraper.py $lowest_id $highest_id 
       lowest_id=$i
    fi
done
   