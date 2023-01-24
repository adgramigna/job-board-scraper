import scrapy
from scrapy.crawler import CrawlerProcess
from greenhouse_scraper.spiders.jobs_outline_spider import JobsOutlineSpider
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
process.crawl(JobsOutlineSpider)
process.start()
