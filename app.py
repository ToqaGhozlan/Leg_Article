import streamlit as st
import psycopg2
import psycopg2.extras
import json
import html as html_lib
from datetime import datetime
import random
import os

# =====================================================
# DATABASE
# =====================================================

DB_URL = os.getenv("DATABASE_URL")

@st.cache_resource
def get_conn():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS laws (
        id SERIAL PRIMARY KEY,

        kind TEXT,

        leg_name TEXT,
        leg_number TEXT,
        year TEXT,

        magazine_number TEXT,
        magazine_page TEXT,
        magazine_date TEXT,

        is_amendment BOOLEAN,

        articles JSONB,
        amended_articles JSONB
    );
    """)

    conn.commit()
    cur.close()


# =====================================================
# CONSTANTS
# =====================================================

AMEND_TYPES = ["تعديل مادة", "إضافة مادة", "إلغاء مادة"]

AMEND_BADGE_CSS = {
    "تعديل مادة": "badge-edit",
    "إضافة مادة": "badge-add",
    "إلغاء مادة": "badge-del",
}

LAW_KINDS = ["قانون ج1", "قانون ج2"]


# =====================================================
# AUTH
# =====================================================

def authenticate(username, password):

    try:
        users = st.secrets.get("users", {"admin": "password"})
    except:
        users = {"admin": "password"}

    return users.get(username.strip()) == password.strip()


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_name = None


if not st.session_state.authenticated:

    st.markdown("""
    <div class="app-header">
        <div class="seal">🔐</div>
        <h1>تسجيل الدخول</h1>
        <div class="subtitle">منظومة مراجعة التشريعات</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login"):

        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")

        if st.form_submit_button("دخول", use_container_width=True, type="primary"):

            if authenticate(username, password):

                st.session_state.authenticated = True
                st.session_state.user_name = username
                st.rerun()

            else:
                st.error("بيانات الدخول غير صحيحة")

    st.stop()


# =====================================================
# STYLES
# =====================================================

def apply_styles():

    st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@300;400;600;700;900&display=swap');

:root {
    --navy:#0f1e3d;
    --navy-mid:#1a2f5a;
    --gold:#c9a84c;
    --gold-light:#e5c97a;
    --cream:#f8f4ed;
}

* {
    font-family:'Tajawal',sans-serif!important;
    direction:rtl;
    text-align:right;
}

.stApp {
    background:var(--navy);
}

.block-container {
    max-width:980px!important;
    padding:2rem 3rem!important;
}

/* Header */

.app-header {
    text-align:center;
    padding:2.5rem 0;
    border-bottom:1px solid rgba(201,168,76,.3);
}

.app-header h1 {
    font-family:'Amiri',serif!important;
    color:var(--gold);
}

.subtitle {
    color:rgba(255,255,255,.5);
}

/* Card */

.law-card {

    background:rgba(255,255,255,.05);
    border:1px solid rgba(201,168,76,.3);

    border-radius:14px;
    padding:1.5rem;

    margin:1.2rem 0;
}

.article-text {

    color:var(--cream);
    line-height:1.9;
    white-space:pre-wrap;
}

/* Amend */

.amend-section {

    background:rgba(201,168,76,.08);
    border:1px solid rgba(201,168,76,.4);

    border-radius:10px;
    padding:1rem;
}

/* Badges */

.badge-edit {
    background:rgba(59,130,246,.2);
    color:#93c5fd;
}

.badge-add {
    background:rgba(34,197,94,.2);
    color:#86efac;
}

.badge-del {
    background:rgba(239,68,68,.2);
    color:#fca5a5;
}

.amend-badge {

    padding:4px 12px;
    border-radius:20px;

    font-size:.75rem;
    font-weight:700;
}

#MainMenu,footer,header {
    visibility:hidden;
}

</style>
""", unsafe_allow_html=True)


apply_styles()


# =====================================================
# DATABASE HELPERS
# =====================================================

def load_laws(kind):

    conn = get_conn()

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
    SELECT * FROM laws
    WHERE kind = %s
    ORDER BY id
    """, (kind,))

    rows = cur.fetchall()

    cur.close()

    result = []

    for r in rows:

        result.append({
            "db_id": r["id"],

            "Leg_Name": r["leg_name"],
            "Leg_Number": r["leg_number"],
            "Year": r["year"],

            "Magazine_Number": r["magazine_number"],
            "Magazine_Page": r["magazine_page"],
            "Magazine_Date": r["magazine_date"],

            "is_amendment": r["is_amendment"],

            "Articles": r["articles"] or [],
            "amended_articles": r["amended_articles"] or []
        })

    return result


def save_law(law, kind):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE laws SET

        leg_name=%s,
        leg_number=%s,
        year=%s,

        magazine_number=%s,
        magazine_page=%s,
        magazine_date=%s,

        is_amendment=%s,

        articles=%s,
        amended_articles=%s

    WHERE id=%s
    """, (

        law["Leg_Name"],
        law["Leg_Number"],
        law["Year"],

        law["Magazine_Number"],
        law["Magazine_Page"],
        law["Magazine_Date"],

        law["is_amendment"],

        json.dumps(law["Articles"], ensure_ascii=False),
        json.dumps(law["amended_articles"], ensure_ascii=False),

        law["db_id"]
    ))

    conn.commit()
    cur.close()


# =====================================================
# TOAST
# =====================================================

def toast():

    st.toast(random.choice(["✅ محفوظ", "كفو", "تم الحفظ"]), icon="✅")


# =====================================================
# UI
# =====================================================

def show_law(idx, laws, kind):

    law = laws[idx]

    st.markdown(f"""
    <div class="law-card">

        <h3>{html_lib.escape(law["Leg_Name"])}</h3>

        <p>
        رقم: {law["Leg_Number"]} |
        سنة: {law["Year"]}
        </p>

    </div>
    """, unsafe_allow_html=True)


    st.markdown("### 📜 المواد")

    articles = law["Articles"]

    if not articles:

        if st.button("➕ إضافة أول مادة"):

            law["Articles"].append({

                "article_number": "1",
                "title": "المادة 1",

                "enforcement_date":
                datetime.now().strftime("%d-%m-%Y"),

                "text": ""
            })

            save_law(law, kind)
            toast()
            st.rerun()

        return


    options = [
        f"المادة {a['article_number']}"
        for a in articles
    ]

    art_idx = st.selectbox(
        "",
        range(len(options)),
        format_func=lambda i: options[i]
    )

    art = articles[art_idx]


    st.markdown(f"""
    <div class="law-card">

        <b>{art["title"]}</b>

        <div class="article-text">
        {html_lib.escape(art["text"])}
        </div>

        <small>
        تاريخ النفاذ: {art["enforcement_date"]}
        </small>

    </div>
    """, unsafe_allow_html=True)


    if st.button("✏️ تعديل المادة"):

        edit_article(law, art_idx, kind)



def edit_article(law, idx, kind):

    art = law["Articles"][idx]

    with st.form("edit"):

        st.subheader("تعديل المادة")

        num = st.text_input("الرقم", art["article_number"])
        title = st.text_input("العنوان", art["title"])
        date = st.text_input("التاريخ", art["enforcement_date"])
        text = st.text_area("النص", art["text"], height=300)

        col1, col2 = st.columns(2)

        if col1.form_submit_button("💾 حفظ"):

            law["Articles"][idx] = {

                "article_number": num,
                "title": title,

                "enforcement_date": date,
                "text": text
            }

            save_law(law, kind)
            toast()
            st.rerun()


        if col2.form_submit_button("إلغاء"):

            st.rerun()


# =====================================================
# MAIN
# =====================================================

def main():

    st.set_page_config(
        "مراجعة التشريعات",
        layout="wide",
        page_icon="⚖️"
    )

    init_db()


    st.sidebar.markdown(
        f"👤 {st.session_state.user_name}"
    )


    if st.sidebar.button("تسجيل الخروج"):

        st.session_state.clear()
        st.rerun()


    st.sidebar.markdown("### نوع القانون")

    kind = st.sidebar.radio("", LAW_KINDS)


    laws = load_laws(kind)


    if not laws:

        st.warning("لا توجد بيانات في القاعدة")

        return


    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0


    idx = st.session_state.current_idx


    show_law(idx, laws, kind)


    col1, col2 = st.columns(2)


    with col1:

        if idx > 0:

            if st.button("◄ السابق"):

                st.session_state.current_idx -= 1
                st.rerun()


    with col2:

        if idx < len(laws)-1:

            if st.button("التالي ►", type="primary"):

                st.session_state.current_idx += 1
                st.rerun()



if __name__ == "__main__":
    main()
