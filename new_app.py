from flask import Flask, g, render_template, current_app, request
from flask_paginate import Pagination
from dotenv import load_dotenv
import logging
from typing import List, Dict, Tuple
from contextlib import contextmanager
import os
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import Integer, String, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column


load_dotenv()
logging.basicConfig(level=logging.INFO)

DATABASE = os.getenv("DATABASE")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
connection_str = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:6543/{DATABASE}"
PER_PAGE = 15


class DatabaseError(Exception):
    pass


app = Flask(__name__)


class JobListing(g.db.Model):
    id: Mapped[Integer] = mapped_column(primary_key=True)
    company_name: Mapped[String]
    job_title: Mapped[String]
    job_link: Mapped[String]
    created_at: Mapped[DateTime]


def get_job_listings_paginated(page: int, per_page: int) -> Tuple[List[Dict], int]:
    try:
        page = g.db.session.execute(g.db.select(JobListing).order_by(JobListing.id)).scalars()
        print(page)
        # total_count = page.count()
        # job_listings = page.offset((page - 1) * per_page).limit(per_page).all()
        return job_listings, total_count

    except Exception as e:
        app.logger.error(f"Error getting job listings: {str(e)}")
        raise DatabaseError("Error getting job listings")



@app.route("/")
def index():
    try:
        page = request.args.get("page", 1, type=int)
        job_listings, total_count = get_job_listings_paginated(page, PER_PAGE)

        pagination = Pagination(
            page=page,
            total=total_count,
            per_page=PER_PAGE,
            prev_label="",
            next_label="",
        )

        return render_template(
            "index.html", job_listings=job_listings, pagination=pagination
        )
    except Exception as e:
        app.logger.error(f"Error loading index page: {str(e)}")
        return render_template(
            "error.html", message="Unable to load job listings. Please try again later."
        )


def get_db_connection():
    return create_engine(connection_str)


def get_db():
    if "db" not in g:
        g.db = get_db_connection()
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            app.logger.error(f"Error closing database connection: {str(e)}")


def init_app(app):
    app.teardown_appcontext(close_db)


init_app(app)

if __name__ == "__main__":
    app.run(debug=True)
