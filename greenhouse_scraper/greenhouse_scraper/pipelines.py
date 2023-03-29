# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from greenhouse_scraper.exporters import ParquetItemExporter

from io import BytesIO
from dotenv import load_dotenv
from botocore.exceptions import ClientError

import os
import boto3
import logging


class GreenhouseScraperPipelineParquet:
    def __init__(self, settings):
        load_dotenv()
        self.bucket_name = settings["S3_BUCKET"]
        self.object_key_template = settings["S3_PATH"]
        self.bot_name = settings["BOT_NAME"]
        self.sse = settings["SERVER_SIDE_ENCRYPTION"]
        self.client = boto3.client(
            "s3",
            region_name=settings["AWS_REGION_NAME"],
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

    @classmethod
    def from_crawler(cls, crawler):
        cls.set_logging()
        return cls(crawler.settings)

    def set_logging():
        logging.getLogger("boto3").setLevel(logging.INFO)
        logging.getLogger("botocore").setLevel(logging.INFO)
        logging.getLogger("s3transfer").setLevel(logging.INFO)
        logging.getLogger("scrapy").setLevel(logging.INFO)
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)
        logging.getLogger("scrapy-playwright").setLevel(logging.INFO)

    def determine_partitions(self, spider):
        if spider.name in ["job_departments", "jobs_outline"]:
            return f"date={spider.current_date_utc}/company={spider.greenhouse_company_name}"

    def _get_uri_params(self):
        params = {}
        params["bot_name"] = self.bot_name
        params["spider_name"] = self.spider.name
        params["partitions"] = self.determine_partitions(self.spider)
        params["file_name"] = "data.parquet"

        return params

    def upload_fileobj_s3(self, f, bucket_name, object_key):
        try:
            self.client.upload_fileobj(f, bucket_name, object_key)
        except ClientError as ex:
            pass

    def open_spider(self, spider):
        self.spider = spider
        self.file = BytesIO()
        self.exporter = ParquetItemExporter(self.file, export_empty_fields=True)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.seek(0)
        self.object_key = self.object_key_template.format(**self._get_uri_params())
        self.upload_fileobj_s3(self.file, self.bucket_name, self.object_key)
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
