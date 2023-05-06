import os
import sys
import logging
import psycopg2
from job_board_scraper.utils.postgres_wrapper import PostgresWrapper

logger = logging.getLogger("ComparisonLogger")
time_to_check = sys.argv[1]
connection = psycopg2.connect(host=os.environ.get("PG_HOST"), user=os.environ.get("PG_USER"), password=os.environ.get("PG_PASSWORD"), dbname=os.environ.get("PG_DATABASE"))
cursor = connection.cursor()
cursor.execute(os.environ.get("COMPARISON_QUERY_EXPECTED"))
num_expected = cursor.fetchall()[0]
cursor.execute(os.environ.get("COMPARISON_QUERY_ACTUAL"), tuple([time_to_check, time_to_check]))
num_actual = cursor.fetchall()[0]
logger.info(f"Num Expected to Scrape: {num_expected}")
logger.info(f"Num Actually to Scraped: {num_actual}")

if num_expected != num_actual:
    cursor.execute(os.environ.get("MISMATCHED_URL_QUERY"), tuple([time_to_check, time_to_check]))
    logger.info(f"Mismatched URLs: {cursor.fetchall()}")
cursor.close()
connection.close()
assert num_expected == num_actual
