from hashids import Hashids
import os
from dotenv import load_dotenv

load_dotenv()

hash_ids = Hashids(
    salt=os.environ.get("HASHIDS_SALT"), alphabet="abcdefghijklmnopqrstuvwxyz1234567890"
)
