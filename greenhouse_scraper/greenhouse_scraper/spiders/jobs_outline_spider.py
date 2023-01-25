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

load_dotenv()
# logger = logging.getLogger("mylogger")


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
        # logger.info("Initialized Spider")


    # @property
    # def url(self):
    #     if self.html_file == "":
    #         return self.html_source
    #     else:
    #         return self.settings["DEFAULT_HTML"]
    
    @property
    def url(self):
        return self.html_source

    def start_requests(self):
        yield scrapy.Request(url=self.url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-1]
        filename = f'{page}-{self.allowed_domains[0].split(".")[1]}.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {filename}')