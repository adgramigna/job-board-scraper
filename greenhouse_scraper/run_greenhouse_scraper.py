import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from greenhouse_scraper.spiders.jobs_outline_spider import JobsOutlineSpider
from greenhouse_scraper.spiders.job_departments_spider import JobDepartmentsSpider
from greenhouse_scraper.spiders.lever_jobs_outline_spider import LeverJobsOutlineSpider
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
careers_page_url = sys.argv[1]
if careers_page_url.split(".")[1] == "greenhouse":
    process.crawl(JobDepartmentsSpider, careers_page_url = careers_page_url, use_existing_html=True)
    process.crawl(JobsOutlineSpider, careers_page_url = careers_page_url, use_existing_html=True)
elif careers_page_url.split(".")[1] == "lever":
    process.crawl(LeverJobsOutlineSpider, careers_page_url = careers_page_url, use_existing_html=True)
process.start()
