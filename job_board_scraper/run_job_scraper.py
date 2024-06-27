import sys
import scrapy
import os
import logging
import psycopg2
import time
import multiprocessing
from scrapy.crawler import CrawlerProcess
from job_board_scraper.spiders.greenhouse_jobs_outline_spider import (
    GreenhouseJobsOutlineSpider,
)
from job_board_scraper.spiders.greenhouse_job_departments_spider import (
    GreenhouseJobDepartmentsSpider,
)
from job_board_scraper.spiders.lever_jobs_outline_spider import LeverJobsOutlineSpider
from job_board_scraper.utils.postgres_wrapper import PostgresWrapper
from job_board_scraper.utils import general as util
from job_board_scraper.utils.scraper_util import get_url_chunks
from scrapy.utils.project import get_project_settings

logger = logging.getLogger("logger")
run_hash = util.hash_ids.encode(int(time.time()))


def run_spider(single_url_chunk, chunk_number):
    process = CrawlerProcess(get_project_settings())
    for i, careers_page_url in enumerate(single_url_chunk):
        logger.info(f"url = {careers_page_url}")
        if careers_page_url.split(".")[1] == "greenhouse":
            process.crawl(
                GreenhouseJobDepartmentsSpider,
                careers_page_url=careers_page_url,
                use_existing_html=False,
                run_hash=run_hash,
                url_id=chunk_number * len(single_url_chunk) + i,
            )
            process.crawl(
                GreenhouseJobsOutlineSpider,
                careers_page_url=careers_page_url,
                use_existing_html=False,
                run_hash=run_hash,
                url_id=chunk_number * len(single_url_chunk) + i,
            )
        elif careers_page_url.split(".")[1] == "lever":
            process.crawl(
                LeverJobsOutlineSpider,
                careers_page_url=careers_page_url,
                use_existing_html=False,
                run_hash=run_hash,
                url_id=chunk_number * len(single_url_chunk) + i,
            )
    process.start()


if __name__ == "__main__":
    chunk_size = int(os.environ.get("CHUNK_SIZE"))

    connection = psycopg2.connect(
        host=os.environ.get("PG_HOST"),
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
        dbname=os.environ.get("PG_DATABASE"),
    )
    cursor = connection.cursor()
    cursor.execute(os.environ.get("PAGES_TO_SCRAPE_QUERY"))
    careers_page_urls = cursor.fetchall()
    cursor.close()
    connection.close()
    url_chunks = get_url_chunks(careers_page_urls, chunk_size)

    num_processes = len(url_chunks)
    processes = []

    for i, single_url_chunk in enumerate(url_chunks):
        time.sleep(60)  # sleep to avoid issues exporting to Postgres
        p = multiprocessing.Process(target=run_spider, args=(single_url_chunk, i))
        processes.append(p)
        p.start()

    for p in processes:
        time.sleep(60)  # sleep to avoid issues exporting to Postgres
        p.join()
