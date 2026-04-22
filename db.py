# db.py - متكامل مع هيكل البيانات الجديد
import os
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
import psycopg.rows
import json

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
    """
    إنشاء جميع الجداول المطلوبة:
    - 5 جداول للقوانين الأساسية (bylaws_pX_base)
    - 5 جداول للتعديلات (bylaws_pX_modified)
    - جدول تقدم المستخدمين (user_progress)
    """
    with get_cursor() as cur:
        # 1. جداول القوانين الأساسية (5 جداول)
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
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(law_name, law_number, year)
            );
            """)
            print(f"✅ Table {table_base} ready")

        # 2. جداول التعديلات (5 جداول)
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
            print(f"✅ Table {table_modified} ready")
            
            # إضافة فهارس لتحسين الأداء
            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_modified}_base_law 
            ON {table_modified}(base_law_id);
            """)

        # 3. جدول تقدم المستخدمين (موجود بالفعل، نضيفه إذا لم يوجد)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            username TEXT NOT NULL,
            kind TEXT NOT NULL,
            last_idx INT NOT NULL DEFAULT 0,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (username, kind)
        );
        """)
        print("✅ Table user_progress ready")
        
        print("🎉 All database tables initialized successfully!")

# =====================================================
# HELPER FUNCTIONS للتعامل مع البيانات
# =====================================================

def save_base_law(kind: str, law_data: dict) -> int:
    """حفظ أو تحديث قانون أساسي"""
    table_base = f"bylaws_{kind}_base"
    law_name = law_data.get("law_name", "")
    law_number = law_data.get("law_number", "")
    year = law_data.get("year", "")
    
    with get_cursor() as cur:
        # البحث عن القانون الموجود
        cur.execute(f"""
            SELECT id FROM {table_base}
            WHERE law_name = %s AND law_number = %s AND year = %s
        """, (law_name, law_number, year))
        existing = cur.fetchone()
        
        base_articles_json = json.dumps(law_data.get("BaseArticles", {}), ensure_ascii=False)
        
        if existing:
            cur.execute(f"""
                UPDATE {table_base}
                SET magazine_number = %s,
                    magazine_page = %s,
                    link = %s,
                    base_articles = %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id
            """, (
                law_data.get("Magazine_number", ""),
                law_data.get("Magazine_page", ""),
                law_data.get("link", ""),
                base_articles_json,
                existing["id"]
            ))
            return existing["id"]
        else:
            cur.execute(f"""
                INSERT INTO {table_base}
                    (law_name, law_number, year, magazine_number, magazine_page, link, base_articles)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
            """, (
                law_name, law_number, year,
                law_data.get("Magazine_number", ""),
                law_data.get("Magazine_page", ""),
                law_data.get("link", ""),
                base_articles_json
            ))
            return cur.fetchone()["id"]

def save_modification(kind: str, base_law_id: int, mod_data: dict):
    """حفظ تعديل (أو تحديثه إذا موجود)"""
    table_modified = f"bylaws_{kind}_modified"
    
    mod_number = mod_data.get("mod_number", "")
    mod_year = mod_data.get("mod_year", "")
    
    with get_cursor() as cur:
        # البحث عن التعديل الموجود
        cur.execute(f"""
            SELECT id FROM {table_modified}
            WHERE base_law_id = %s AND mod_number = %s AND mod_year = %s
        """, (base_law_id, mod_number, mod_year))
        existing = cur.fetchone()
        
        mod_articles_json = json.dumps(mod_data.get("mod_Articles", []), ensure_ascii=False)
        desc_articles_json = json.dumps(mod_data.get("descArticles", []), ensure_ascii=False)
        
        if existing:
            cur.execute(f"""
                UPDATE {table_modified}
                SET mod_name = %s,
                    mod_mg_number = %s,
                    mod_mg_page = %s,
                    mod_articles = %s::jsonb,
                    desc_articles = %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                mod_data.get("mod_name", ""),
                mod_data.get("mod_mg_number", ""),
                mod_data.get("mod_mg_page", ""),
                mod_articles_json,
                desc_articles_json,
                existing["id"]
            ))
        else:
            cur.execute(f"""
                INSERT INTO {table_modified}
                    (base_law_id, mod_name, mod_number, mod_year, mod_mg_number, mod_mg_page, mod_articles, desc_articles)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
            """, (
                base_law_id,
                mod_data.get("mod_name", ""),
                mod_number,
                mod_year,
                mod_data.get("mod_mg_number", ""),
                mod_data.get("mod_mg_page", ""),
                mod_articles_json,
                desc_articles_json
            ))

def save_amendment_from_comparison(kind: str, base_law_id: int, mod_id: int, 
                                    article_num: str, old_text: str, new_text: str, 
                                    user: str):
    """
    حفظ تعديل قام به المستخدم في قسم المقارنة
    amendment_type = "comparison_edit"
    """
    table_modified = f"bylaws_{kind}_modified"
    
    with get_cursor() as cur:
        # جلب التعديل الحالي
        cur.execute(f"""
            SELECT amended_articles FROM {table_modified}
            WHERE id = %s
        """, (mod_id,))
        row = cur.fetchone()
        
        amended_articles = row["amended_articles"] if row["amended_articles"] else []
        
        # إضافة التعديل الجديد
        new_amendment = {
            "type": "comparison_edit",
            "article_number": article_num,
            "old_text": old_text,
            "new_text": new_text,
            "edited_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "edited_by": user,
            "mod_id": mod_id
        }
        amended_articles.append(new_amendment)
        
        # تحديث جدول التعديلات
        cur.execute(f"""
            UPDATE {table_modified}
            SET amended_articles = %s::jsonb,
                updated_at = NOW()
            WHERE id = %s
        """, (json.dumps(amended_articles, ensure_ascii=False), mod_id))

def load_all_data(kind: str):
    """تحميل جميع القوانين والتعديلات لنوع معين"""
    table_base = f"bylaws_{kind}_base"
    table_modified = f"bylaws_{kind}_modified"
    
    with get_cursor() as cur:
        # جلب جميع القوانين الأساسية
        cur.execute(f"""
            SELECT * FROM {table_base}
            ORDER BY id
        """)
        base_laws = cur.fetchall()
        
        result = []
        for base in base_laws:
            # جلب التعديلات لهذا القانون
            cur.execute(f"""
                SELECT * FROM {table_modified}
                WHERE base_law_id = %s
                ORDER BY id
            """, (base["id"],))
            modifications = cur.fetchall()
            
            result.append({
                "base_law": dict(base),
                "modifications": [dict(m) for m in modifications]
            })
        
        return result

def save_progress(username: str, kind: str, idx: int):
    """حفظ تقدم المستخدم"""
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO user_progress (username, kind, last_idx, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (username, kind)
            DO UPDATE SET last_idx = EXCLUDED.last_idx, updated_at = NOW()
        """, (username, kind, idx))

def load_progress(username: str, kind: str) -> int:
    """تحميل تقدم المستخدم"""
    with get_cursor() as cur:
        cur.execute(
            "SELECT last_idx FROM user_progress WHERE username=%s AND kind=%s",
            (username, kind)
        )
        row = cur.fetchone()
        return row["last_idx"] if row else 0

def load_all_progress(username: str) -> dict:
    """تحميل كل تقدم المستخدم"""
    with get_cursor() as cur:
        cur.execute(
            "SELECT kind, last_idx FROM user_progress WHERE username=%s",
            (username,)
        )
        rows = cur.fetchall()
        return {row["kind"]: row["last_idx"] for row in rows}
