import scrapy
# import logging
import time

import boto3
import os
from dotenv import load_dotenv
# from greenhouse_scraper.items import BoxscoreIDItem
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from datetime import datetime

load_dotenv()
# logger = logging.getLogger("logger")


#TODO: 
# 1. Add in proper URLs as well as logic to scrape HTML file in s3 or raw website
    #a. add kwargs to run script as well
# 2. Create s3 bucket for raw HTML
# 3. Begin Scraping Greenhouse for 3 different companies

class JobsOutlineSpider(scrapy.Spider):
    name = "jobs_outline"
    allowed_domains = ["boards.greenhouse.io"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 0)
        self.use_existing_html = kwargs.pop("use_existing_html", 0)
        self.html_source = kwargs.pop("careers_page_url", "")
        self.settings = get_project_settings()
        self.current_time = time.time()
        self.updated_at = self.current_time
        self.created_at = self.current_time
        self.current_time_utc = datetime.utcfromtimestamp(self.current_time)
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
            #Remove final "/" so greenhouse_company_name is correct
            return self.html_source[:-1] if self.html_source[-1] == '/' else self.html_source
        else:
            return self.settings["DEFAULT_HTML"]
    
    @property
    def greenhouse_company_name(self):
        return self.url.split("/")[-1]
    
    def determine_partitions(self):
        return f"scrape_date={self.current_time_utc.strftime('%Y-%m-%d')}/company={self.greenhouse_company_name}"

    def _get_uri_params(self):
        params = {}
        params["source"] = self.settings["SOURCE"]
        params["bot_name"] = self.settings["BOT_NAME"]
        params["partitions"] = self.determine_partitions()
        params["file_name"] = f"{self.greenhouse_company_name}-{self.allowed_domains[0].split('.')[1]}.html"

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

    def finalize_response(self, response):
        if self.html_file != "":
            self.created_at = self.html_file["LastModified"].timestamp()
            return self.html_file["Body"].read()
        else:
            self.export_html(response.text)
            return response.text

    def parse(self, response):
        response_html = self.finalize_response(response)
        selector = Selector(text=response_html, type="html")
        filename = f'{self.greenhouse_company_name}-{self.allowed_domains[0].split(".")[1]}.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {filename}')