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

    for i in range(1, 6):
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS tm_part{i} (
            id SERIAL PRIMARY KEY,
            leg_name TEXT,
            leg_number TEXT,
            mg_num TEXT,
            mg_page TEXT,
            year TEXT,
            mod_articles JSONB
        );
        """)
    cur.execute(f"ALTER TABLE tm_part{i} ADD COLUMN IF NOT EXISTS year TEXT;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_progress (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        law_idx INTEGER DEFAULT 0,
        mod_idx INTEGER DEFAULT 1
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
