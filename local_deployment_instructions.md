# Deploying Locally

I will try to provide steps on how to run this locally. Please take everything I share here with a grain of salt, as this is only
a personal project without ongoing maintenance for other deployments besides my own. After cloning the repo, the key piece needed
to run this locally is properly setting up your environment varaibles. Let's get started!

### Aside
I will walk through how to set it up as I have with a
Postgres Database, but for a simple use case only focused on scraping, and not using dbt, you may want to consider using the
[FEEDS](https://docs.scrapy.org/en/latest/topics/feed-exports.html) setting in settings.py, and export the output to a csv or JSON.
More detail on this can be found [here](https://www.geeksforgeeks.org/scrapy-feed-exports/#). If you go this route, you will also need to disable the `ITEM_PIPELINES` setting in [`settings.py`](/job_board_scraper/job_board_scraper/settings.py). You may also want to look at the code [`run_job_scraper_single.py`](/job_board_scraper/run_job_scraper_single.py) which takes a single url as a command line parameter, instead of scraping many urls.

## Prerequisites

I'll go in to detail on some environment variables that need to be defined to run the scraper. Please see [`.env.example`](/.env.example) as a helpful resource.

1. You need an AWS account, as well as the following enivironment variables:
    <ol type="a">
    <li>AWS_ACCESS_KEY_ID</li>
    <li>AWS_SECRET_ACCESS_KEY</li>
    <li>AWS_REGION</li>
    </ol>

    Here is some information on how to get these, in the [boto3 doumentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
2. You also need an S3 bucket to store your raw HTML scraped, or you choose to omit this part by removing the `export_html` function call. I have this variable defined in my environment variables as `RAW_HTML_S3_BUCKET`
3. You need to connect your own Postgres database, or sign up for [Neon](https://neon.tech) as I have. You will probably be okay using the free tier of Neon for quite a while. You will need the following environment variables:
    <ol type="a">
    <li>PG_DATABASE</li>
    <li>PG_HOST</li>
    <li>PG_USER</li>
    <li>PG_PASSWORD</li>
    </ol>

4. There  is one point in the code where we are querying Postgres to determine what urls we need to scrape. You need to create a table in your Postgres DB with at minimum the columns `id` (I did type SERIAL here), `url`, and `is_enabled`, which should be defaulted to true. **Here is where you must insert into this table the urls which you would like to scrape job postings from**. You can change `is_enabled` to false if you want to stop scraping a certain url. I had to do this with Ramp and OpenSea, as they opted for [Ashby](https://www.ashbyhq.com/) which is not supported (yet!). You need the environment variable, `PAGES_TO_SCRAPE_QUERY`, which should look something similar to this `select distinct url from <YOUR_URLS_TABLE> where is_enabled;`

5. Finally, I opted to determine a unique id for a Levergreen record using [Hashids](https://github.com/davidaurelio/hashids-python), it looks they they rebranded to [Sqids](https://sqids.org/). For now, I'll keep the existing hashids implemenation. We need a salt in the hashids algorithm which can be any string. Save any string to the environment variable `HASHIDS_SALT`.

## Running the Program

Once you've completed the prerequisites, you are ready to get scraping. My recommendation here is to use the Github Action workflow [`daily_job_board_scrape.yml`](.github/workflows/daily_job_board_scrape.yml) as a guide, to see how we are scraping. The key steps are:


1. Installing the dependencies defined in [`requirements.txt`](/requirements.txt) (virtual enviorment is recommended).
2. Running the file [`run_job_scraper.py`](job_board_scraper/run_job_scraper_single.py) with the necessary environment variables.
3. Installing dbt packages using the `dbt deps` command
4. Running dbt to build are mart tables (`all_job_postings` and `active_job_postings`).

I also have a testing workflow to make sure my data adheres to the tests I've defined in dbt.

## Final Thoughts

This should be all that is needed to begin scraping jobs from companies you are interested in. I hope you can use this to find your dream role at an exciting company! Please star this repo and spread the word if you find this project useful. Best of luck!