import scrapy
# import logging
import time

import boto3
import os
from dotenv import load_dotenv
from greenhouse_scraper.spiders.job_departments_spider import JobsOutlineSpider
from greenhouse_scraper.items import JobDepartmentsItem
from greenhouse_scraper.utils import general as util
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from datetime import datetime

load_dotenv()
# logger = logging.getLogger("logger")

class LeverJobsOutlineSpider(JobsOutlineSpider):
    name = "lever_jobs_outline"
    allowed_domains = ["jobs.lever.co"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 2)
        self.logger.info(f"Initialized Spider, {self.html_source}")

    def parse(self, response):
        response_html = self.finalize_response(response)
        selector = Selector(text=response_html, type="html")
        all_departments = selector.xpath('//section[contains(@class, "level")]')

        for i, department in enumerate(all_departments):
            il = ItemLoader(item=JobDepartmentsItem(), selector=Selector(text=department.get(),type="html"))
            dept_loader = il.nested_xpath(f"//section[contains(@class, 'level')]/*[self::h1 or self::h2 or self::h3 or self::h4]")
            self.logger.info(f"Parsing row {i+1}, {self.company_name}, {self.name}")

            dept_loader.add_xpath("department_id", "@id")
            dept_loader.add_xpath("department_name", "text()")
            il.add_xpath("department_category", "//section[contains(@class, 'level')]/@class")

            il.add_value("id", self.determine_row_id(i))
            il.add_value("created_at", self.created_at)
            il.add_value("updated_at", self.updated_at)

            il.add_value("source", self.html_source)
            il.add_value("company_name", self.company_name)

            yield il.load_item()

            # self.logger.info(f"{dep_xpath} Department here")