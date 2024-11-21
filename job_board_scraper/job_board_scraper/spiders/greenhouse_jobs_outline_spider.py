import scrapy

# import logging
import time

import boto3
import os
from dotenv import load_dotenv
from job_board_scraper.items import GreenhouseJobsOutlineItem
from job_board_scraper.utils import general as util
from job_board_scraper.spiders.greenhouse_job_departments_spider import (
    GreenhouseJobDepartmentsSpider,
)
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from datetime import datetime

load_dotenv()
# logger = logging.getLogger("logger")


class GreenhouseJobsOutlineSpider(GreenhouseJobDepartmentsSpider):
    name = "greenhouse_jobs_outline"
    allowed_domains = [
        "boards.greenhouse.io",
        "job-boards.greenhouse.io",
        "boards.greenhouse.io",
        "greenhouse.io",        
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 2)
        self.use_existing_html = kwargs.pop("use_existing_html", 1)  # from departments
        self.logger.info(f"Initialized Spider, {self.html_source}")
        self.page_number = 1

    def get_department_ids(self, job_post):
        stratified_selector = Selector(text=job_post.get(), type="html")

        primary_department = stratified_selector.xpath(
            "//*[starts-with(name(), 'h')]/text()"
        ).get()

        department_ids = self.company_name + "_" + primary_department

        job_openings = stratified_selector.xpath("//td[@class='cell']")

        return department_ids, job_openings

    def parse_job_boards_prefix(self, i, j, department_ids, opening):
        try:
            il = ItemLoader(
                item=GreenhouseJobsOutlineItem(),
                selector=Selector(text=opening.get(), type="html"),
            )
            
            il.add_value("department_ids", department_ids)
            il.add_xpath("opening_link", "//a/@href")
            il.add_xpath("opening_title", "//p[contains(@class, 'body--medium')]/text()")
            il.add_xpath("location", "//p[contains(@class, 'body--metadata')]/text()")
            
            il.add_value("id", self.determine_row_id(i * 1000 + j * 100 + self.page_number))
            il.add_value("created_at", self.created_at)
            il.add_value("updated_at", self.updated_at)
            il.add_value("source", self.html_source)
            il.add_value("run_hash", self.run_hash)
            il.add_value("raw_html_file_location", self.full_s3_html_path)
            il.add_value("existing_html_used", self.existing_html_used)
            
            return il
        except Exception as e:
            self.logger.error(f"Error in parse_job_boards_prefix: {e}")
            raise e

    def parse(self, response):
        try:
            response_html = self.finalize_response(response)
            selector = Selector(text=response_html, type="html")
            
            if self.careers_page_url.split(".")[0].split("/")[-1] == "job-boards":
                job_posts = selector.xpath("//div[(@class='job-posts')]")
                self.logger.info(f"Found {len(job_posts)} job posts")
                
                for i, job_post in enumerate(job_posts):
                    try:
                        department_ids, job_openings = self.get_department_ids(job_post)
                        self.logger.info(f"Processing department {department_ids} with {len(job_openings)} openings")
                        
                        for j, opening in enumerate(job_openings):
                            il = self.parse_job_boards_prefix(i, j, department_ids, opening)
                            item = il.load_item()
                            self.logger.info(f"Yielding job item: {item}")
                            yield item
                            
                    except Exception as e:
                        self.logger.error(f"Error processing job post {i}: {e}")
                        
                if len(job_posts) != 0:
                    next_page = self.careers_page_url + f"?page={self.page_number + 1}"
                    self.logger.info(f"Following next page: {next_page}")
                    self.page_number += 1
                    yield response.follow(url=next_page, callback=self.parse)
            else:
                job_openings = selector.xpath('//div[@class="opening"]')
                self.logger.info(f"Found {len(job_openings)} job openings")
                
                for i, opening in enumerate(job_openings):
                    try:
                        il = ItemLoader(
                            item=GreenhouseJobsOutlineItem(),
                            selector=Selector(text=opening.get(), type="html"),
                        )
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
                        il.add_value("raw_html_file_location", self.full_s3_html_path)
                        il.add_value("existing_html_used", self.existing_html_used)
                        
                        self.logger.info(f"Yielding job item: {il.load_item().get('opening_title')}")
                        try:
                            yield il.load_item()
                        except Exception as e:
                            self.logger.error(f"Error yielding item: {e}")
                        
                    except Exception as e:
                        self.logger.error(f"Error processing opening {i}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error in parse method: {e}")
