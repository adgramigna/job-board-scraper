def set_initial_table_schema(spider_name):
    ## Set Initial table schema, columns present in all tables
    return f"""CREATE TABLE IF NOT EXISTS {spider_name}( 
        id PRIMARY KEY
        , created_at bigint
        , updated_at bigint
        , source text
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

def get_table_columns(table_name):
    initial_columns = """(id, created_at, updated_at, source"""
    if table_name == "greenhouse_job_departments":
        return initial_columns + """, company_name, department_category, department_id, department_name)"""
    elif table_name == "greenhouse_jobs_outline":
        return initial_columns + """, department_ids, location, office_ids, opening_link, opening_title)"""
    elif table_name == "lever_jobs_outline":
        return initial_columns + """, company_name, department_names, location, opening_link, opening_title, workplace_type)"""
    else:
        return initial_columns + """)""" 

def get_table_values(table_name, item):
    inital_values = f"""({item["id"]}, {item["created_at"]}, {item["updated_at"]}, {item["source"]}"""
    if table_name == "greenhouse_job_departments":
        return inital_values + f""", {item["company_name"]}, {item["department_category"]}, {item["department_id"]}, {item["department_name"]})"""
    elif table_name == "greenhouse_jobs_outline":
        return inital_values + f""", {item["department_ids"]}, {item["location"]}, {item["office_ids"]}, {item["opening_link"]}, {item["opening_title"]})"""
    elif table_name == "lever_jobs_outline":
        return inital_values + f""", {item["company_name"]}, {item["department_names"]}, {item["location"]}, {item["opening_link"]}, {item["opening_title"]}, {item["workplace_type"]})"""
    else:
        return inital_values + """)""" 

def create_insert_item(table_name, item):
    table_columns = get_table_columns(table_name)
    table_values = get_table_values(table_name, item)
    return f"""insert into {table_name} {table_columns} values {table_values}"""

