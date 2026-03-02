import json
from db import get_conn

conn = get_conn()
cur = conn.cursor()

with open("V02_Laws_P1.json", encoding="utf-8") as f:
    data = json.load(f)

for law in data:

    cur.execute("""
    INSERT INTO laws (
        kind,
        leg_name, leg_number, year,
        magazine_number, magazine_page, magazine_date,
        is_amendment,
        articles, amended_articles
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (

        "قانون ج1",

        law["Leg_Name"],
        law["Leg_Number"],
        law["Year"],

        law["Magazine_Number"],
        law["Magazine_Page"],
        law["Magazine_Date"],

        law["is_amendment"],

        json.dumps(law["Articles"], ensure_ascii=False),
        json.dumps(law["amended_articles"], ensure_ascii=False),
    ))

conn.commit()
cur.close()
