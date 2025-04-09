"""
This script deletes data from Postgres and uploads to S3. This is done so we
can remain in Neon's free tier. I choose to keep data from the most recent week
so the active job postings can still have a week's worth of data, potentially.
"""

import psycopg2
import os
import s3fs
import polars as pl
import logging
from datetime import datetime, timedelta
from psycopg2.sql import SQL, Identifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")

today_date = datetime.now()
today_str = str(today_date)
one_week_ago = str(today_date - timedelta(days=7))
one_week_ago_unix = int(
    datetime.strptime(one_week_ago, "%Y-%m-%d %H:%M:%S.%f").timestamp()
)


table_names = [
    "greenhouse_job_departments",
    "greenhouse_jobs_outline",
    "lever_jobs_outline",
    "rippling_jobs_outline",
    "ashby_jobs_outline",
    "ashby_job_departments",
    "ashby_job_locations",
]


pg_host = os.environ.get("PG_HOST")
pg_user = os.environ.get("PG_USER")
pg_pw = os.environ.get("PG_PASSWORD")
pg_db = os.environ.get("PG_DATABASE")

connection_string = f"postgresql://{pg_user}:{pg_pw}@{pg_host}/{pg_db}"

connection = psycopg2.connect(
    host=pg_host,
    user=pg_user,
    password=pg_pw,
    dbname=pg_db,
)
cursor = connection.cursor()

fs = s3fs.S3FileSystem()

for table in table_names:
    query = SQL(os.environ.get("SELECT_TABLES_TO_UPLOAD_QUERY")).format(
        table=Identifier(table)
    )
    if table != "rippling_jobs_outline":
        cursor.execute(query, {"one_week_ago": one_week_ago_unix})
    else:
        cursor.execute(query, {"one_week_ago": one_week_ago})
    # Fetch all rows from the cursor
    rows = cursor.fetchall()

    # Get column names from cursor description
    column_names = [desc[0] for desc in cursor.description]

    # Convert to polars DataFrame
    df = pl.DataFrame(rows, schema=column_names)

    # Write parquet
    destination = f"s3://{os.environ.get('S3_BUCKET')}/postgres-export/{today_date}/{table}.parquet"
    with fs.open(destination, mode="wb") as f:
        df.write_parquet(f)

    logging.info(f"Exported {table}")

connection.close()
