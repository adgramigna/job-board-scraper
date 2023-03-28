import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from greenhouse_scraper.spiders.jobs_outline_spider import JobsOutlineSpider
from greenhouse_scraper.spiders.job_departments_spider import JobDepartmentsSpider
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
# process.crawl(JobsOutlineSpider, careers_page_url = sys.argv[1])
process.crawl(JobDepartmentsSpider, careers_page_url = sys.argv[1], use_existing_html=False)
process.start()
