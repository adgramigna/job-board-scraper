import scrapy
# import logging
import time

import boto3
import os
from dotenv import load_dotenv
from greenhouse_scraper.items import JobsOutlineItem
from greenhouse_scraper.utils import general as util
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
    
    def determine_row_id(self, i):
        return util.hash_ids.encode(
            self.spider_id,
            i,
            self.current_time
        )

    def finalize_response(self, response):
        if self.html_file != "":
            self.created_at = self.html_file["LastModified"].timestamp()
            return self.html_file["Body"].read()
        else:
            # self.export_html(response.text)
            return response.text

    def parse(self, response):
        response_html = self.finalize_response(response)
        selector = Selector(text=response_html, type="html")
        all_departments = selector.xpath('//section[contains(@class, "level")]')
        main_departments = selector.xpath('//section[contains(@class, "level-0")]')
        secondary_departments = selector.xpath('//section[contains(@class, "level-1")]')
        job_openings = selector.xpath('//div[@class="opening"]')

        for i, department in enumerate(main_departments):
            il = ItemLoader(item=JobsOutlineItem(), selector=department)
            self.logger.info(f"Parsing row {i+1}, {self.greenhouse_company_name}")
            # main_department_text = department.xpath(f'//section[contains(@class, "level-0")][{i+1}]/*[self::h1 or self::h2 or self::h3 or self::h4]/text()')
            dep_xpath = f"//section[contains(@class, 'level-0')][{i+1}]/*[self::h1 or self::h2 or self::h3 or self::h4]/text()"
            il.replace_xpath(
                "main_department",
                dep_xpath
            )
            secondary_departments = department.xpath(f'//section[contains(@class, "level-0")][{i+1}]//section[contains(@class, "level-1")]')
            # self.logger.info(f"{dep_xpath} Department here")
  
            job_openings = department.xpath(f'//section[contains(@class, "level-0")][{i+1}]/div[@class="opening"]')
            for k, opening in enumerate(job_openings):
                    job_xpath = f'//section[contains(@class, "level-0")][{i+1}]/div[@class="opening"][{k+1}]/a/text()'
                    dep_id_xpath = f'//section[contains(@class, "level-0")][{i+1}]/div[{k+1}]/@department_id'
                    il.replace_xpath(
                        "job_title",
                        job_xpath
                    )
                    il.replace_xpath(
                        "department_id",
                        dep_id_xpath
                    )
                    # self.logger.info(f'{i} {j} {k} {job_xpath} xpth')
                    yield il.load_item()
                    
            if len(secondary_departments) == 0:
                il.add_value(
                    "secondary_department",
                    None
                )
            else:
                for j, sec_department in enumerate(secondary_departments):
                    sec_dep_xpath = f"//section[contains(@class, 'level-0')][{i+1}]//section[contains(@class, 'level-1')][{j+1}]/*[self::h1 or self::h2 or self::h3 or self::h4]/text()"
                    il.replace_xpath(
                        "secondary_department",
                        sec_dep_xpath
                    )
                # self.logger.info(f"{sec_dep_xpath} sec Department here")
                    job_openings = sec_department.xpath(f'//section[contains(@class, "level-0")][{i+1}]//section[contains(@class, "level-1")][{j+1}]/div[@class="opening"]')
                    for k, opening in enumerate(job_openings):
                        job_xpath = f'//section[contains(@class, "level-0")][{i+1}]/section[contains(@class, "level-1")][{j+1}]/div[@class="opening"][{k+1}]/a/text()'
                        dep_id_xpath = f'//section[contains(@class, "level-0")][{i+1}]/section[contains(@class, "level-1")][{j+1}]/div[{k+1}]/@department_id'
                        il.replace_xpath(
                            "job_title",
                            job_xpath
                        )
                        il.replace_xpath(
                            "department_id",
                            dep_id_xpath
                        )
                        # self.logger.info(f'{i} {j} {k} {job_xpath} xpth')
                        yield il.load_item()
   
        # filename = f'{self.greenhouse_company_name}-{self.allowed_domains[0].split(".")[1]}.html'
        # with open(filename, 'wb') as f:
        #     f.write(response.body)
        # self.log(f'Saved file {filename}')