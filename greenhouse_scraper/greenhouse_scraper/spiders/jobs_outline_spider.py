import scrapy
# import logging
import time

import boto3
import os
from dotenv import load_dotenv
from greenhouse_scraper.items import JobsOutlineItem
from greenhouse_scraper.utils import general as util
from greenhouse_scraper.spiders.job_departments_spider import JobDepartmentsSpider
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

class JobsOutlineSpider(JobDepartmentsSpider):
    name = "jobs_outline"
    allowed_domains = ["boards.greenhouse.io"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 1)
        self.use_existing_html = kwargs.pop("use_existing_html", 1) #from departments
        self.logger.info(f"Initialized Spider, {self.html_source}")
    
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