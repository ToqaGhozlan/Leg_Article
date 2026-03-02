import streamlit as st
import json
import html as html_lib
from datetime import datetime
import random
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from db import get_cursor, init_db

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
credentials_str = os.environ.get("CREDENTIALS_YAML")
if not credentials_str:
    st.error("لم يتم العثور على متغير CREDENTIALS_YAML في Railway – أضيفيه في Variables")
    st.stop()
try:
    config = yaml.safe_load(credentials_str)
except Exception as e:
    st.error(f"خطأ في تحليل بيانات المستخدمين: {str(e)}")
    st.stop()

authenticator = stauth.Authenticate(
    credentials = config['credentials'],
    cookie_name = config['cookie']['name'],
    cookie_key = config['cookie']['key'],
    cookie_expiry_days = config['cookie']['expiry_days'],
    preauthorized = config.get('preauthorized')
)

authenticator.login(
    location = 'main',
    key = 'login_form',
    fields = {'Form name': 'تسجيل الدخول'}
)

authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")

if authentication_status:
    st.session_state.authenticated = True
    st.session_state.user_name = name or username
elif authentication_status is False:
    st.error('اسم المستخدم أو كلمة المرور غير صحيحة')
elif authentication_status is None:
    st.warning('الرجاء إدخال اسم المستخدم وكلمة المرور')
    st.stop()

if not st.session_state.get('authenticated', False):
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
    .stApp {background:var(--navy);}
    .block-container {max-width:980px!important; padding:2rem 3rem!important;}
    .app-header {text-align:center; padding:2.5rem 0; border-bottom:1px solid rgba(201,168,76,.3);}
    .app-header h1 {font-family:'Amiri',serif!important; color:var(--gold);}
    .subtitle {color:rgba(255,255,255,.5);}
    .law-card {background:rgba(255,255,255,.05); border:1px solid rgba(201,168,76,.3); border-radius:14px; padding:1.5rem; margin:1.2rem 0;}
    .article-text {color:var(--cream); line-height:1.9; white-space:pre-wrap;}
    .amend-section {background:rgba(201,168,76,.08); border:1px solid rgba(201,168,76,.4); border-radius:10px; padding:1rem;}
    .badge-edit {background:rgba(59,130,246,.2); color:#93c5fd;}
    .badge-add {background:rgba(34,197,94,.2); color:#86efac;}
    .badge-del {background:rgba(239,68,68,.2); color:#fca5a5;}
    .amend-badge {padding:4px 12px; border-radius:20px; font-size:.75rem; font-weight:700;}
    #MainMenu,footer,header {visibility:hidden;}
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# =====================================================
# DATABASE HELPERS
# =====================================================
def load_laws(kind):
    try:
        with get_cursor() as cur:
            cur.execute("""
            SELECT * FROM laws
            WHERE kind = %s
            ORDER BY id
            """, (kind,))
            rows = cur.fetchall()
            laws_list = []
            for row in rows:
                laws_list.append({
                    "db_id": row["id"],
                    "Leg_Name": row["leg_name"],
                    "Leg_Number": row["leg_number"],
                    "Year": row["year"],
                    "Magazine_Number": row["magazine_number"],
                    "Magazine_Page": row["magazine_page"],
                    "Magazine_Date": row["magazine_date"],
                    "is_amendment": row["is_amendment"],
                    "Articles": row["articles"] or [],
                    "amended_articles": row["amended_articles"] or []
                })
            return laws_list
    except Exception as e:
        st.error(f"خطأ في تحميل القوانين: {str(e)}")
        return []

def save_law(law, kind):
    try:
        with get_cursor() as cur:
            cur.execute("""
            UPDATE laws SET
                leg_name = %s,
                leg_number = %s,
                year = %s,
                magazine_number = %s,
                magazine_page = %s,
                magazine_date = %s,
                is_amendment = %s,
                articles = %s::jsonb,
                amended_articles = %s::jsonb
            WHERE id = %s
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
    except Exception as e:
        st.error(f"خطأ في حفظ القانون: {str(e)}")

def toast():
    st.toast(random.choice(["✅ محفوظ", "كفو", "تم الحفظ"]), icon="✅")

# =====================================================
# MIGRATION دالة عامة لكلا النوعين
# =====================================================
def migrate_law_kind(kind, json_filename):
    json_path = f"app/{json_filename}"
    st.info(f"معالجة {kind} من الملف: {json_path}")
    if not os.path.exists(json_path):
        st.error(f"الملف {json_path} غير موجود!")
        return 0
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        num_items = len(data)
        st.info(f"تم قراءة {num_items} عنصر من {kind}")
        if num_items == 0:
            st.warning(f"ملف {json_filename} فارغ")
            return 0
        inserted = 0
        with get_cursor() as cur:
            for i, law in enumerate(data, 1):
                cur.execute("""
                INSERT INTO laws (
                    kind, leg_name, leg_number, year,
                    magazine_number, magazine_page, magazine_date,
                    is_amendment, articles, amended_articles
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """, (
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
                ))
                if cur.fetchone():
                    inserted += 1
        st.success(f"{kind}: أُضيف {inserted} سجل جديد")
        return inserted
    except json.JSONDecodeError as e:
        st.error(f"خطأ في صيغة JSON لـ {kind}: {str(e)}")
        return 0
    except Exception as e:
        st.error(f"خطأ أثناء معالجة {kind}: {str(e)}")
        return 0

# =====================================================
# UI Functions
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
                "enforcement_date": datetime.now().strftime("%d-%m-%Y"),
                "text": ""
            })
            save_law(law, kind)
            toast()
            st.rerun()
        return

    options = [f"المادة {a['article_number']}" for a in articles]
    art_idx = st.selectbox("", range(len(options)), format_func=lambda i: options[i])
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

    try:
        init_db()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return

    # تشغيل الـ migration مرة واحدة فقط لكلا النوعين
    #if "migration_done" not in st.session_state:
    st.subheader("تهيئة البيانات الأولية")
    migrate_law_kind("قانون ج1", "V02_Laws_P1.json")
    migrate_law_kind("قانون ج2", "V02_Laws_P2.json")
    st.session_state.migration_done = True
    st.success("تمت محاولة تحميل البيانات لكلا النوعين")
    st.rerun()  # عشان يختفي قسم التهيئة ويظهر البيانات

    st.sidebar.markdown(f"👤 {st.session_state.user_name}")
    authenticator.logout("تسجيل الخروج", location="sidebar", key="logout_widget")

    st.sidebar.markdown("### نوع القانون")
    kind = st.sidebar.radio("", LAW_KINDS)

    laws = load_laws(kind)
    if not laws:
        st.warning(f"لا توجد بيانات في القاعدة لـ {kind}")
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
