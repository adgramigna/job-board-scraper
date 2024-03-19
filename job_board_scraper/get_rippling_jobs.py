import time
import logging
import sys
import utils.general as general_util
import utils.export as export_util
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")

job_board_provider = sys.argv[1]

start = time.time()
run_hash = general_util.hash_ids.encode(int(start))

board_tokens = general_util.setup_postgres_connection(job_board_provider)
for board_token in board_tokens:

    logger.info(f"{board_token}, {time.time() - start}")
    start = time.time()

    if not general_util.initial_error_check(board_token, job_board_provider):
        jobs_outline_json, source = general_util.job_board_api_factory(
            board_token, job_board_provider
        )
    else:
        continue

    dfs = general_util.create_dataframes_factory(
        job_board_provider, jobs_outline_json, board_token, run_hash, source
    )

    table_names = export_util.determine_table_names(job_board_provider)

    table_pairs_dict = dict(zip(table_names, dfs))

    export_util.export_dataframes_to_postgres(table_pairs_dict)
