import os
import json
from db import get_cursor, init_db

def has_migration_run(name: str) -> bool:
    """التحقق إذا تم تنفيذ الـ migration سابقًا"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM migration_status WHERE migration_name = %s", (name,))
            return cur.fetchone() is not None
    except Exception as e:
        print(f"خطأ في التحقق من حالة الـ migration: {e}")
        return False


def mark_migration_done(name: str):
    """تسجيل أن الـ migration تم بنجاح"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO migration_status (migration_name, completed_at)
                VALUES (%s, CURRENT_TIMESTAMP)
                ON CONFLICT (migration_name) DO NOTHING
                """,
                (name,)
            )
        print(f"تم تسجيل نجاح الـ migration: {name}")
    except Exception as e:
        print(f"خطأ أثناء تسجيل نجاح الـ migration: {e}")


def migrate_law_kind(kind: str, json_filename: str, target_table: str) -> int:
    """
    تحميل بيانات قانون معين من ملف JSON إلى الجدول المحدد
    """
    json_path = f"app/{json_filename}"
    
    print(f"جاري معالجة {kind}")
    print(f"  المسار: {json_path}")
    print(f"  الجدول الهدف: {target_table}")
    
    if not os.path.exists(json_path):
        print(f"    → الملف غير موجود: {json_path}")
        return 0
    
    try:
        with open(json_path, encoding="utf-8-sig") as f:
            data = json.load(f)
        print(f"    → تم قراءة {len(data):,} عنصر")
    except Exception as e:
        print(f"    → خطأ في قراءة الملف JSON: {e}")
        return 0
    
    if not data:
        print("    → الملف فارغ")
        return 0
    
    inserted = 0
    try:
        with get_cursor() as cur:
            for i, law in enumerate(data, 1):
                leg_number = law.get("Leg_Number")
                if not leg_number:
                    leg_number = f"NO_NUMBER_{i:04d}"
                
                cur.execute(
                    f"""
                    INSERT INTO {target_table} (
                        leg_name, leg_number, year,
                        magazine_number, magazine_page, magazine_date,
                        is_amendment, articles, amended_articles
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    ON CONFLICT (leg_number) DO NOTHING
                    RETURNING id
                    """,
                    (
                        law.get("Leg_Name"),
                        leg_number,
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
        
        print(f"    → تم إضافة {inserted:,} سجل جديد (من {len(data):,})")
        return inserted
    
    except Exception as e:
        print(f"    → خطأ أثناء إدخال البيانات في {target_table}: {e}")
        return 0


if __name__ == "__main__":
    print("=== بدء تشغيل migrate.py ===")
    
    print("تهيئة قاعدة البيانات...")
    try:
        init_db()
        print("قاعدة البيانات جاهزة ✅")
    except Exception as e:
        print(f"خطأ في تهيئة قاعدة البيانات: {e}")
        exit(1)
    
    migration_name = "initial_data_load_v3_p1_p2_separate_tables"
    print(f"التحقق من حالة الـ migration '{migration_name}'...")
    
    if has_migration_run(migration_name):
        print("→ تم تنفيذ الـ migration مسبقاً → لا حاجة لإعادة التحميل")
    else:
        print("→ بدء تحميل البيانات الأولية...")
        
        inserted1 = migrate_law_kind(
            "قانون ج1",
            "V02_Laws_P1.json",
            "laws_p1_original"
        )
        
        inserted2 = migrate_law_kind(
            "قانون ج2",
            "V02_Laws_P2.json",
            "laws_p2_original"
        )
        
        total = inserted1 + inserted2
        print(f"\nإجمالي السجلات المُضافة: {total:,}")
        
        if total > 0:
            mark_migration_done(migration_name)
            print("تم تسجيل النجاح → لن يُعاد التحميل في المرات القادمة")
        else:
            print("لم يتم إضافة أي سجلات → لم يتم تسجيل النجاح")
    
    print("=== انتهى migrate.py ===")
