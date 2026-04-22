# db.py - قاعدة البيانات المتكاملة لمنصة التدقيق القانوني
import os
import json
from datetime import datetime
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
import psycopg.rows

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL not found! Make sure PostgreSQL is added on Railway.")

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
        print("✅ Database connection pool created")
    return _pool

@contextmanager
def get_cursor():
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"❌ Database error: {e}")
                raise

def init_db():
    """Create all necessary tables for the legal audit platform"""
    with get_cursor() as cur:
        # 1. Base laws tables (5 tables - one for each law type)
        for i in range(1, 6):
            table_base = f"bylaws_p{i}_base"
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_base} (
                id SERIAL PRIMARY KEY,
                law_name TEXT NOT NULL,
                law_number TEXT,
                year TEXT,
                magazine_number TEXT,
                magazine_page TEXT,
                link TEXT,
                base_articles JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """)
            
            # Add unique constraint
            cur.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'unique_law_{i}'
                ) THEN
                    ALTER TABLE {table_base} ADD CONSTRAINT unique_law_{i} 
                    UNIQUE(law_name, law_number, year);
                END IF;
            END $$;
            """)
        
        # 2. Modifications tables (5 tables)
        for i in range(1, 6):
            table_modified = f"bylaws_p{i}_modified"
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_modified} (
                id SERIAL PRIMARY KEY,
                base_law_id INTEGER REFERENCES bylaws_p{i}_base(id) ON DELETE CASCADE,
                mod_name TEXT,
                mod_number TEXT,
                mod_year TEXT,
                mod_mg_number TEXT,
                mod_mg_page TEXT,
                mod_articles JSONB DEFAULT '[]'::jsonb,
                desc_articles JSONB DEFAULT '[]'::jsonb,
                amended_articles JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """)
            
            # Add indexes for performance
            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_mod_base_law_{i} 
            ON {table_modified}(base_law_id);
            """)
        
        # 3. User progress table
        cur.execute("""
        CREATE
