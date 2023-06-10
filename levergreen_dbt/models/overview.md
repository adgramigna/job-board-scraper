{% docs __overview__ %}
### Links
[Levergreen Website](https://corey542.softr.app/)

[Github Repo](https://github.com/adgramigna/job-board-scraper/)
# Levergreen dbt Data Model
This website displays the data model of the Levergreen Job Scraper. We start by scraping data from the job boards Greenhouse
and Lever and cleaning the data in our `stg_<job_board>__` staging models. We then do some more advanced transformations and regrain
in our `int_` intermediate models. Finally, we create our `marts` models containing `all_job_postings` scraped by Levergreen, and 
`active_job_postings`



![Lineage](/assets/images/lineage_graph.png)

{% enddocs %}