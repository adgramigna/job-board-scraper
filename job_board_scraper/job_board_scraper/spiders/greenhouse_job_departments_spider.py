import scrapy
# import logging
import time

import boto3
import os
from dotenv import load_dotenv
from job_board_scraper.items import GreenhouseJobDepartmentsItem
from job_board_scraper.utils import general as util
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from datetime import datetime

load_dotenv()
# logger = logging.getLogger("logger")

class GreenhouseJobDepartmentsSpider(scrapy.Spider):
    name = "greenhouse_job_departments"
    allowed_domains = ["boards.greenhouse.io"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 1)
        self.use_existing_html = kwargs.pop("use_existing_html", 0)
        self.careers_page_url = kwargs.pop("careers_page_url", "")
        self.html_source = self.careers_page_url[:-1] if self.careers_page_url[-1] == '/' else self.careers_page_url
        self.settings = get_project_settings()
        self.current_time = time.time()
        self.updated_at = int(self.current_time)
        self.created_at = int(self.current_time)
        self.current_date_utc = datetime.utcfromtimestamp(self.current_time).strftime("%Y-%m-%d")
        self.logger.info(f"Initialized Spider, {self.html_source}")

    @property
    def s3_client(self):
        return boto3.client(
            "s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION")
        )

    @property
    def s3_html_path(self):
        return self.settings["S3_HTML_PATH"].format(**self._get_uri_params())
    
    @property
    def html_file(self):
        if self.use_existing_html == False:
            return ""
        try:
            return self.s3_client.get_object(
                Bucket=self.settings["S3_HTML_BUCKET"], Key=self.s3_html_path
            )
        except:
            return ""

    @property
    def url(self):
        if self.html_file == "":
            #Remove final "/" so company_name is correct
            return self.html_source
        else:
            return self.settings["DEFAULT_HTML"]
    
    @property
    def company_name(self):
        return self.html_source.split("/")[-1]
    
    def determine_partitions(self):
        return f"date={self.current_date_utc}/company={self.company_name}"

    def _get_uri_params(self):
        params = {}
        params["source"] = self.allowed_domains[0].split('.')[1]
        params["bot_name"] = self.settings["BOT_NAME"]
        params["partitions"] = self.determine_partitions()
        params["file_name"] = f"{self.company_name}-{self.allowed_domains[0].split('.')[1]}.html"

        return params

    def start_requests(self):
        yield scrapy.Request(url=self.url, callback=self.parse)
    
    def export_html(self, response_html):
        self.s3_client.put_object(
            Bucket=self.settings["S3_HTML_BUCKET"],
            Key=self.s3_html_path,
            Body=response_html,
            ContentType="text/html",
        )
        self.logger.info("Uploaded raw HTML to s3")
    
    def determine_row_id(self, i):
        return util.hash_ids.encode(
            self.spider_id,
            i,
            int(self.created_at)
        )

    def finalize_response(self, response):
        if self.html_file != "":
            self.created_at = int(self.html_file["LastModified"].timestamp())
            return self.html_file["Body"].read()
        else:
            self.export_html(response.text)
            return response.text

    def parse(self, response):
        response_html = self.finalize_response(response)
        selector = Selector(text=response_html, type="html")
        all_departments = selector.xpath('//section[contains(@class, "level")]')

        for i, department in enumerate(all_departments):
            il = ItemLoader(item=GreenhouseJobDepartmentsItem(), selector=Selector(text=department.get(),type="html"))
            dept_loader = il.nested_xpath(f"//section[contains(@class, 'level')]/*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5]")
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