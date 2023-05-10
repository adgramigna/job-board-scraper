import scrapy
# import logging
import time

import boto3
import os
from dotenv import load_dotenv
from job_board_scraper.items import GreenhouseJobsOutlineItem
from job_board_scraper.utils import general as util
from job_board_scraper.spiders.greenhouse_job_departments_spider import GreenhouseJobDepartmentsSpider
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from datetime import datetime

load_dotenv()
# logger = logging.getLogger("logger")

class GreenhouseJobsOutlineSpider(GreenhouseJobDepartmentsSpider):
    name = "greenhouse_jobs_outline"
    allowed_domains = ["boards.greenhouse.io"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 2)
        self.use_existing_html = kwargs.pop("use_existing_html", 1) #from departments
        self.logger.info(f"Initialized Spider, {self.html_source}")
    
    def parse(self, response):
        response_html = self.finalize_response(response)
        selector = Selector(text=response_html, type="html")
        job_openings = selector.xpath('//div[@class="opening"]')

        for i, opening in enumerate(job_openings):
            il = ItemLoader(item=GreenhouseJobsOutlineItem(), selector=Selector(text=opening.get(),type="html"))
            self.logger.info(f"Parsing row {i+1}, {self.company_name} {self.name}")
            nested = il.nested_xpath('//div[@class="opening"]')

            nested.add_xpath("department_ids", "@department_id")
            nested.add_xpath("office_ids", "@office_id")
            il.add_xpath("opening_link", "//a/@href")
            il.add_xpath("opening_title", "//a/text()")
            il.add_xpath("location", "//span/text()")
            
            il.add_value("id", self.determine_row_id(i))
            il.add_value("created_at", self.created_at)
            il.add_value("updated_at", self.updated_at)
            il.add_value("source", self.html_source)
            il.add_value("run_hash", self.run_hash)
            # self.logger.info(f'{i} {j} {k} {job_xpath} xpth')
            yield il.load_item()

        # filename = f'{self.company_name}-{self.allowed_domains[0].split(".")[1]}.html'
        # with open(filename, 'wb') as f:
        #     f.write(response.body)
        # self.log(f'Saved file {filename}')