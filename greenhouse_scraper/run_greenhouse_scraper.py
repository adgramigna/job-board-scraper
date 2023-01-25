import scrapy
import sys
from scrapy.crawler import CrawlerProcess
from greenhouse_scraper.spiders.jobs_outline_spider import JobsOutlineSpider
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
process.crawl(JobsOutlineSpider, careers_page_url = sys.argv[1])
process.start()
