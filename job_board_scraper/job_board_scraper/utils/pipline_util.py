def set_initial_table_schema(spider_name):
    ## Set Initial table schema, columns present in all tables
    return f"""CREATE TABLE IF NOT EXISTS {spider_name} ( 
        id serial PRIMARY KEY
        , levergreen_id text
        , created_at bigint
        , updated_at bigint
        , source text
        , run_hash text
        , raw_html_file_location text
        , existing_html_used int
    """

def create_table_schema(table_name, initial_table_schema = ""):
    if table_name == "greenhouse_job_departments":
        return initial_table_schema + """, company_name text
            , department_category text
            , department_id text
            , department_name text
        )
        """
    elif table_name == "greenhouse_jobs_outline":
        return initial_table_schema + """, department_ids text
            , location text
            , office_ids text
            , opening_link text
            , opening_title text
        )
        """
    elif table_name == "lever_jobs_outline":
        return initial_table_schema + """, company_name text
            , department_names text
            , location text
            , opening_link text
            , opening_title text
            , workplace_type text
        )
        """
    else:
        return initial_table_schema

def finalize_value(item, value):
    try:
        return item[value]
    except:
        return None

def get_table_columns(table_name):
    initial_columns = """(levergreen_id, created_at, updated_at, source, run_hash, raw_html_file_location, existing_html_used"""
    if table_name == "greenhouse_job_departments":
        return initial_columns + """, company_name, department_category, department_id, department_name)"""
    elif table_name == "greenhouse_jobs_outline":
        return initial_columns + """, department_ids, location, office_ids, opening_link, opening_title)"""
    elif table_name == "lever_jobs_outline":
        return initial_columns + """, company_name, department_names, location, opening_link, opening_title, workplace_type)"""
    else:
        return initial_columns + """)""" 

def get_table_values(table_name, item):
    initial_percent_s = """(%s, %s, %s, %s, %s, %s, %s"""
    initial_values = [finalize_value(item, "id"), finalize_value(item, "created_at"), finalize_value(item, "updated_at"), finalize_value(item, "source"), finalize_value(item, "run_hash"), finalize_value(item, "raw_html_file_location"), finalize_value(item, "existing_html_used")]
    if table_name == "greenhouse_job_departments":
        return initial_percent_s + """, %s, %s, %s, %s)""", initial_values + [finalize_value(item, "company_name"), finalize_value(item, "department_category"), finalize_value(item, "department_id"), finalize_value(item, "department_name")]
    elif table_name == "greenhouse_jobs_outline":
        return initial_percent_s + """, %s, %s, %s, %s, %s)""", initial_values + [finalize_value(item, "department_ids"), finalize_value(item, "location"), finalize_value(item, "office_ids"), finalize_value(item, "opening_link"), finalize_value(item, "opening_title")]
    elif table_name == "lever_jobs_outline":
        return initial_percent_s + """, %s, %s, %s, %s, %s, %s)""", initial_values + [finalize_value(item, "company_name"), finalize_value(item, "department_names"), finalize_value(item, "location"), finalize_value(item, "opening_link"), finalize_value(item, "opening_title"), finalize_value(item, "workplace_type")]
    else:
        return initial_percent_s + """)""", initial_values

def create_insert_item(table_name, item):
    table_columns = get_table_columns(table_name)
    percent_s, table_values = get_table_values(table_name, item)
    return f"""insert into {table_name} {table_columns} values {percent_s}""", table_values

