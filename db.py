import os
import psycopg2
import json

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True


def get_cursor():
    return conn.cursor()


def init_db():
    cur = get_cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS laws (
        id SERIAL PRIMARY KEY,

        kind TEXT,

        leg_name TEXT,
        leg_number TEXT,
        year TEXT,

        magazine_number TEXT,
        magazine_page TEXT,
        magazine_date TEXT,

        is_amendment BOOLEAN,

        articles JSONB,
        amended_articles JSONB
    );
    """)
