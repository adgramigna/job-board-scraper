import duckdb
import json
import polars as pl
import requests
import logging
import time
import os
import psycopg2
from msgspec.json import decode
from msgspec import Struct
from typing import Optional
from datetime import datetime
from job_board_scraper.utils import general as util


def determine_row_id(spider_id, url_id, row_id, created_at, k=0):
    return util.hash_ids.encode(spider_id, url_id, row_id, created_at, k)


def set_initial_table_schema(table_name):
    ## Set Initial table schema, columns present in all tables
    return f"""CREATE TABLE IF NOT EXISTS {table_name} ( 
        id serial PRIMARY KEY
        , levergreen_id text
        , created_at bigint
        , updated_at bigint
        , company_name text
        , ashby_job_board_source text
        , run_hash text
        , raw_json_file_location text
        , existing_json_used boolean
    """


def create_table_schema(table_name, initial_table_schema=""):
    if table_name == "ashby_job_locations":
        return (
            initial_table_schema
            + """, opening_id uuid
            , secondary_location_id uuid
            , secondary_location_name text
        )
        """
        )
    elif table_name == "ashby_job_departments":
        return (
            initial_table_schema
            + """, department_id uuid
            , department_name text
            , parent_department_id uuid
        )
        """
        )
    elif table_name == "ashby_jobs_outline":
        return (
            initial_table_schema
            + """, opening_id uuid
            , opening_name text
            , department_id uuid
            , location_id uuid
            , location_name text
            , employment_type text
            , compensation_tier text
            , opening_link text
        )
        """
        )
    else:
        return initial_table_schema


def finalize_table_schema(table_name):
    initial_table_schema = set_initial_table_schema(table_name)
    return create_table_schema(table_name, initial_table_schema)


class SecondaryLocation(Struct):
    locationId: str
    locationName: str


class Posting(Struct):
    id: str
    title: str
    teamId: str
    locationId: str
    locationName: str
    employmentType: str
    compensationTierSummary: Optional[str]
    secondaryLocations: Optional[list[SecondaryLocation]]


class Team(Struct):
    id: str
    name: str
    parentTeamId: Optional[str]


logger = logging.getLogger("ashby_logger")
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
logger.addHandler(console)

ashby_teams_id = 3
ashby_postings_id = 4
ashby_locations_id = 5

run_hash = util.hash_ids.encode(int(time.time()))

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
cursor.execute(finalize_table_schema("ashby_jobs_outline"))
cursor.execute(finalize_table_schema("ashby_job_departments"))
cursor.execute(finalize_table_schema("ashby_job_locations"))
connection.commit()
cursor.execute(os.environ.get("ASHBY_PAGES_TO_SCRAPE_QUERY"))
careers_page_urls = cursor.fetchall()
cursor.close()
connection.close()

con = duckdb.connect(database=":memory:")

ashby_api_endpoint = (
    "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
)

f = open("queries/ashby_jobs_outline.graphql")
query = f.read()

headers = {"Content-Type": "application/json"}
# careers_page_urls = [("https://jobs.ashbyhq.com/deel",)]
for i, url in enumerate(careers_page_urls):
    ashby_url = url[0]  # UnTuple-ify
    ashby_company = ashby_url.split("/")[-1]
    # ashby_company = '5'

    variables = {"organizationHostedJobsPageName": ashby_company}

    current_time = time.time()
    created_at = int(current_time)
    updated_at = int(current_time)
    current_date_utc = datetime.utcfromtimestamp(current_time).strftime("%Y-%m-%d")

    s3_json_path = f"requests/ashby/date={current_date_utc}/company={ashby_company}/{ashby_company}-ashby.json"
    full_s3_json_path = (
        "s3://" + os.environ.get("RAW_HTML_S3_BUCKET") + "/" + s3_json_path
    )
    ashby_job_board_source = f"https://jobs.ashbyhq.com/{ashby_company}"

    response = requests.request(
        "POST",
        ashby_api_endpoint,
        headers=headers,
        json={"query": query, "variables": variables},
    )

    response_text = response.text
    response_json = json.loads(response_text)
    if response_json["data"]["jobBoard"] == None:
        logger.error(f"No data for {ashby_company}")
    else:
        logger.info(f"Got data for {ashby_company}")

    try:
        posting_data = decode(
            json.dumps(response_json["data"]["jobBoard"]["jobPostings"]),
            type=list[Posting],
        )
    except TypeError as te:
        logger.error(
            f"An error occurred for company '{ashby_company}'. Perhaps you have the wrong Ashby company name"
        )

    # secondaryLocations list
    all_postings_json = []
    all_locations_json = []
    for j, record in enumerate(posting_data):
        try:
            for k, location in enumerate(record.secondaryLocations):
                location_json_record = {}
                location_json_record["levergreen_id"] = determine_row_id(
                    ashby_locations_id, i, j, created_at, k
                )
                location_json_record["opening_id"] = record.id
                location_json_record["secondary_location_id"] = location.locationId
                location_json_record["secondary_location_name"] = location.locationName
                all_locations_json.append(location_json_record)
        except:
            pass
        ashby_locations = pl.DataFrame(all_locations_json)
        if len(ashby_locations) > 0:
            ashby_locations_final = con.execute(
                """
                select *, 
                    ? as created_at,
                    ? as updated_at,
                    ? as company_name,
                    ? as ashby_job_board_source,
                    ? as run_hash,
                    false as existing_json_used,
                    null as raw_json_file_location,
                from ashby_locations
                """,
                [
                    created_at,
                    updated_at,
                    ashby_company,
                    ashby_job_board_source,
                    run_hash,
                ],
            ).pl()
        else:
            ashby_locations_final = ashby_locations.clone()

        # postings list
        posting_json_record = {}
        posting_json_record["levergreen_id"] = determine_row_id(
            ashby_postings_id, i, j, created_at
        )
        posting_json_record["opening_id"] = record.id
        posting_json_record["opening_name"] = record.title
        posting_json_record["department_id"] = record.teamId
        posting_json_record["location_id"] = record.locationId
        posting_json_record["location_name"] = record.locationName
        posting_json_record["employment_type"] = record.employmentType
        posting_json_record["compensation_tier"] = record.compensationTierSummary
        all_postings_json.append(posting_json_record)

    # DuckDB calls
    ashby_postings = pl.DataFrame(all_postings_json)

    if len(ashby_postings) > 0:
        ashby_postings_final = con.execute(
            """
        select *, 
            ? as s3_json_path,
            ? as created_at,
            ? as updated_at,
            ? as company_name,
            ? as ashby_job_board_source,
            ? as run_hash,
            ? || '/' || opening_id as opening_link,
            false as existing_json_used,
            null as raw_json_file_location,
        from ashby_postings
        """,
            [
                full_s3_json_path,
                created_at,
                updated_at,
                ashby_company,
                ashby_job_board_source,
                run_hash,
                ashby_job_board_source,
            ],
        ).pl()
    else:
        ashby_postings_final = ashby_postings.clone()

    try:
        team_data = decode(
            json.dumps(response_json["data"]["jobBoard"]["teams"]), type=list[Team]
        )
    except TypeError as te:
        logger.error(
            f"An error occurred for company '{ashby_company}'. Perhaps you have the wrong Ashby company name"
        )

    all_teams_json = []
    for j, record in enumerate(team_data):
        team_json_record = {}
        team_json_record["levergreen_id"] = determine_row_id(
            ashby_postings_id, i, j, created_at
        )
        team_json_record["department_id"] = record.id
        team_json_record["department_name"] = record.name
        team_json_record["parent_department_id"] = record.parentTeamId
        all_teams_json.append(team_json_record)

    ashby_departments = pl.DataFrame(all_teams_json)
    if len(ashby_departments) > 0:
        ashby_departments_final = con.execute(
            """
            select *, 
                ? as created_at,
                ? as updated_at,
                ? as company_name,
                ? as ashby_job_board_source,
                ? as run_hash,
                null as raw_json_file_location,
                false as existing_json_used,
            from ashby_departments
            """,
            [
                created_at,
                updated_at,
                ashby_company,
                ashby_job_board_source,
                run_hash,
            ],
        ).pl()
    else:
        ashby_departments_final = ashby_departments.clone()

    # Export to Postgres
    if len(ashby_postings_final) > 0:
        con.sql(
            """
                select
                    levergreen_id
                    , created_at
                    , updated_at
                    , company_name
                    , ashby_job_board_source
                    , run_hash
                    , raw_json_file_location
                    , existing_json_used
                    , opening_id
                    , opening_name
                    , department_id
                    , location_id
                    , location_name
                    , employment_type
                    , compensation_tier
                    , opening_link
                from ashby_postings_final
            """
        ).pl().write_database(
            "ashby_jobs_outline",
            connection_string,
            if_exists="append",
            engine="sqlalchemy",
        )

    if len(ashby_departments_final) > 0:
        con.sql(
            """
                select
                    levergreen_id
                    , created_at
                    , updated_at
                    , company_name
                    , ashby_job_board_source
                    , run_hash
                    , raw_json_file_location
                    , existing_json_used
                    , department_id
                    , department_name
                    , parent_department_id
                from ashby_departments_final
            """
        ).pl().write_database(
            "ashby_job_departments",
            connection_string,
            if_exists="append",
            engine="sqlalchemy",
        )
    if len(ashby_locations_final) > 0:
        con.sql(
            """
                select
                    levergreen_id
                    , created_at
                    , updated_at
                    , company_name
                    , ashby_job_board_source
                    , run_hash
                    , raw_json_file_location
                    , existing_json_used
                    , opening_id
                    , secondary_location_id
                    , secondary_location_name
                from ashby_locations_final
            """
        ).pl().write_database(
            "ashby_job_locations",
            connection_string,
            if_exists="append",
            engine="sqlalchemy",
        )

    # break


con.close()
