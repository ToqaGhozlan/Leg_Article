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
    with get_cursor() as cur:
        # جدول القوانين + UNIQUE constraint لمنع التكرار
        cur.execute("""
        CREATE TABLE IF NOT EXISTS laws (
            id SERIAL PRIMARY KEY,
            kind TEXT NOT NULL,
            leg_name TEXT,
            leg_number TEXT,
            year TEXT,
            magazine_number TEXT,
            magazine_page TEXT,
            magazine_date TEXT,
            is_amendment BOOLEAN DEFAULT FALSE,
            articles JSONB,
            amended_articles JSONB,
            CONSTRAINT unique_law_per_kind UNIQUE (kind, leg_name, leg_number)
        );
        CREATE INDEX IF NOT EXISTS idx_laws_kind ON laws (kind);
        """)

        # جدول تتبع الـ migrations
        cur.execute("""
        CREATE TABLE IF NOT EXISTS migration_status (
            id SERIAL PRIMARY KEY,
            migration_name TEXT UNIQUE NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
