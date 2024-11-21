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
from psycopg2 import pool

logger = logging.getLogger("logger")


class JobScraperPipelinePostgres:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing JobScraperPipelinePostgres")
        
        # Log environment variables (excluding sensitive info)
        self.hostname = os.getenv("PG_HOST")
        self.username = os.getenv("PG_USER")
        self.database = os.getenv("PG_DATABASE")
        self.port = os.getenv("PG_PORT", "5432")
        
        self.logger.info(f"Database config: host={self.hostname}, db={self.database}, port={self.port}")
        
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 20,
                host=self.hostname,
                user=self.username,
                password=os.getenv("PG_PASSWORD"),
                dbname=self.database,
                port=self.port
            )
            self.logger.info("Successfully created database connection pool")
        except Exception as e:
            self.logger.error(f"Failed to create connection pool: {e}")
            raise

    def open_spider(self, spider):
        self.logger.info(f"Opening spider {spider.name}")
        self.table_name = spider.name
        self.logger.info(f"Using table name: {self.table_name}")
        
        # Create table if it doesn't exist
        initial_table_schema = pipline_util.set_initial_table_schema(self.table_name)
        create_table_statement = pipline_util.create_table_schema(
            self.table_name, initial_table_schema
        )
        
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                self.logger.info(f"Creating table with statement: {create_table_statement}")
                cur.execute(create_table_statement)
                conn.commit()
                self.logger.info(f"Successfully created/verified table {self.table_name}")
        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def process_item(self, item, spider):
        self.logger.info(f"Processing item in pipeline for spider {spider.name}")
        if not item:
            self.logger.error("Received empty item")
            return item
        
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                insert_item_statement, table_values_list = pipline_util.create_insert_item(
                    self.table_name, item
                )
                self.logger.info(f"Attempting to execute SQL: {insert_item_statement}")
                self.logger.info(f"With values: {table_values_list}")
                
                if not table_values_list:
                    self.logger.error("No values to insert")
                    return item
                    
                cur.execute(insert_item_statement, tuple(table_values_list))
                conn.commit()
                self.logger.info(f"Successfully inserted item into {self.table_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to insert item: {str(e)}")
            self.logger.error(f"Item contents: {dict(item)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.connection_pool.putconn(conn)
        
        return item

    def close_spider(self, spider):
        try:
            self.connection_pool.closeall()
            self.logger.info("PostgreSQL connection pool closed.")
        except Exception as e:
            self.logger.error(f"Error closing connection pool: {e}")

    def export_html(self, item):
        try:
            html_content = item.get('html_content')
            url = item.get('url')
            if html_content and url:
                object_key = f"html/{self._generate_object_key(url)}.html"
                self.s3_client.put_object(
                    Bucket=self.raw_html_s3_bucket,
                    Key=object_key,
                    Body=html_content.encode('utf-8'),
                    ContentType='text/html'
                )
                logging.info(f"Exported HTML to s3://{self.raw_html_s3_bucket}/{object_key}")
        except Exception as e:
            logging.error(f"Failed to export HTML to S3: {e}")

    def _generate_object_key(self, url):
        return url.replace("https://", "").replace("/", "_")
