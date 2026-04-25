import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tm_part1 (
        id SERIAL PRIMARY KEY,
        leg_name TEXT,
        leg_number TEXT,
        mg_num TEXT,
        mg_page TEXT,
        year TEXT,
        mod_articles JSONB
    );
    """)

    # ضمان وجود العمود في الجداول القديمة
    cur.execute("ALTER TABLE tm_part1 ADD COLUMN IF NOT EXISTS year TEXT;")

    conn.commit()
    cur.close()
    conn.close()
