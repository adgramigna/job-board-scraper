import sys
import scrapy
import time
from scrapy.crawler import CrawlerProcess
from job_board_scraper.spiders.greenhouse_jobs_outline_spider import GreenhouseJobsOutlineSpider
from job_board_scraper.spiders.greenhouse_job_departments_spider import GreenhouseJobDepartmentsSpider
from job_board_scraper.spiders.lever_jobs_outline_spider import LeverJobsOutlineSpider
from job_board_scraper.utils import general as util
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
careers_page_url = sys.argv[1]
run_hash = util.hash_ids.encode(int(time.time()))
if careers_page_url.split(".")[1] == "greenhouse":
    process.crawl(GreenhouseJobDepartmentsSpider, careers_page_url = careers_page_url, use_existing_html=True, run_hash=run_hash)
    process.crawl(GreenhouseJobsOutlineSpider, careers_page_url = careers_page_url, use_existing_html=True, run_hash=run_hash)
elif careers_page_url.split(".")[1] == "lever":
    process.crawl(LeverJobsOutlineSpider, careers_page_url = careers_page_url, use_existing_html=True, run_hash=run_hash)
process.start()
