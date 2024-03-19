import requests

import polars as pl
import json
from msgspec.json import decode
from utils.rippling.classes import JobOutline


def call_rippling_job_board_api(board_token, include_compensation=False):
    headers = {
        "Content-Type": "application/json",
    }

    rippling_job_board_endpoint = (
        f"https://api.rippling.com/platform/api/ats/v1/board/{board_token}/jobs"
    )

    response = requests.get(rippling_job_board_endpoint, headers=headers)

    result_json = response.json()

    return result_json, rippling_job_board_endpoint


def create_rippling_dataframes(jobs_outline_json, board_token, run_hash, source):
    jobs_outline_data = decode(json.dumps(jobs_outline_json), type=list[JobOutline])

    all_job_outlines_json = parse_jobs_outline_json(
        jobs_outline_data, board_token, run_hash, source
    )

    job_outline_df = (
        pl.DataFrame(all_job_outlines_json)
        .groupby([key for key in all_job_outlines_json[0].keys() if key != "location"])
        .agg(pl.col("location").str.concat(", "))
    )

    return [job_outline_df]


def parse_jobs_outline_json(data, board_token, run_hash, source="local"):
    all_job_outlines_json = []
    for i, job_outline in enumerate(data):
        job_outline_json_record = {}
        job_outline_json_record["job_id"] = job_outline.uuid
        job_outline_json_record["title"] = job_outline.name
        job_outline_json_record["department"] = job_outline.department.label
        job_outline_json_record["location"] = job_outline.workLocation.label
        job_outline_json_record["url"] = job_outline.url
        job_outline_json_record["board_token"] = board_token
        job_outline_json_record["run_hash"] = run_hash
        job_outline_json_record["api_endpoint"] = source

        all_job_outlines_json.append(job_outline_json_record)

    return all_job_outlines_json
