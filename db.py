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
    ينشئ جداول التعديلات الثمانية + جدول تقدم المستخدمين
    """
    with get_cursor() as cur:
        # جداول التعديلات — 8 جداول
        for i in range(1, 9):
            table = f"bylaws_p{i}_modified"
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id          SERIAL PRIMARY KEY,
                leg_name    TEXT,
                leg_number  TEXT,
                year        TEXT,
                magazine_number TEXT,
                magazine_page   TEXT,
                magazine_date   TEXT,
                is_amendment    BOOLEAN DEFAULT FALSE,
                articles        JSONB,
                amended_articles JSONB
            );
            """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            username    TEXT NOT NULL,
            kind        TEXT NOT NULL,
            last_idx    INT NOT NULL DEFAULT 0,
            updated_at  TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (username, kind)
        );
        """)