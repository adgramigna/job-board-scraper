# import logging
import logging
import scrapy
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
from twisted.internet.error import DNSLookupError, TCPTimedOutError, TimeoutError

load_dotenv()
# logger = logging.getLogger("logger")


class GreenhouseJobDepartmentsSpider(scrapy.Spider):
    name = "greenhouse_job_departments"
    allowed_domains = [
        "boards.greenhouse.io",
        "job-boards.greenhouse.io",
        "greenhouse.io",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 1)
        self.use_existing_html = kwargs.pop("use_existing_html", 0)
        self.careers_page_url = kwargs.pop("careers_page_url")
        self.run_hash = kwargs.pop("run_hash")
        self.url_id = kwargs.pop("url_id", 0)
        self.html_source = (
            self.careers_page_url[:-1]
            if self.careers_page_url[-1] == "/"
            else self.careers_page_url
        )
        self.settings = get_project_settings()
        self.current_time = time.time()
        self.page_number = 1  # default
        self.updated_at = int(self.current_time)
        self.created_at = int(self.current_time)
        self.current_date_utc = datetime.utcfromtimestamp(self.current_time).strftime(
            "%Y-%m-%d"
        )
        self.existing_html_used = False  # Initially set this to false, change later on in finalize_response if True
        self.logger.info(f"Initialized Spider, {self.html_source}")
        
        self.raw_html_s3_bucket = os.getenv("RAW_HTML_S3_BUCKET")
        if self.raw_html_s3_bucket:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION"),
            )
            logging.info("S3 Client initialized.")
        else:
            self.s3_client = None
            logging.info("RAW_HTML_S3_BUCKET is not set. Skipping HTML export.")

    @property
    def s3_html_path(self):
        s3_path_template = self.settings.get("S3_HTML_PATH")
        if not s3_path_template:
            self.logger.warning("S3_HTML_PATH is not set in settings. Skipping HTML export.")
            return None
        return s3_path_template.format(**self._get_uri_params())

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
            # Remove final "/" so company_name is correct
            return self.html_source
        else:
            return self.settings["DEFAULT_HTML"]

    @property
    def company_name(self):
        # Different format for embedded html
        if "for=" in self.html_source:
            return self.html_source.split("for=")[-1]
        # Traditional format
        return self.html_source.split("/")[-1].split("?")[0]

    @property
    def full_s3_html_path(self):
        # Ensure S3_HTML_BUCKET is set
        s3_html_bucket = self.settings.get("S3_HTML_BUCKET")
        if not s3_html_bucket:
            self.logger.warning("S3_HTML_BUCKET is not set. Skipping HTML export.")
            return None

        # Construct the full S3 path
        return "s3://" + s3_html_bucket + "/" + self.s3_html_path

    def determine_partitions(self):
        return f"date={self.current_date_utc}/company={self.company_name}"

    def _get_uri_params(self):
        params = {}
        params["source"] = self.allowed_domains[0].split(".")[1]
        params["bot_name"] = self.settings["BOT_NAME"]
        params["partitions"] = self.determine_partitions()
        params["file_name"] = (
            f"{self.company_name}-{self.allowed_domains[0].split('.')[1]}.html"
        )

        return params

    def start_requests(self):
        if not self.careers_page_url:
            self.logger.error("No careers page URL provided")
            return
        
        yield scrapy.Request(
            url=self.careers_page_url,
            callback=self.parse,
            dont_filter=True,
            errback=self.errback_httpbin,
            meta={'dont_retry': True}
        )

    def export_html(self, response_html):
        if not self.s3_html_path:
            self.logger.warning("S3_HTML_PATH is not set. Skipping HTML export.")
            return
        if not self.s3_client:
            self.logger.warning("S3 client is not initialized. Skipping HTML export.")
            return
        try:
            self.s3_client.put_object(
                Bucket=self.settings["S3_HTML_BUCKET"],
                Key=self.s3_html_path,
                Body=response_html,
                ContentType="text/html",
            )
            self.logger.info("Uploaded raw HTML to s3")
        except Exception as e:
            self.logger.error(f"Failed to upload HTML to S3: {e}")

    def determine_row_id(self, i):
        return util.hash_ids.encode(
            self.spider_id, i, self.url_id, int(self.created_at)
        )

    def finalize_response(self, response):
        if self.html_file != "":
            self.created_at = int(self.html_file["LastModified"].timestamp())
            self.existing_html_used = True
            return self.html_file["Body"].read()
        else:
            if self.s3_client:
                self.export_html(response.text)
            return response.text

    # Greenhouse has exposed a new URL with different features for scraping for some companies
    def parse_job_boards_prefix(self, i, department):
        il = ItemLoader(
            item=GreenhouseJobDepartmentsItem(),
            selector=Selector(text=department.get(), type="html"),
        )
        self.logger.info(f"Parsing row {i+1}, {self.company_name}, {self.name}")

        il.add_value("department_id", self.company_name + "_" + department.get())
        il.add_value("department_name", department.get())
        il.add_value("department_category", "level-0")

        il.add_value("id", self.determine_row_id(i))
        il.add_value("created_at", self.created_at)
        il.add_value("updated_at", self.updated_at)

        il.add_value("source", self.html_source)
        il.add_value("company_name", self.company_name)
        il.add_value("run_hash", self.run_hash)
        il.add_value("raw_html_file_location", self.full_s3_html_path)
        il.add_value("existing_html_used", self.existing_html_used)

        return il

    def parse(self, response):
        self.logger.info(f"Parsing URL: {response.url}")
        response_html = self.finalize_response(response)
        selector = Selector(text=response_html, type="html")
        
        # Add debug logging
        if self.careers_page_url.split(".")[0].split("/")[-1] == "job-boards":
            all_departments = selector.xpath("//div[contains(@class, 'job-posts')]/*[starts-with(name(), 'h')]/text()")
            num_departments = len(all_departments)
            self.logger.info(f"Found {num_departments} departments")
            
            if num_departments == 0:
                self.logger.warning("No departments found with the current XPath selector.")
            
            for i, department in enumerate(all_departments):
                il = self.parse_job_boards_prefix(i, department)
                yield il.load_item()
            
            if num_departments != 0:
                self.page_number += 1
                yield response.follow(
                    self.careers_page_url + f"?page={self.page_number}", self.parse
                )

            # for i, department in enumerate(all_departments):
            #     il = ItemLoader(
            #         item=GreenhouseJobDepartmentsItem(),
            #         selector=Selector(text=department.get(), type="html"),
            #     )
            #     self.logger.info(f"Parsing row {i+1}, {self.company_name}, {self.name}")

            #     department_id = self.company_name + "_" + department.get()
            #     il.add_value("department_id", department_id)
            #     il.add_value("department_name", department.get())
            #     il.add_value("department_category", "level-0")

            #     il.add_value("id", self.determine_row_id(i))
            #     il.add_value("created_at", self.created_at)
            #     il.add_value("updated_at", self.updated_at)

            #     il.add_value("source", self.html_source)
            #     il.add_value("company_name", self.company_name)
            #     il.add_value("run_hash", self.run_hash)
            #     il.add_value("raw_html_file_location", self.full_s3_html_path)
            #     il.add_value("existing_html_used", self.existing_html_used)

            #     # print(il.load_item())

            #     yield il.load_item()

        else:
            all_departments = selector.xpath('//section[contains(@class, "level")]')
            self.logger.info(f"Found {len(all_departments)} departments")
            
            if len(all_departments) == 0:
                self.logger.warning("No departments found with the current XPath selector.")
            
            for i, department in enumerate(all_departments):
                il = ItemLoader(
                    item=GreenhouseJobDepartmentsItem(),
                    selector=Selector(text=department.get(), type="html"),
                )
                dept_loader = il.nested_xpath(
                    f"//section[contains(@class, 'level')]/*[starts-with(name(), 'h')]"
                )
                self.logger.info(f"Parsing row {i+1}, {self.company_name}, {self.name}")

                dept_loader.add_xpath("department_id", "@id")
                dept_loader.add_xpath("department_name", "text()")
                il.add_xpath(
                    "department_category", "//section[contains(@class, 'level')]/@class"
                )

                il.add_value("id", self.determine_row_id(i))
                il.add_value("created_at", self.created_at)
                il.add_value("updated_at", self.updated_at)

                il.add_value("source", self.html_source)
                il.add_value("company_name", self.company_name)
                il.add_value("run_hash", self.run_hash)
                il.add_value("raw_html_file_location", self.full_s3_html_path)
                il.add_value("existing_html_used", self.existing_html_used)

                yield il.load_item()
            # self.logger.info(f"{dep_xpath} Department here")

    def errback_httpbin(self, failure):
        self.logger.error(f"Request failed: {failure.value}")
