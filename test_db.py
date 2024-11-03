from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

DATABASE = os.getenv("DATABASE")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")


try:
    conn = psycopg2.connect(
        database=DATABASE,
        host=DATABASE_HOST,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
    )

    print(conn)
    cur = conn.cursor()

    cur.execute("select * from job_listings")
    rows = cur.fetchall()
    print(rows[0:5])

except:
    print("Error")
