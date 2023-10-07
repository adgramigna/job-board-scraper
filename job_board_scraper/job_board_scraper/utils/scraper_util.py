import os
import sys
from dotenv import load_dotenv
load_dotenv()

def parse_args():
    try:
        id_lower_bound = int(sys.argv[1])
        id_upper_bound = int(sys.argv[2])
        id_restriction = f""" and {os.environ.get("ID_COL")} >= %s and {os.environ.get("ID_COL")} < %s"""
        id_values = tuple([id_lower_bound, id_upper_bound])
    except:
        id_restriction = ""
        id_values = tuple()
    return id_restriction, id_values