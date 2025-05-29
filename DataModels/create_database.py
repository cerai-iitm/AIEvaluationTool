import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    db_user = os.getenv("PG_USER")
    db_password = os.getenv("PG_PASSWORD")
    db_host = os.getenv("PG_HOST")
    db_port = os.getenv("PG_PORT")
    db_name = "postgres"
    connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    connection.autocommit = True

    cursor = connection.cursor()

    cursor.execute("CREATE DATABASE evaldb;")

    print("Database evaldb created successfully")
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")

except Exception as e:
    print(f"An error occurred while creating the database: {e}")