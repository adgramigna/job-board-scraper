import scrapy

# import logging
import time

import boto3
import os
from dotenv import load_dotenv
from job_board_scraper.spiders.greenhouse_jobs_outline_spider import (
    GreenhouseJobsOutlineSpider,
)
from job_board_scraper.items import LeverJobsOutlineItem
from job_board_scraper.utils import general as util
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from datetime import datetime

load_dotenv()
# logger = logging.getLogger("logger")


class LeverJobsOutlineSpider(GreenhouseJobsOutlineSpider):
    name = "lever_jobs_outline"
    allowed_domains = ["jobs.lever.co"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 3)
        self.logger.info(f"Initialized Spider, {self.html_source}")

    def parse(self, response):
        response_html = self.finalize_response(response)
        selector = Selector(text=response_html, type="html")
        postings_groups = selector.xpath('//div[@class="postings-group"]')
        # departments = selector.xpath("//div[contains(@class, 'large-category')]/text()")
        # job_openings = selector.xpath('//a[@class="posting-title"]')

        for i, postings_group in enumerate(postings_groups):
            stratified_selector = Selector(text=postings_group.get(), type="html")

            potential_primary_department = stratified_selector.xpath(
                f"//div[contains(@class, 'large-category-header')]/text()"
            )

            label_department = stratified_selector.xpath(
                f"//div[contains(@class, 'large-category-label')]/text()"
            )

            if i == 0:
                if len(potential_primary_department) == 0:
                    secondary_string = "label"
                    primary_department = label_department.get()
                else:
                    secondary_string = "header"
                    primary_department = potential_primary_department.get()
            if secondary_string == "header":
                if len(potential_primary_department) != 0:
                    primary_department = potential_primary_department.get()
                departments = primary_department + " – " + label_department.get()
            else:
                departments = label_department.get()

            job_openings = stratified_selector.xpath("//a[@class='posting-title']")

            for j, opening in enumerate(job_openings):
                il = ItemLoader(
                    item=LeverJobsOutlineItem(),
                    selector=Selector(text=opening.get(), type="html"),
                )
                # print(opening.get())
                self.logger.info(f"Parsing row {i+1}, {self.company_name} {self.name}")
                # nested = il.nested_xpath('//a[@class="posting-title"]')

                il.add_value("department_names", departments)
                il.add_xpath("opening_link", '//a[@class="posting-title"]/@href')
                # nested.add_xpath("opening_link", "@href")
                il.add_xpath("opening_title", "//h5/text()")
                il.add_xpath(
                    "workplace_type", "//span[contains(@class, 'workplaceType')]/text()"
                )
                il.add_xpath("location", "//span[contains(@class, 'location')]/text()")

                il.add_value("id", self.determine_row_id(i * 1000 + j))
                il.add_value("created_at", self.created_at)
                il.add_value("updated_at", self.updated_at)
                il.add_value("source", self.html_source)
                il.add_value("company_name", self.company_name)
                il.add_value("run_hash", self.run_hash)
                il.add_value("raw_html_file_location", self.full_s3_html_path)
                il.add_value("existing_html_used", self.existing_html_used)

                yield il.load_item()
            # self.logger.info(f"{dep_xpath} Department here")
