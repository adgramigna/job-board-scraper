import os
import sys
import logging
from job_board_scraper.utils.postgres_wrapper import PostgresWrapper

logger = logging.getLogger("ComparisonLogger")
time_to_check = sys.argv[1]
pg_wrapper = PostgresWrapper()
connection = pg_wrapper.connection()
cursor = connection.cursor()
cursor.execute(os.environ.get("COMPARISON_QUERY_EXPECTED"))
num_expected = cursor.fetchall()[0]
cursor.close()
connection.close()

cursor.execute(os.environ.get("COMPARISON_QUERY_ACTUAL"), tuple([time_to_check, time_to_check]))
num_actual = cursor.fetchall()[0]
logger.info(f"Num Expected to Scrape: {num_expected}")
logger.info(f"Num Actually to Scraped: {num_actual}")

if num_expected != num_actual:
    cursor.execute(os.environ.get("MISMATCHED_URL_QUERY"), tuple([time_to_check, time_to_check]))
    logger.info(f"Mismatched URLs: {cursor.fetchall()}")
assert num_expected == num_actual
