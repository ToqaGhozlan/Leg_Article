import os
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
import psycopg.rows

DATABASE_URL = os.environ.get("DATABASE_URL")

# سننشئ الـ pool مرة واحدة فقط (يتم cache في Streamlit)
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=1,
            max_size=10,          # زدي إذا كان في مستخدمين كثير
            timeout=20,
            max_lifetime=1800,    # 30 دقيقة
            max_idle=300,         # 5 دقائق idle
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
            amended_articles JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_laws_kind ON laws (kind);
        """)
