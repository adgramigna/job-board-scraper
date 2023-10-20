# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Compose
from w3lib.html import remove_tags


def get_last_word(class_name):
    return class_name.split()[-1]


class LevergreenScrapyItem(scrapy.Item):
    id = scrapy.Field(output_processor=TakeFirst())
    created_at = scrapy.Field(output_processor=TakeFirst())
    updated_at = scrapy.Field(output_processor=TakeFirst())
    source = scrapy.Field(output_processor=TakeFirst())
    run_hash = scrapy.Field(output_processor=TakeFirst())
    existing_html_used = scrapy.Field(output_processor=TakeFirst())
    raw_html_file_location = scrapy.Field(output_processor=TakeFirst())


class GreenhouseJobsOutlineItem(LevergreenScrapyItem):
    # define the fields for your item here like:
    department_ids = scrapy.Field(output_processor=TakeFirst())
    office_ids = scrapy.Field(output_processor=TakeFirst())
    opening_title = scrapy.Field(output_processor=TakeFirst())
    opening_link = scrapy.Field(output_processor=TakeFirst())
    location = scrapy.Field(output_processor=TakeFirst())


class LeverJobsOutlineItem(LevergreenScrapyItem):
    # define the fields for your item here like:
    department_names = scrapy.Field(output_processor=TakeFirst())
    workplace_type = scrapy.Field(output_processor=TakeFirst())
    opening_title = scrapy.Field(output_processor=TakeFirst())
    opening_link = scrapy.Field(output_processor=TakeFirst())
    location = scrapy.Field(output_processor=TakeFirst())
    company_name = scrapy.Field(output_processor=TakeFirst())


class GreenhouseJobDepartmentsItem(LevergreenScrapyItem):
    # define the fields for your item here like:
    company_name = scrapy.Field(output_processor=TakeFirst())
    department_id = scrapy.Field(output_processor=TakeFirst())
    department_name = scrapy.Field(output_processor=TakeFirst())
    department_category = scrapy.Field(
        input_processor=MapCompose(get_last_word), output_processor=TakeFirst()
    )
