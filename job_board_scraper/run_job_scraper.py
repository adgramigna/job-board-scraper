import sys
import scrapy
import os
import logging
import psycopg2
from scrapy.crawler import CrawlerProcess
from job_board_scraper.spiders.greenhouse_jobs_outline_spider import GreenhouseJobsOutlineSpider
from job_board_scraper.spiders.greenhouse_job_departments_spider import GreenhouseJobDepartmentsSpider
from job_board_scraper.spiders.lever_jobs_outline_spider import LeverJobsOutlineSpider
from job_board_scraper.utils.postgres_wrapper import PostgresWrapper
from scrapy.utils.project import get_project_settings

logger = logging.getLogger("logger")
process = CrawlerProcess(get_project_settings())
pg_wrapper = PostgresWrapper()
connection = psycopg2.connect(host=os.environ.get("PG_HOST"), user=os.environ.get("PG_USER"), password=os.environ.get("PG_PASSWORD"), dbname=os.environ.get("PG_DATABASE"))
cursor = connection.cursor()
cursor.execute(os.environ.get("PAGES_TO_SCRAPE_QUERY"))
careers_page_urls = cursor.fetchall()
cursor.close()
connection.close()

for url in careers_page_urls:
    careers_page_url = url[0] #UnTuple-ify
    logger.info(f"url = {careers_page_url} {careers_page_urls}")
    if careers_page_url.split(".")[1] == "greenhouse":
        process.crawl(GreenhouseJobDepartmentsSpider, careers_page_url = careers_page_url, use_existing_html=True)
        process.crawl(GreenhouseJobsOutlineSpider, careers_page_url = careers_page_url, use_existing_html=True)
    elif careers_page_url.split(".")[1] == "lever":
        process.crawl(LeverJobsOutlineSpider, careers_page_url = careers_page_url, use_existing_html=True)
process.start()
