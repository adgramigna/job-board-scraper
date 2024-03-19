from hashids import Hashids
import os
import psycopg2
import logging
from utils.rippling.parsing_helper import (
    call_rippling_job_board_api,
    create_rippling_dataframes,
)
from json import JSONDecodeError
from urllib.error import HTTPError
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")

hash_ids = Hashids(
    salt=os.environ.get("HASHIDS_SALT"), alphabet="abcdefghijklmnopqrstuvwxyz1234567890"
)


def setup_postgres_connection(job_board_provider):
    conn = psycopg2.connect(
        host=os.environ.get("PG_HOST"),
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
        dbname=os.environ.get("PG_DATABASE"),
        port=os.environ.get("PG_PORT"),
    )

    cursor = conn.cursor()
    cursor.execute(
        os.environ.get("GET_BOARD_TOKENS_BASE_QUERY"), {"provider": job_board_provider}
    )
    conn.commit()

    board_tokens = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return board_tokens


def create_dataframes_factory(
    job_board_provider, jobs_outline_json, board_token, run_hash, source
):
    if job_board_provider == "rippling":
        return create_rippling_dataframes(
            jobs_outline_json, board_token, run_hash, source
        )


def job_board_api_factory(board_token, job_board):
    if job_board == "rippling":
        return call_rippling_job_board_api(board_token)


def initial_error_check(board_token, job_board):
    try:
        jobs_outline_json, source = job_board_api_factory(board_token, job_board)
    except (KeyError, TypeError, JSONDecodeError, HTTPError):
        logger.error(f"Bad Input for {board_token}")
        return True

    # No Jobs found
    if len(jobs_outline_json) == 0:
        logger.warning(f"No Jobs found for {board_token}")
        return True

    return False
