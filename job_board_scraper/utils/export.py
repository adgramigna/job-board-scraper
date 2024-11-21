import os
from dotenv import load_dotenv

load_dotenv()

pg_user = os.getenv("PG_USER")
pg_password = os.getenv("PG_PASSWORD")
pg_host = os.getenv("PG_HOST")
pg_database = os.getenv("PG_DATABASE")
pg_port = os.getenv("PG_PORT")

connection_string = (
    f"postgresql://{pg_user}:{pg_password}@{pg_host}/{pg_database}?sslmode=require"
)


def export_table_to_postgres(df, table_name):
    df.write_database(
        table_name=table_name,
        connection=connection_string,
        if_exists="append",
        engine="adbc",
    )


def determine_table_names(job_board_provider):
    if job_board_provider == "rippling":
        return [os.getenv("RIPPLING_JOBS_OUTLINE_TABLE_NAME")]


def export_dataframes_to_postgres(table_pairs_dict):
    for key, value in table_pairs_dict.items():
        if len(value) != 0:
            export_table_to_postgres(df=value, table_name=key)
