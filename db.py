import os
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
import psycopg.rows

DATABASE_URL = os.environ.get("DATABASE_URL")
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=1,
            max_size=10,
            timeout=30,
            max_lifetime=1800,
            max_idle=300,
            kwargs={"row_factory": psycopg.rows.dict_row},
            open=False
        )
        _pool.open()
    return _pool

@contextmanager
def get_cursor():
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise

def init_db():
    """
    ينشئ جداول الـ modified فقط — البيانات الأصلية تُقرأ من JSON.
    """
    with get_cursor() as cur:
        for table in ["laws_p1_modified", "laws_p2_modified", "laws_p3_modified"]:
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id               SERIAL PRIMARY KEY,
                leg_name         TEXT,
                leg_number       TEXT,
                year             TEXT,
                magazine_number  TEXT,
                magazine_page    TEXT,
                magazine_date    TEXT,
                is_amendment     BOOLEAN DEFAULT FALSE,
                articles         JSONB,
                amended_articles JSONB
            );
            """)
