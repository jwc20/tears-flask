from flask import Flask, g, render_template, current_app, request
from flask_paginate import Pagination
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Tuple
from contextlib import contextmanager
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)

DATABASE = os.getenv("DATABASE")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
PER_PAGE = 15


class DatabaseError(Exception):
    pass


app = Flask(__name__)


@app.route('/')
def index():
    try:
        page = request.args.get('page', 1, type=int)
        job_listings, total_count = get_job_listings_paginated(page, PER_PAGE)

        pagination = Pagination(
            page=page,
            total=total_count,
            per_page=PER_PAGE,
            prev_label='',
            next_label='',
        )

        return render_template(
            'index.html',
            job_listings=job_listings,
            pagination=pagination
        )
    except Exception as e:
        app.logger.error(f"Error loading index page: {str(e)}")
        return render_template(
            'error.html',
            message="Unable to load job listings. Please try again later."
        )


def get_db_connection():
    return psycopg2.connect(
        database=DATABASE,
        host=DATABASE_HOST,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        cursor_factory=RealDictCursor
    )


def get_db():
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except psycopg2.Error as e:
            logging.error(f"Error closing database connection: {str(e)}")


@contextmanager
def get_db_cursor():
    conn = get_db()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        logging.error(f"Database operation failed: {str(e)}")
        raise DatabaseError("Database operation failed") from e
    finally:
        cursor.close()


def get_job_listings_paginated(page: int, per_page: int) -> Tuple[List[Dict], int]:
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM job_listings")
            total_count = cursor.fetchone()['count']

            cursor.execute("""
                SELECT company_name, job_title, job_link 
                FROM job_listings 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (per_page, (page - 1) * per_page))

            return cursor.fetchall(), total_count
    except (psycopg2.Error, DatabaseError) as e:
        logging.error(f"Failed to fetch job listings: {str(e)}")
        return [], 0


def init_app(app):
    app.teardown_appcontext(close_db)

init_app(app)

if __name__ == '__main__':
    app.run(debug=True)