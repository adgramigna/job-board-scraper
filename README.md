# Levergreen Job Board Scraper
End Result: https://levergreen.dev  
Data Documentation: https://adgramigna.github.io/job-board-scraper/#!/overview

![Data Flow](/assets/images/data_flow.jpg)

## Overall Summary

Levergreen is an application which scrapes job openings from Greenhouse and Lever once a day, cleans and transforms the data to fit a unified data model, and finally displays the data live on [levergreen.dev](https://levergreen.dev). 

## Web Scraping
### Summary
Web Scraping is done via [Scrapy](https://scrapy.org/) using 3 spiders: two spiders for Greenhouse to obtain the job outline and the job department info, and one spider for Lever containing outline and department info. These spiders are orchestrated from the file `run_job_scraper.py`. Here we are determining which set of spiders to run based on the job board source, and the urls to scrape based on what we've stored in our Postgres DB.

### Outputs
Raw HTML pages are sent to S3 (Note: depending on cost I may omit this step going forward). Our scraping methodology also ensures that if we attempt to scrape the same job board twice a day, by default we will not scrape the website the second time, but instead use the existing HTML file stored in S3 to prevent throttling the websites. We take the important pieces of each job posting and export this data to a Postgres Instance hosted on Amazon RDS.

## Data Transformation
Data Transformation is done via [dbt](https://www.getdbt.com/), specifcally [dbt Core](https://github.com/dbt-labs/dbt-core) for Postgres. Here we take job outline data from multiple job boards and clean and transform the data so it can be actionable for an end user.More information about the exact steps taken can be found [here](https://github.com/adgramigna/job-board-scraper/blob/main/levergreen_dbt/README.md) (mobile) or [here](https://adgramigna.github.io/job-board-scraper/#!/overview) (desktop)

After we obtain our cleaned data, we need to expose it to be available on a website.

## Github Actions
All the above steps are executed on a daily cron schedule via Github Actions. We opted to use Github Actions instead of a scheduler like Airflow or Prefect given the small scale of this project. We have two Github actions runs, one which scrapes the data and one which transforms the data in dbt. These can be found in the `.github/workflows` folder.

A key step in the Web Scraping which is prevalent in the Github Actions workflow is `compare_workflow_success.py`. This ensures that the number of careers pages we expected to scrape matches what we actually scraped. I added this to make sure we are aware if one company is not properly scraped due to a change in the goal URL, or another reason.

## Displaying the data on a Website
### Summary
From the beginning of this project, I wanted to use [Softr](https://www.softr.io/) to expose the cleaned data in a no-code website, because I had heard good things about it, and I do not know enough front-end programming to create my own website for this. Softr can use data from Airtable or Google Sheets, so I chose to export my Postgres data to Airtable as I wanted to gain experience there and I found Airtable to be a more convenient choice with Softr.

### Hightouch
[Hightouch](https://hightouch.com/) is a Reverse ETL tool which takes data from a Data Warehouse and into an external product, in this case Airtable. Hightouch is also running a cron schedule, with plenty of buffer after the data transformation for Hightouch to obtain the most recent data.

### Airtable
[Airtable](https://airtable.com/) is mostly used as a middle-man to allow Softr to ingest the data. I am not much interacting with the data from the Airtable UI.

### Softr
Softr is able to visualize my Airtable data in real time, and I was able to create a nice website to visualize the active job postings. On the website, we can filter for specific job categories, or for "Remote Only" roles. I've also added a suggestion box at the bottom for people to suggest companies they would like to see included in my list.

## Cost
All of the software I am using here is free for my use case except for AWS and the domain name https://levergreen.dev

