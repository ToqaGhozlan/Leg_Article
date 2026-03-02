import json
import os
from db import get_cursor

with open("V02_Laws_P1.json", encoding="utf-8") as f:
    data = json.load(f)

with get_cursor() as cur:
    for law in data:
        cur.execute("""
        INSERT INTO laws (
            kind, leg_name, leg_number, year,
            magazine_number, magazine_page, magazine_date,
            is_amendment, articles, amended_articles
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """, (
            "قانون ج1",
            law.get("Leg_Name"),
            law.get("Leg_Number"),
            law.get("Year"),
            law.get("Magazine_Number"),
            law.get("Magazine_Page"),
            law.get("Magazine_Date"),
            law.get("is_amendment", False),
            json.dumps(law.get("Articles", []), ensure_ascii=False),
            json.dumps(law.get("amended_articles", []), ensure_ascii=False),
        ))
