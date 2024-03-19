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

    all_job_outlines_json, all_job_locations_json = parse_jobs_outline_json(
        jobs_outline_data, board_token, run_hash, source
    )

    job_outline_df = pl.DataFrame(all_job_outlines_json).with_columns(
        pl.col("rippling_published_at").dt.replace_time_zone("UTC")
    )

    job_location_df = pl.DataFrame(all_job_locations_json)
    if len(job_location_df) > 0:
        job_location_df = job_location_df.with_columns(
            pl.col("placement").cast(pl.Int16)
        )

    return [job_outline_df, job_location_df]


def parse_jobs_outline_json(data, board_token, run_hash, source="local"):
    all_job_outlines_json = []
    all_job_locations_json = []
    for i, job_outline in enumerate(data):
        job_outline_json_record = {}
        job_outline_json_record["job_id"] = job_outline.id
        job_outline_json_record["title"] = job_outline.title
        job_outline_json_record["department"] = job_outline.department
        job_outline_json_record["team"] = job_outline.team
        job_outline_json_record["employment_type"] = job_outline.employmentType
        job_outline_json_record["location"] = job_outline.location
        job_outline_json_record["rippling_published_at"] = job_outline.publishedAt
        job_outline_json_record["is_listed"] = job_outline.isListed
        job_outline_json_record["is_remote"] = job_outline.isRemote
        job_outline_json_record["job_url"] = job_outline.jobUrl
        job_outline_json_record["description_plain"] = job_outline.descriptionPlain

        try:
            job_outline_json_record["address_region"] = (
                job_outline.address.postalAddress.addressRegion
            )
            job_outline_json_record["address_country"] = (
                job_outline.address.postalAddress.addressCountry
            )
            job_outline_json_record["address_locality"] = (
                job_outline.address.postalAddress.addressLocality
            )
        except AttributeError:
            job_outline_json_record["address_region"] = None
            job_outline_json_record["address_country"] = None
            job_outline_json_record["address_locality"] = None

        all_locations = job_outline.location
        for secondary_location in job_outline.secondaryLocations:
            all_locations = all_locations + ", " + secondary_location.location

        job_outline_json_record["all_locations"] = all_locations

        job_outline_json_record["board_token"] = board_token
        job_outline_json_record["run_hash"] = run_hash
        job_outline_json_record["api_endpoint"] = source

        all_job_outlines_json.append(job_outline_json_record)

        for j, secondary_location in enumerate(job_outline.secondaryLocations):
            job_location_json_record = {}
            job_location_json_record["job_id"] = job_outline.id
            job_location_json_record["placement"] = j + 1
            job_location_json_record["location_name"] = secondary_location.location
            job_location_json_record["address_region"] = (
                secondary_location.address.postalAddress.addressRegion
            )
            job_location_json_record["address_country"] = (
                secondary_location.address.postalAddress.addressCountry
            )
            job_location_json_record["address_locality"] = (
                secondary_location.address.postalAddress.addressLocality
            )
            job_location_json_record["board_token"] = board_token
            job_location_json_record["run_hash"] = run_hash
            job_location_json_record["api_endpoint"] = source
            all_job_locations_json.append(job_location_json_record)

    return all_job_outlines_json, all_job_locations_json
