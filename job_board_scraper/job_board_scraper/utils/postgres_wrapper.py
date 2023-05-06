import os
import psycopg2

class PostgresWrapper:
    def __init__(self):
        ## Connection Details
        self.hostname = os.environ.get("PG_HOST")
        self.username = os.environ.get("PG_USER")
        self.password = os.environ.get("PG_PASSWORD")
        self.database = os.environ.get("PG_DATABASE")

    def connection(self):
        ## Create/Connect to database
        return psycopg2.connect(host=self.hostname, user=self.username, password=self.password, dbname=self.database)


    def cursor(self):  
        ## Create cursor, used to execute commands
        return self.connection().cursor()
