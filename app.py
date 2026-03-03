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
KIND_TO_TABLE = {
    "قانون ج1": {"original": "laws_p1_original", "modified": "laws_p1_modified"},
    "قانون ج2": {"original": "laws_p2_original", "modified": "laws_p2_modified"},
}

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
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days'],
    preauthorized=config.get('preauthorized')
)
authenticator.login(
    location='main',
    key='login_form',
    fields={'Form name': 'تسجيل الدخول'}
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
def row_to_law(row):
    return {
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
    }

def load_laws(kind):
    table_original = KIND_TO_TABLE[kind]["original"]
    table_modified = KIND_TO_TABLE[kind]["modified"]
    try:
        with get_cursor() as cur:
            # حاول جلب النسخة المعدلة أولاً
            cur.execute(f"SELECT * FROM {table_modified} ORDER BY id")
            rows = cur.fetchall()
            
            # إذا ما فيش في modified → جيب من original
            if not rows:
                cur.execute(f"SELECT * FROM {table_original} ORDER BY id")
                rows = cur.fetchall()
            
            laws_list = [row_to_law(row) for row in rows]
            if not laws_list:
                st.warning(f"لا توجد قوانين في {table_original} ولا في {table_modified}")
            return laws_list
    except Exception as e:
        st.error(f"خطأ في تحميل القوانين: {str(e)}")
        return []

def save_law(law, kind):
    table_modified = KIND_TO_TABLE[kind]["modified"]
    leg_number = law["Leg_Number"]
    try:
        with get_cursor() as cur:
            # تحقق إذا موجود في modified
            cur.execute(f"SELECT id FROM {table_modified} WHERE leg_number = %s", (leg_number,))
            exists = cur.fetchone() is not None

            if exists:
                # تحديث
                cur.execute(f"""
                    UPDATE {table_modified} SET
                        leg_name = %s,
                        leg_number = %s,
                        year = %s,
                        magazine_number = %s,
                        magazine_page = %s,
                        magazine_date = %s,
                        is_amendment = %s,
                        articles = %s::jsonb,
                        amended_articles = %s::jsonb
                    WHERE leg_number = %s
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
                    leg_number
                ))
            else:
                # إدراج نسخة جديدة في modified
                cur.execute(f"""
                    INSERT INTO {table_modified} (
                        leg_name, leg_number, year,
                        magazine_number, magazine_page, magazine_date,
                        is_amendment, articles, amended_articles
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
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
                ))
        toast()
    except Exception as e:
        st.error(f"خطأ في حفظ القانون: {str(e)}")

def toast():
    st.toast(random.choice(["✅ محفوظ", "كفو", "تم الحفظ"]), icon="✅")

# =====================================================
# Migration Status Helpers (كما هي)
# =====================================================
def has_migration_run(name):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM migration_status WHERE migration_name = %s", (name,))
            result = cur.fetchone()
            st.info(f"التحقق من حالة الـ migration '{name}': {'تم' if result else 'لم يتم'}")
            return result is not None
    except Exception as e:
        st.error(f"خطأ أثناء التحقق من migration_status: {str(e)}")
        return False

def mark_migration_done(name):
    try:
        with get_cursor() as cur:
            cur.execute("""
            INSERT INTO migration_status (migration_name)
            VALUES (%s)
            ON CONFLICT (migration_name) DO NOTHING
            """, (name,))
        st.info(f"تم تسجيل نجاح الـ migration: {name}")
    except Exception as e:
        st.error(f"خطأ في تسجيل نجاح الـ migration: {str(e)}")

# =====================================================
# MIGRATION دالة عامة (كما هي)
# =====================================================
def migrate_law_kind(kind, json_filename, table_original):
    json_path = f"app/{json_filename}"
    st.info(f"جاري معالجة {kind} من: {json_path}")
    
    if not os.path.exists(json_path):
        st.error(f"الملف غير موجود: {json_path}")
        return 0
    
    try:
        with open(json_path, encoding="utf-8-sig") as f:
            data = json.load(f)
        num_items = len(data)
        st.info(f"تم قراءة {num_items} عنصر من {kind}")
        
        if num_items == 0:
            st.warning(f"الملف فارغ: {json_filename}")
            return 0
        
        inserted = 0
        with get_cursor() as cur:
            for i, law in enumerate(data, 1):
                cur.execute(f"""
                INSERT INTO {table_original} (
                    leg_name, leg_number, year,
                    magazine_number, magazine_page, magazine_date,
                    is_amendment, articles, amended_articles
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """, (
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
        
        st.success(f"{kind}: تم إضافة {inserted} سجل جديد (من أصل {num_items})")
        return inserted
    
    except json.JSONDecodeError as e:
        st.error(f"خطأ في قراءة JSON لـ {kind}: {str(e)}")
        return 0
    except Exception as e:
        st.error(f"خطأ عام أثناء معالجة {kind}: {str(e)}")
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
            add_article(law, kind, position=0)
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
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✏️ تعديل المادة"):
            edit_article(law, art_idx, kind)
    with col2:
        if st.button("➕ إضافة مادة بعد هذه"):
            add_article(law, kind, position=art_idx + 1)
    with col3:
        if st.button("➕ إضافة مادة في النهاية"):
            add_article(law, kind, position=len(articles))

    # قسم التعديلات التشريعية
    st.markdown("### 🔄 التعديلات التشريعية")
    amended = law["amended_articles"]
    if amended:
        for amend in amended:
            badge_class = AMEND_BADGE_CSS.get(amend["type"], "")
            st.markdown(f"""
            <div class="amend-section">
                <span class="amend-badge {badge_class}">{amend["type"]}</span>
                <b>المادة: {amend.get("article_number", "")}</b>
                <div>{html_lib.escape(amend.get("text", ""))}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لا توجد تعديلات تشريعية بعد.")
    
    if st.button("➕ إضافة تعديل تشريعي"):
        add_amendment(law, kind)

def add_article(law, kind, position):
    with st.form("add_article"):
        st.subheader("إضافة مادة جديدة")
        articles = law["Articles"]
        suggested_num = str(len(articles) + 1) if position == len(articles) else str(int(articles[position-1]["article_number"]) + 1 if articles[position-1]["article_number"].isdigit() else "")
        num = st.text_input("الرقم (اقتراح تلقائي)", value=suggested_num)
        title = st.text_input("العنوان", value=f"المادة {num}")
        date = st.text_input("التاريخ", value=datetime.now().strftime("%d-%m-%Y"))
        text = st.text_area("النص", height=300)
        col1, col2 = st.columns(2)
        if col1.form_submit_button("💾 حفظ"):
            new_art = {
                "article_number": num,
                "title": title,
                "enforcement_date": date,
                "text": text
            }
            law["Articles"].insert(position, new_art)
            save_law(law, kind)
            toast()
            st.rerun()
        if col2.form_submit_button("إلغاء"):
            st.rerun()

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

def add_amendment(law, kind):
    with st.form("add_amendment"):
        st.subheader("إضافة تعديل تشريعي")
        amend_type = st.selectbox("نوع التعديل", AMEND_TYPES)
        article_num = st.text_input("رقم المادة المعدلة")
        text = st.text_area("نص التعديل", height=200)
        col1, col2 = st.columns(2)
        if col1.form_submit_button("💾 حفظ"):
            new_amend = {
                "type": amend_type,
                "article_number": article_num,
                "text": text
            }
            law["amended_articles"].append(new_amend)
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
    
    # التحميل الأولي
    migration_name = "initial_data_load_v1"
    if not has_migration_run(migration_name):
        st.subheader("تهيئة البيانات الأولية – جاري التحميل مرة واحدة فقط")
        try:
            inserted1 = migrate_law_kind("قانون ج1", "V02_Laws_P1.json", "laws_p1_original")
            inserted2 = migrate_law_kind("قانون ج2", "V02_Laws_P2.json", "laws_p2_original")
            total = inserted1 + inserted2
            mark_migration_done(migration_name)
            st.success(f"تم التحميل بنجاح! أُضيف {total} سجل جديد")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ كبير أثناء التحميل الأولي: {str(e)}")
    
    st.sidebar.markdown(f"👤 {st.session_state.user_name}")
    authenticator.logout("تسجيل الخروج", location="sidebar", key="logout_widget")
    st.sidebar.markdown("### نوع القانون")
    kind = st.sidebar.radio("اختر نوع القانون", LAW_KINDS)  # ← أصلحنا التحذير هنا
    
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
