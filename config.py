"""Load config from environment variables."""
from os import environ, path
from dotenv import load_dotenv


# Load variables from .env
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


# Database config
DATABASE_HOST = "itbot.chc2ffunjdw0.us-east-1.rds.amazonaws.com"
DATABASE_PORT = "5432"  # default postgres port
DATABASE_NAME = "CXG"
DATABASE_USERNAME = "ubilityai"
DATABASE_PASSWORD = "ubility#07"

# SQL queries
SQL_QUERIES_FOLDER = 'sql'
CSV_COLUMN_INTENT='Level 1'
CSV_COLUMN_DESCRIPTION='description'
LANGUAGES=['en','fr','russ','zh','jp']
RASA_ADDRESS='http://0.0.0.0:'
PATH_TO_TRAIN='/model/train'
PATH_TO_MODEL='/model'
