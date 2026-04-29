import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import json
from db import init_db, get_conn

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-change-me")

init_db()

# ─── بيانات اليوزرات ───────────────────────────────────────
USERS = {
    "leen":   {"password": "leen1234",   "part": 1, "data_file": "data_part1.js"},
    "diwan":  {"password": "diwan1234",  "part": 2, "data_file": "data_part2.js"},
    "toqa":   {"password": "toqa1234",   "part": 3, "data_file": "data_part3.js"},
    "sadeen": {"password": "sadeen1234", "part": 4, "data_file": "data_part4.js"},
    "nula":   {"password": "nula1234",   "part": 5, "data_file": "data_part5.js"},
}

def get_table():
    part = session.get("part", 1)
    return f"tm_part{part}"

# ─── LOGIN ─────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = USERS.get(username)
        if user and user["password"] == password:
            session["username"]  = username
            session["part"]      = user["part"]
            session["data_file"] = user["data_file"]
            return redirect(url_for("home"))
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── HOME ──────────────────────────────────────────────────
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html",
                           username=session["username"],
                           data_file=session["data_file"])

# ─── UPDATE ARTICLE ────────────────────────────────────────
@app.route("/update-article", methods=["POST"])
def update_article():
    if "username" not in session:
        return jsonify({"error": "unauthorized"}), 401

    data       = request.json
    table      = get_table()
    leg_number = data["leg_number"]
    year       = data.get("year")
    mod_number = data["mod_number"]
    mod_name   = data["mod_name"]
    mod_year   = data["mod_year"]
    mod_mg_number = data["mod_mg_number"]
    mod_mg_page   = data["mod_mg_page"]
    art_num    = data["art_num"]
    content    = data["content"]

    conn = get_conn()
    cur  = conn.cursor()

    cur.execute(f"SELECT mod_articles FROM {table} WHERE leg_number = %s", (leg_number,))
    row = cur.fetchone()

    new_article = {"art_num": art_num, "content": content}
    new_mod = {
        "mod_name": mod_name, "mod_number": mod_number,
        "mod_year": mod_year, "mod_mg_number": mod_mg_number,
        "mod_mg_page": mod_mg_page, "articles": [new_article]
    }

    if row is None:
        cur.execute(f"""
            INSERT INTO {table} (leg_name, leg_number, mg_num, mg_page, year, mod_articles)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (mod_name, leg_number, mod_mg_number, mod_mg_page, year, json.dumps([new_mod])))
    else:
        existing = row[0] or []
        if isinstance(existing, str):
            existing = json.loads(existing)

        found = False
        for m in existing:
            if isinstance(m, dict) and m.get("mod_number") == mod_number:
                m.setdefault("articles", [])
                m["articles"] = [a for a in m["articles"] if a["art_num"] != art_num]
                m["articles"].append(new_article)
                found = True
                break
        if not found:
            existing.append(new_mod)

        cur.execute(f"""
            UPDATE {table} SET mod_articles = %s WHERE leg_number = %s
        """, (json.dumps(existing), leg_number))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"})

# ─── ADD ARTICLE ───────────────────────────────────────────
@app.route("/add-article", methods=["POST"])
def add_article():
    if "username" not in session:
        return jsonify({"error": "unauthorized"}), 401

    data          = request.json
    table         = get_table()
    leg_number    = data["leg_number"]
    mod_number    = data["mod_number"]
    mod_name      = data["mod_name"]
    mod_year      = data["mod_year"]
    mod_mg_number = data["mod_mg_number"]
    mod_mg_page   = data["mod_mg_page"]
    art_num       = data["art_num"]        # رقم المادة الجديدة
    content       = data["content"]        # محتوى المادة
    art_type      = data.get("art_type", "إضافة مادة")  # نوع التعديل

    new_article = {
        "art_num":  art_num,
        "content":  content,
        "art_type": art_type
    }
    new_mod = {
        "mod_name":      mod_name,
        "mod_number":    mod_number,
        "mod_year":      mod_year,
        "mod_mg_number": mod_mg_number,
        "mod_mg_page":   mod_mg_page,
        "articles":      [new_article]
    }

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(f"SELECT mod_articles FROM {table} WHERE leg_number = %s", (leg_number,))
    row = cur.fetchone()

    if row is None:
        cur.execute(f"""
            INSERT INTO {table} (leg_name, leg_number, mg_num, mg_page, year, mod_articles)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (mod_name, leg_number, mod_mg_number, mod_mg_page, None, json.dumps([new_mod])))
    else:
        existing = row[0] or []
        if isinstance(existing, str):
            existing = json.loads(existing)

        found = False
        for m in existing:
            if isinstance(m, dict) and m.get("mod_number") == mod_number:
                m.setdefault("articles", [])
                # لا تكرر نفس رقم المادة
                m["articles"] = [a for a in m["articles"] if str(a["art_num"]) != str(art_num)]
                m["articles"].append(new_article)
                found = True
                break
        if not found:
            existing.append(new_mod)

        cur.execute(f"""
            UPDATE {table} SET mod_articles = %s WHERE leg_number = %s
        """, (json.dumps(existing), leg_number))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"})
# ─── GET LAW DATA ──────────────────────────────────────────
@app.route("/get-law-data")
def get_law_data():
    if "username" not in session:
        return jsonify({"error": "unauthorized"}), 401

    leg_number = request.args.get("leg_number")
    if not leg_number:
        return jsonify({"error": "leg_number required"}), 400

    table = get_table()
    conn  = get_conn()
    cur   = conn.cursor()
    cur.execute(f"SELECT mod_articles FROM {table} WHERE leg_number = %s", (leg_number,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None or row[0] is None:
        return jsonify({"mod_articles": []})

    existing = row[0]
    if isinstance(existing, str):
        existing = json.loads(existing)
    return jsonify({"mod_articles": existing})

@app.route("/save-progress", methods=["POST"])
def save_progress():
    if "username" not in session:
        return jsonify({"error": "unauthorized"}), 401
    data     = request.json
    law_idx  = data.get("law_idx", 0)
    mod_idx  = data.get("mod_idx", 1)
    username = session["username"]
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO user_progress (username, law_idx, mod_idx)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO UPDATE
        SET law_idx = EXCLUDED.law_idx,
            mod_idx = EXCLUDED.mod_idx
    """, (username, law_idx, mod_idx))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"})


@app.route("/get-progress")
def get_progress():
    if "username" not in session:
        return jsonify({"error": "unauthorized"}), 401
    username = session["username"]
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT law_idx, mod_idx FROM user_progress WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
         return jsonify({"law_idx": 0, "mod_idx": 1})
    return jsonify({
        "law_idx": row[0] if row[0] is not None else 0,
        "mod_idx": row[1] if row[1] is not None else 1
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
