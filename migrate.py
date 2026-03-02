# migrate.py
import os
import json
from db import get_cursor, init_db

def has_migration_run(name: str) -> bool:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM migration_status WHERE migration_name = %s", (name,))
            return cur.fetchone() is not None
    except Exception as e:
        print(f"خطأ في التحقق من الـ migration: {e}")
        return False


def mark_migration_done(name: str):
    try:
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO migration_status (migration_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (name,)
            )
    except Exception as e:
        print(f"خطأ في تسجيل الـ migration: {e}")


def migrate_law_kind(kind: str, json_filename: str) -> int:
    # ← غيّر المسار حسب مكان ملفات JSON في الـ repo الخاص بك
    # الأمثلة الشائعة:
    # json_path = f"data/{json_filename}"
    # json_path = json_filename
    json_path = f"app/{json_filename}"   # ← إذا كانت داخل مجلد app

    if not os.path.exists(json_path):
        print(f"الملف غير موجود: {json_path}")
        return 0

    try:
        with open(json_path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception as e:
        print(f"خطأ في قراءة الملف {json_path}: {e}")
        return 0

    inserted = 0
    try:
        with get_cursor() as cur:
            for law in data:
                cur.execute(
                    """
                    INSERT INTO laws (
                        kind, leg_name, leg_number, year,
                        magazine_number, magazine_page, magazine_date,
                        is_amendment, articles, amended_articles
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    ON CONFLICT ON CONSTRAINT unique_law_per_kind DO NOTHING
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
        print(f"{kind}: تم إضافة {inserted} سجل (من {len(data)})")
    except Exception as e:
        print(f"خطأ أثناء إدخال بيانات {kind}: {e}")
        return 0

    return inserted


if __name__ == "__main__":
    print("تهيئة قاعدة البيانات...")
    init_db()

    migration_name = "initial_data_load_v1"

    if not has_migration_run(migration_name):
        print("بدء تحميل البيانات الأولية...")
        t1 = migrate_law_kind("قانون ج1", "V02_Laws_P1.json")
        t2 = migrate_law_kind("قانون ج2", "V02_Laws_P2.json")
        total = t1 + t2
        mark_migration_done(migration_name)
        print(f"تم التحميل بنجاح → إجمالي السجلات المضافة: {total}")
    else:
        print("تم تنفيذ الـ migration مسبقاً → لا حاجة لإعادته")
