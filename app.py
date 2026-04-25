import os

from flask import Flask, request, jsonify, render_template
import json
from db import init_db, get_conn

app = Flask(__name__)

init_db()

# الصفحة الرئيسية
@app.route("/")
def home():
    return render_template("index.html")


# 🔥 API لحفظ المادة المعدلة
@app.route("/update-article", methods=["POST"])
def update_article():
    data = request.json
    print("REQUEST JSON:", request.json)
    leg_number = data["leg_number"]
    year = data.get("year")
    mod_number = data["mod_number"]
    mod_name = data["mod_name"]
    mod_year = data["mod_year"]
    mod_mg_number = data["mod_mg_number"]
    mod_mg_page = data["mod_mg_page"]

    art_num = data["art_num"]
    content = data["content"]

    conn = get_conn()
    cur = conn.cursor()

    # 1) جيب القانون
    cur.execute("""
        SELECT mod_articles
        FROM tm_part1
        WHERE leg_number = %s
    """, (leg_number,))

    row = cur.fetchone()

    new_article = {
        "art_num": art_num,
        "content": content
    }

    new_mod = {
        "mod_name": mod_name,
        "mod_number": mod_number,
        "mod_year": mod_year,
        "mod_mg_number": mod_mg_number,
        "mod_mg_page": mod_mg_page,
        "articles": [new_article]
    }

    if row is None:
        # أول إدخال
        cur.execute("""
            INSERT INTO tm_part1 (leg_name, leg_number, mg_num, mg_page, year, mod_articles)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            mod_name,
            leg_number,
            mod_mg_number,
            mod_mg_page,
            year,
            json.dumps([new_mod])
        ))
    else:
        # تحديث
        existing = row[0] or []
        if isinstance(existing, str):
            existing = json.loads(existing)

        # نضيف أو نعدل
        found = False

        for m in existing:
            if isinstance(m, dict) and m.get("mod_number") == mod_number:
                m.setdefault("articles", [])
                m["articles"] = [
                    a for a in m["articles"]
                    if a["art_num"] != art_num
                ]
                m["articles"].append(new_article)
                found = True
                break

        if not found:
            existing.append(new_mod)

        cur.execute("""
            UPDATE tm_part1
            SET mod_articles = %s
            WHERE leg_number = %s
        """, (json.dumps(existing), leg_number))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/get-law-data")
def get_law_data():
    leg_number = request.args.get("leg_number")
    if not leg_number:
        return jsonify({"error": "leg_number required"}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT mod_articles FROM tm_part1 WHERE leg_number = %s", (leg_number,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None or row[0] is None:
        return jsonify({"mod_articles": []})

    existing = row[0]
    if isinstance(existing, str):
        existing = json.loads(existing)

    return jsonify({"mod_articles": existing})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
