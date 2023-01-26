# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Compose
from w3lib.html import remove_tags

def get_boxscore_id(link):
    return link.split("/")[2].split(".")

def get_pfr_team_id(link):
    return link.split("/")[2]

class JobsOutlineItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field(output_processor=TakeFirst())
    created_at = scrapy.Field(output_processor=TakeFirst())
    updated_at = scrapy.Field(output_processor=TakeFirst())
    source = scrapy.Field(output_processor=TakeFirst())
    main_department = scrapy.Field(output_processor=TakeFirst())
    secondary_department = scrapy.Field(output_processor=TakeFirst())
    job_title = scrapy.Field(output_processor=TakeFirst())
    greenhouse_company_name = scrapy.Field(output_processor=TakeFirst())
    department_id = scrapy.Field(output_processor=TakeFirst())