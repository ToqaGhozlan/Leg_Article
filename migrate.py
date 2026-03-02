# migrate.py
import os
import json
from db import get_cursor, init_db

def has_migration_run(name: str) -> bool:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM migration_status WHERE migration_name = %s", (name,))
            return cur.fetchone() is not None
    except Exception:
        return False

def mark_migration_done(name: str):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO migration_status (migration_name) VALUES (%s) ON CONFLICT DO NOTHING",
            (name,)
        )

def migrate_law_kind(kind: str, json_filename: str) -> int:
    json_path = f"app/{json_filename}"  # أو عدل المسار حسب هيكلك
    if not os.path.exists(json_path):
        print(f"الملف غير موجود: {json_path}")
        return 0

    with open(json_path, encoding="utf-8-sig") as f:
        data = json.load(f)

    inserted = 0
    with get_cursor() as cur:
        for law in data:
            cur.execute(
                """
                INSERT INTO laws (kind, leg_name, leg_number, year, magazine_number, magazine_page, magazine_date, is_amendment, articles, amended_articles)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                ON CONFLICT (kind, leg_name, leg_number) DO NOTHING
                RETURNING id
                """,
                (
                    kind,
                    law.get("Leg_Name"),
                    law.get("Leg_Number"),
                    law.get("Year"),
                    law.get("Magazine_Number"),
                    law.get("Magazine_Page"),
                    law.get("Magazine_Date"),
                    law.get("is_amendment", False),
                    json.dumps(law.get("Articles", []), ensure_ascii=False),
                    json.dumps(law.get("amended_articles", []), ensure_ascii=False),
                )
            )
            if cur.fetchone():
                inserted += 1
    print(f"{kind}: أُضيف {inserted} سجل من {len(data)}")
    return inserted

if __name__ == "__main__":
    init_db()  # ينشئ الجداول لو مش موجودة
    migration_name = "initial_data_load_v1"
    if not has_migration_run(migration_name):
        print("جاري الـ migration...")
        t1 = migrate_law_kind("قانون ج1", "V02_Laws_P1.json")
        t2 = migrate_law_kind("قانون ج2", "V02_Laws_P2.json")
        mark_migration_done(migration_name)
        print(f"تم! أُضيف {t1 + t2} سجل")
    else:
        print("الـ migration تم من قبل، ما في داعي نعيده.")
