# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from job_board_scraper.utils import pipline_util

from io import BytesIO
from dotenv import load_dotenv
from botocore.exceptions import ClientError

import os
import boto3
import logging
import psycopg2

logger = logging.getLogger("logger")

class JobScraperPipelinePostgres:
    def __init__(self):
        ## Connection Details
        self.hostname = os.environ.get("PG_HOST")
        self.username = os.environ.get("PG_USER")
        self.password = os.environ.get("PG_PASSWORD")
        self.database = os.environ.get("PG_DATABASE")

        ## Create/Connect to database
        self.connection = psycopg2.connect(host=self.hostname, user=self.username, password=self.password, dbname=self.database)
        
        ## Create cursor, used to execute commands
        self.cur = self.connection.cursor()

    def open_spider(self, spider):
        self.table_name = spider.name
        initial_table_schema = pipline_util.set_initial_table_schema(self.table_name)
        create_table_statement = pipline_util.create_table_schema(self.table_name, initial_table_schema)
        self.cur.execute(create_table_statement)
    
    def process_item(self, item, spider):
         ## Execute insert of data into database
        insert_item_statement, table_values_list = pipline_util.create_insert_item(self.table_name, item)
        # logger.info(f"INSERT STMT {insert_item_statement} ____ {table_values_list}")
        self.cur.execute(insert_item_statement, tuple(table_values_list))
        self.connection.commit()
        return item

    def close_spider(self, spider):
        ## Close cursor & connection to database 
        self.cur.close()
        self.connection.close()