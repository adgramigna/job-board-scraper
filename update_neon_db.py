import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import urlparse
from sqlalchemy.engine import URL
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from a specific path
dotenv_path = '/Users/arnav/Downloads/GitHub/job-board-scraper-arnav/.env'  # Replace with the actual path
load_dotenv(dotenv_path, verbose=True)

# Database connection parameters
DB_USER = os.getenv('PG_USER')
DB_PASSWORD = os.getenv('PG_PASSWORD')
DB_HOST = os.getenv('PG_HOST')
DB_NAME = os.getenv('PG_DATABASE')

# Print only necessary environment variables
print(f"DB_USER: {DB_USER} (type: {type(DB_USER)})")
print(f"DB_HOST: {DB_HOST} (type: {type(DB_HOST)})")
print(f"DB_NAME: {DB_NAME} (type: {type(DB_NAME)})")

# Check for missing environment variables
required_env_vars = ['PG_USER', 'PG_PASSWORD', 'PG_HOST', 'PG_DATABASE']
missing_vars = [var for var in required_env_vars if os.getenv(var) is None]

if missing_vars:
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

# Ensure DB_PASSWORD is a string
if not isinstance(DB_PASSWORD, str):
    DB_PASSWORD = str(DB_PASSWORD)

# Create database connection URL
db_url = URL.create(
    drivername="postgresql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database=DB_NAME
)
engine = create_engine(db_url)

# Read CSV file
df = pd.read_csv('/Users/arnav/Downloads/GitHub/Linkedin-Jobs/company_ats_data.csv')

# Convert all column names to lowercase
df.columns = df.columns.str.lower()

# Filter for Greenhouse and Lever ATS systems
df = df[df['ats'].str.lower().isin(['greenhouse', 'lever', 'ashbyhq'])]

# Function to clean URLs by removing query parameters
def clean_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

# Clean the 'company_url' column
df['company_url'] = df['company url'].apply(clean_url)

# Drop duplicates based on 'company_url'
df = df.drop_duplicates(subset='company_url')

# Add is_enabled and is_prospect columns
df['is_enabled'] = True
df['is_prospect'] = False

# Select and reorder columns - include is_prospect
final_df = df[['company_url', 'ats', 'is_enabled', 'is_prospect']]

# Create table and upload data
try:
    # Create table if it doesn't exist
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS job_board_urls (
        id SERIAL PRIMARY KEY,
        company_url TEXT NOT NULL UNIQUE,
        ats TEXT NOT NULL,
        is_enabled BOOLEAN DEFAULT TRUE,
        is_prospect BOOLEAN DEFAULT FALSE
    );
    """
    
    # Prepare upsert SQL with correct parameter binding
    upsert_sql = """
    INSERT INTO job_board_urls (company_url, ats, is_enabled, is_prospect)
    VALUES (:company_url, :ats, :is_enabled, :is_prospect)
    ON CONFLICT (company_url) 
    DO UPDATE SET 
        ats = EXCLUDED.ats,
        is_enabled = EXCLUDED.is_enabled,
        is_prospect = EXCLUDED.is_prospect;
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        
        records = final_df.to_dict('records')
        for record in records:
            conn.execute(text(upsert_sql), record)
        
        conn.commit()
        print(f"Successfully upserted {len(records)} records to database!")

except Exception as e:
    logging.error("An error occurred during the database operation", exc_info=True)
    print(f"An error occurred: {e}")