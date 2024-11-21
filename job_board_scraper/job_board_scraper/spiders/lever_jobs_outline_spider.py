import scrapy
import time
import boto3
import os
from dotenv import load_dotenv
from job_board_scraper.spiders.greenhouse_jobs_outline_spider import GreenhouseJobsOutlineSpider
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
    allowed_domains = ["jobs.lever.co", "lever.co"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spider_id = kwargs.pop("spider_id", 3)
        self.start_urls = [self.careers_page_url]
        self.logger.info(f"Initialized Spider with URL: {self.start_urls[0]}")

    def start_requests(self):
        self.logger.info(f"Starting requests with URLs: {self.start_urls}")
        for url in self.start_urls:
            self.logger.info(f"Making request to: {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_httpbin,
                dont_filter=True,
                meta={'dont_retry': True}
            )

    def parse(self, response):
        try:
            self.logger.info(f"Parsing response from URL: {response.url}")
            response_html = self.finalize_response(response)
            self.logger.debug(f"Response HTML length: {len(response_html)}")
            if 'postings-group' not in response_html:
                self.logger.warning("No 'postings-group' found in the response HTML.")
            selector = Selector(text=response_html, type="html")
            postings_groups = selector.xpath('//div[@class="postings-group"]')
            self.logger.info(f"Found {len(postings_groups)} postings groups.")

            for i, postings_group in enumerate(postings_groups):
                try:
                    stratified_selector = Selector(text=postings_group.get(), type="html")
                    
                    potential_primary_department = stratified_selector.xpath(
                        "//div[contains(@class, 'large-category-header')]/text()"
                    )
                    label_department = stratified_selector.xpath(
                        "//div[contains(@class, 'large-category-label')]/text()"
                    )
                    
                    # Initialize variables
                    secondary_string = None
                    primary_department = None
                    departments = None
                    
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
                    self.logger.info(f"Found {len(job_openings)} job openings in group {i}.")

                    for j, opening in enumerate(job_openings):
                        try:
                            il = ItemLoader(
                                item=LeverJobsOutlineItem(),
                                selector=Selector(text=opening.get(), type="html"),
                            )
                            
                            # Add fields with logging
                            self.logger.debug(f"Processing opening {j} with text: {opening.get()}")
                            
                            il.add_value("department_names", departments)
                            il.add_xpath("opening_link", './/div[@class="posting-apply"]/a/@href')
                            il.add_xpath("opening_title", './/h5[@data-qa="posting-name"]/text()')
                            il.add_xpath(
                                "workplace_type", 
                                './/span[contains(@class, "workplaceTypes")]/text()'
                            )
                            il.add_xpath("location", './/span[contains(@class, "location")]/text()')
                            
                            # Add required fields
                            row_id = self.determine_row_id(i * 1000 + j)
                            self.logger.debug(f"Generated row_id: {row_id}")
                            il.add_value("id", row_id)
                            il.add_value("created_at", self.created_at)
                            il.add_value("updated_at", self.updated_at)
                            il.add_value("source", self.html_source)
                            il.add_value("company_name", self.company_name)
                            il.add_value("run_hash", self.run_hash)
                            il.add_value("raw_html_file_location", self.full_s3_html_path)
                            il.add_value("existing_html_used", self.existing_html_used)
                            
                            item = il.load_item()
                            self.logger.info(f"Created item with fields: {dict(item)}")
                            if not any(item.values()):
                                self.logger.warning(f"Item has no values: {dict(item)}")
                                continue
                            yield item
                            self.logger.info(f"Successfully yielded item for opening {j}")
                            
                        except Exception as e:
                            self.logger.error(f"Error processing opening {j}: {e}")
                            self.logger.error(f"Opening HTML: {opening.get()}")
                            
                except Exception as e:
                    self.logger.error(f"Error processing postings group {i}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in parse method: {e}", exc_info=True)

    def errback_httpbin(self, failure):
        self.logger.error(f"Request failed: {failure.value}")
