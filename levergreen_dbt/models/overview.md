{% docs __overview__ %}
### Links
[Levergreen Website](https://levergreen.dev/)\
[Github Repo](https://github.com/adgramigna/job-board-scraper/)
# Levergreen dbt Data Model
This website displays the data model of the Levergreen Job Scraper. We start by scraping data from the job boards Greenhouse
and Lever and cleaning the data in our `stg_<job_board>__` staging models. We then do some more advanced transformations and regrain
in our `int_` intermediate models. Finally, we create our `marts` models containing `all_job_postings` scraped by Levergreen, and 
`active_job_postings`

![Lineage Graph](https://raw.githubusercontent.com/adgramigna/job-board-scraper/main/assets/images/lineage_graph.png)

## Staging Models
To view, on the left menu, click `levergreen_dbt -> models -> staging`

We have staging models for each job board. For Greenhouse, we chose to scrape departments and job information in two separate Scrapy Spiders.
For Lever, we were able to get both in one spider. In these models we normalize our source data and make simple transformations.

## Intermediate Models
To view, on the left menu, click `levergreen_dbt -> models -> intermediate`

In our intermediate models, we expand the job departments from multiple rows to one row, and drop metadata columns not needed for our Marts. After our
intermediate models are complete, each job board adheres to the same schema. It is ready for us to union in our marts.

## Marts Models
To view, on the left menu, click `levergreen_dbt -> models -> marts`

### all_job_postings
Here we keep a record of all job postings ever scraped by Levergreen. This could be useful if we'd like to late run analyses on how long jobs are
likely to open, what months have the most jobs posted, company posting history, etc. We also generate important columns categorizing the type of role
and how long it has been active, if at all.

### active_job_postings
Here we filter `all_job_postings for only jobs which are active. The results of this are persisted to Airtable via Hightouch, and subsequently to our
Softr Website.

{% enddocs %}