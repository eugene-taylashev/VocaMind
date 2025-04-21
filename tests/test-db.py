# Note: this project uses psycopg3, not psycopg2
import psycopg
from dotenv import load_dotenv

# loading variables from .env file
load_dotenv() 
DB_HOST=os.getenv("DB_HOST")
DB_NAME=os.getenv("DB_NAME")
DB_USER=os.getenv("DB_USER")
DB_PASS=os.getenv("DB_PASS")


with psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) as conn:
    #-- Open a cursor to perform database operations
    cur = conn.cursor()

    cur.execute("SELECT * FROM logs LIMIT 1;")
    print(cur.fetchone())

    cur.close()
