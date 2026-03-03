# app.py - النسخة الكاملة المحسّنة
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
    "تعديل مادة":  "badge-edit",
    "إضافة مادة":  "badge-add",
    "إلغاء مادة":  "badge-del",
    "استعادة مادة": "badge-add",
}
LAW_KINDS = ["قانون ج1", "قانون ج2"]
KIND_TO_TABLE = {
    "قانون ج1": {"original": "laws_p1_original", "modified": "laws_p1_modified"},
    "قانون ج2": {"original": "laws_p2_original", "modified": "laws_p2_modified"},
}

# =====================================================
# PAGE CONFIG (must be first Streamlit call)
# =====================================================
st.set_page_config(
    page_title="مراجعة التشريعات",
    layout="wide",
    page_icon="⚖️",
    initial_sidebar_state="expanded"
)

# =====================================================
# STYLES
# =====================================================
def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Tajawal:wght@300;400;500;600;700;900&display=swap');

    :root {
        --navy:       #0a1628;
        --navy-mid:   #0f2044;
        --navy-card:  #132252;
        --navy-light: #1a2f6a;
        --gold:       #c9a84c;
        --gold-light: #e8c96a;
        --gold-dim:   #7a6030;
        --cream:      #f0e8d4;
        --cream-dim:  #b0a080;
        --red:        #e05555;
        --green:      #4caf82;
        --blue:       #5588e0;
        --border:     rgba(201,168,76,0.25);
        --border-hover: rgba(201,168,76,0.55);
        --glass:      rgba(255,255,255,0.04);
        --glass-hover:rgba(255,255,255,0.08);
        --shadow:     0 8px 32px rgba(0,0,0,0.4);
        --radius:     14px;
        --radius-sm:  8px;
    }

    * { font-family: 'Tajawal', sans-serif !important; direction: rtl; text-align: right; box-sizing: border-box; }

    /* ── APP BACKGROUND ── */
    .stApp {
        background: var(--navy);
        background-image:
            radial-gradient(ellipse at 20% 10%, rgba(201,168,76,0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 90%, rgba(21,45,110,0.8) 0%, transparent 50%);
    }
    .block-container { max-width: 1100px !important; padding: 1.5rem 2.5rem !important; }

    /* ── HEADER ── */
    .app-header {
        text-align: center;
        padding: 2rem 0 1.5rem;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
        position: relative;
    }
    .app-header::after {
        content: '';
        position: absolute;
        bottom: -1px; left: 50%; transform: translateX(-50%);
        width: 120px; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }
    .app-header h1 {
        font-family: 'Amiri', serif !important;
        color: var(--gold) !important;
        font-size: 2.4rem !important;
        margin: 0 0 0.3rem !important;
        text-shadow: 0 0 40px rgba(201,168,76,0.3);
        letter-spacing: 1px;
    }
    .header-sub {
        color: var(--cream-dim);
        font-size: 0.9rem;
        margin: 0;
    }

    /* ── LAW CARD (header block) ── */
    .law-header-card {
        background: linear-gradient(135deg, var(--navy-card) 0%, var(--navy-light) 100%);
        border: 1px solid var(--border-hover);
        border-radius: var(--radius);
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow), inset 0 1px 0 rgba(201,168,76,0.15);
        position: relative;
        overflow: hidden;
    }
    .law-header-card::before {
        content: '⚖';
        position: absolute;
        left: 1.5rem; top: 50%; transform: translateY(-50%);
        font-size: 3rem;
        opacity: 0.05;
    }
    .law-title {
        font-family: 'Amiri', serif !important;
        color: var(--gold-light) !important;
        font-size: 1.6rem !important;
        margin: 0 0 0.7rem !important;
        line-height: 1.5;
    }
    .law-meta {
        display: flex;
        gap: 1.5rem;
        flex-wrap: wrap;
    }
    .meta-chip {
        background: rgba(201,168,76,0.1);
        border: 1px solid rgba(201,168,76,0.2);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 0.82rem;
        color: var(--cream-dim);
    }
    .meta-chip b { color: var(--gold); }

    /* ── ARTICLE CARD ── */
    .article-card {
        background: var(--glass);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.4rem 1.8rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .article-card:hover {
        background: var(--glass-hover);
        border-color: var(--border-hover);
        transform: translateX(-3px);
    }
    .article-card.selected {
        background: rgba(201,168,76,0.07);
        border-color: var(--gold);
        box-shadow: 0 0 0 1px rgba(201,168,76,0.3), var(--shadow);
    }
    /* ── DELETED ARTICLE STYLE ── */
    .article-card.deleted {
        background: rgba(224,85,85,0.04);
        border-color: rgba(224,85,85,0.25);
        border-right: 3px solid rgba(224,85,85,0.5);
        opacity: 0.7;
    }
    .article-card.deleted .article-title-text,
    .article-card.deleted .article-body {
        text-decoration: line-through;
        text-decoration-color: rgba(224,85,85,0.6);
        text-decoration-thickness: 1.5px;
        color: var(--cream-dim) !important;
    }
    .deleted-stamp {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(224,85,85,0.15);
        border: 1px solid rgba(224,85,85,0.3);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        color: #fca5a5;
        font-weight: 700;
        margin-right: 0.5rem;
    }
    .article-num {
        display: inline-block;
        background: linear-gradient(135deg, var(--gold-dim), var(--gold));
        color: var(--navy) !important;
        font-weight: 900;
        font-size: 0.75rem;
        padding: 2px 10px;
        border-radius: 12px;
        margin-left: 0.6rem;
        letter-spacing: 0.5px;
    }
    .article-num.deleted-num {
        background: linear-gradient(135deg, #7a3030, #e05555);
    }
    .article-title-text {
        color: var(--cream);
        font-size: 1rem;
        font-weight: 600;
    }
    .article-date { color: var(--cream-dim); font-size: 0.78rem; margin-top: 0.3rem; }
    .article-body {
        color: var(--cream);
        line-height: 2;
        white-space: pre-wrap;
        font-size: 0.96rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
    }

    /* ── AMENDMENT BADGES ── */
    .badge-wrap { display: inline-flex; align-items: center; gap: 0.4rem; }
    .amend-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.73rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .badge-edit { background: rgba(85,136,224,.18); color: #93c5fd; border: 1px solid rgba(85,136,224,.3); }
    .badge-add  { background: rgba(76,175,130,.18); color: #86efac; border: 1px solid rgba(76,175,130,.3); }
    .badge-del  { background: rgba(224,85,85,.18);  color: #fca5a5; border: 1px solid rgba(224,85,85,.3); }

    /* ── AMENDMENT CARD ── */
    .amend-card {
        background: rgba(201,168,76,0.05);
        border: 1px solid rgba(201,168,76,0.2);
        border-right: 3px solid var(--gold);
        border-radius: var(--radius-sm);
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.7rem;
    }
    .amend-article-ref {
        color: var(--gold);
        font-weight: 700;
        font-size: 0.85rem;
        margin: 0.3rem 0;
    }
    .amend-text { color: var(--cream-dim); font-size: 0.9rem; line-height: 1.7; }

    /* ── SECTION DIVIDER ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin: 1.8rem 0 1rem;
        color: var(--gold);
        font-weight: 700;
        font-size: 1rem;
    }
    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, var(--gold-dim), transparent);
    }

    /* ── NAV BUTTONS ── */
    .law-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        border-top: 1px solid var(--border);
        margin-top: 1rem;
    }
    .law-counter {
        background: rgba(201,168,76,0.1);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 4px 18px;
        color: var(--gold);
        font-size: 0.85rem;
    }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background: var(--navy-mid) !important;
        border-left: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--cream) !important; }
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
    }
    .sidebar-logo span {
        font-size: 2rem;
    }
    .user-chip {
        background: rgba(201,168,76,0.1);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.6rem 1rem;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: var(--cream-dim) !important;
    }
    .user-chip b { color: var(--gold) !important; }

    /* ── FORMS ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: var(--navy-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--cream) !important;
        border-radius: var(--radius-sm) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 2px rgba(201,168,76,0.15) !important;
    }

    /* ── STBUTTON overrides ── */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        transition: all 0.15s !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--gold-dim), var(--gold)) !important;
        color: var(--navy) !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(201,168,76,0.35) !important;
    }
    .stButton > button[kind="secondary"] {
        background: var(--glass) !important;
        border: 1px solid var(--border) !important;
        color: var(--cream) !important;
    }

    /* ── MISC ── */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: var(--cream-dim);
    }
    .empty-state .icon { font-size: 3rem; margin-bottom: 0.5rem; }
    hr { border-color: var(--border) !important; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

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
    st.stop()
elif authentication_status is None:
    st.warning('الرجاء إدخال اسم المستخدم وكلمة المرور')
    st.stop()
if not st.session_state.get('authenticated', False):
    st.stop()

apply_styles()

# =====================================================
# DATABASE HELPERS
# =====================================================
def load_laws(kind):
    table_original = KIND_TO_TABLE[kind]["original"]
    table_modified  = KIND_TO_TABLE[kind]["modified"]
    try:
        with get_cursor() as cur:
            cur.execute(f"SELECT * FROM {table_original} ORDER BY id")
            original_rows = cur.fetchall()
            laws_dict = {row["leg_number"]: row_to_law(row) for row in original_rows}

            cur.execute(f"SELECT * FROM {table_modified} ORDER BY id")
            modified_rows = cur.fetchall()
            for row in modified_rows:
                laws_dict[row["leg_number"]] = row_to_law(row)

            return list(laws_dict.values())
    except Exception as e:
        st.error(f"خطأ في تحميل القوانين: {str(e)}")
        return []

def row_to_law(row):
    return {
        "db_id":          row["id"],
        "Leg_Name":       row["leg_name"],
        "Leg_Number":     row["leg_number"],
        "Year":           row["year"],
        "Magazine_Number":row["magazine_number"],
        "Magazine_Page":  row["magazine_page"],
        "Magazine_Date":  row["magazine_date"],
        "is_amendment":   row["is_amendment"],
        "Articles":       row["articles"] or [],
        "amended_articles": row["amended_articles"] or []
    }

def save_law(law, kind):
    """حفظ القانون كاملاً في جدول modified (upsert)."""
    table_modified = KIND_TO_TABLE[kind]["modified"]
    table_original = KIND_TO_TABLE[kind]["original"]
    leg_number = law["Leg_Number"]
    try:
        with get_cursor() as cur:
            cur.execute(f"SELECT id FROM {table_modified} WHERE leg_number = %s", (leg_number,))
            exists = cur.fetchone()
            if exists:
                cur.execute(f"""
                UPDATE {table_modified} SET
                    leg_name=%s, year=%s, magazine_number=%s,
                    magazine_page=%s, magazine_date=%s,
                    is_amendment=%s, articles=%s::jsonb, amended_articles=%s::jsonb
                WHERE leg_number=%s
                """, (
                    law["Leg_Name"], law["Year"], law["Magazine_Number"],
                    law["Magazine_Page"], law["Magazine_Date"],
                    law["is_amendment"],
                    json.dumps(law["Articles"], ensure_ascii=False),
                    json.dumps(law["amended_articles"], ensure_ascii=False),
                    leg_number
                ))
            else:
                # نسخ من original أولاً ثم تحديث
                cur.execute(f"""
                INSERT INTO {table_modified}
                    (leg_name,leg_number,year,magazine_number,magazine_page,
                     magazine_date,is_amendment,articles,amended_articles)
                SELECT leg_name,leg_number,year,magazine_number,magazine_page,
                       magazine_date,is_amendment,articles,amended_articles
                FROM {table_original} WHERE leg_number=%s
                """, (leg_number,))
                cur.execute(f"""
                UPDATE {table_modified} SET
                    articles=%s::jsonb, amended_articles=%s::jsonb
                WHERE leg_number=%s
                """, (
                    json.dumps(law["Articles"], ensure_ascii=False),
                    json.dumps(law["amended_articles"], ensure_ascii=False),
                    leg_number
                ))
    except Exception as e:
        st.error(f"خطأ في حفظ القانون: {str(e)}")
        raise

def toast(msg=None):
    msgs = ["✅ تم الحفظ بنجاح", "💾 محفوظ", "✅ تمّ"]
    st.toast(msg or random.choice(msgs), icon="✅")

# =====================================================
# MIGRATION HELPERS
# =====================================================
def has_migration_run(name):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM migration_status WHERE migration_name=%s", (name,))
            return cur.fetchone() is not None
    except Exception:
        return False

def mark_migration_done(name):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO migration_status (migration_name) VALUES (%s) ON CONFLICT DO NOTHING",
            (name,)
        )

def run_initial_migration():
    migration_name = "initial_data_load_v1"
    if has_migration_run(migration_name):
        return True  # already done

    with st.spinner("⚙️ جاري تحميل البيانات الأولية – مرة واحدة فقط..."):
        try:
            total = 0
            for kind, filename, table in [
                ("قانون ج1", "V02_Laws_P1.json", "laws_p1_original"),
                ("قانون ج2", "V02_Laws_P2.json", "laws_p2_original"),
            ]:
                json_path = f"app/{filename}"
                if not os.path.exists(json_path):
                    st.error(f"الملف غير موجود: {json_path}")
                    continue
                with open(json_path, encoding="utf-8-sig") as f:
                    data = json.load(f)
                inserted = 0
                with get_cursor() as cur:
                    for law in data:
                        cur.execute(f"""
                        INSERT INTO {table}
                            (leg_name,leg_number,year,magazine_number,magazine_page,
                             magazine_date,is_amendment,articles,amended_articles)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)
                        """, (
                            law.get("Leg_Name"), law.get("Leg_Number"), law.get("Year"),
                            law.get("Magazine_Number"), law.get("Magazine_Page"),
                            law.get("Magazine_Date"), law.get("is_amendment", False),
                            json.dumps(law.get("Articles", []), ensure_ascii=False),
                            json.dumps(law.get("amended_articles", []), ensure_ascii=False),
                        ))
                        inserted += 1
                total += inserted
            mark_migration_done(migration_name)
            st.success(f"✅ تم تحميل {total} قانون بنجاح!")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ في التحميل الأولي: {e}")
            return False
    return True

# =====================================================
# UI COMPONENTS
# =====================================================
def render_header():
    st.markdown("""
    <div class="app-header">
        <h1>⚖ نظام مراجعة التشريعات</h1>
        <p class="header-sub">مراجعة وتعديل القوانين والتشريعات</p>
    </div>
    """, unsafe_allow_html=True)

def render_law_header(law, idx, total):
    amendment_badge = ""
    if law.get("is_amendment"):
        amendment_badge = '<span class="amend-badge badge-edit" style="font-size:0.8rem;">تعديل تشريعي</span>'
    st.markdown(f"""
    <div class="law-header-card">
        <div class="law-title">{html_lib.escape(law["Leg_Name"])} {amendment_badge}</div>
        <div class="law-meta">
            <span class="meta-chip"><b>رقم:</b> {law["Leg_Number"]}</span>
            <span class="meta-chip"><b>السنة:</b> {law["Year"] or '—'}</span>
            <span class="meta-chip"><b>المجلة:</b> {law["Magazine_Number"] or '—'}</span>
            <span class="meta-chip"><b>الصفحة:</b> {law["Magazine_Page"] or '—'}</span>
            <span class="meta-chip"><b>التاريخ:</b> {law["Magazine_Date"] or '—'}</span>
        </div>
        <div style="margin-top:0.8rem;">
            <span class="law-counter">{idx + 1} / {total}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_law(idx, laws, kind):
    law = laws[idx]
    render_law_header(law, idx, len(laws))

    # ── Articles Section ──
    st.markdown('<div class="section-header">📜 مواد القانون</div>', unsafe_allow_html=True)

    articles = law["Articles"]
    if not articles:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📄</div>
            <div>لا توجد مواد بعد</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Article selector — كل المواد تظهر، المحذوفة تُعلَّم
        def art_label(a):
            deleted_mark = " 🚫" if a.get("deleted") else ""
            return f"المادة {a['article_number']}{deleted_mark} — {a.get('title','')[:35]}"

        art_idx = st.selectbox(
            "اختر مادة",
            range(len(articles)),
            format_func=lambda i: art_label(articles[i]),
            key=f"art_select_{idx}"
        )
        art = articles[art_idx]
        is_deleted = art.get("deleted", False)

        # ── Render article card ──
        is_deleted  = art.get("deleted", False)
        num_class   = "article-num deleted-num" if is_deleted else "article-num"
        card_class  = "article-card selected deleted" if is_deleted else "article-card selected"
        del_stamp   = '<span class="deleted-stamp">🚫 ملغاة</span>' if is_deleted else ""
        del_info    = ""
        if is_deleted:
            by = html_lib.escape(art.get("deleted_by",""))
            at = html_lib.escape(art.get("deleted_at",""))
            del_info = f'<div style="color:#fca5a5;font-size:0.78rem;margin-top:0.4rem;">🗑️ حُذفت {"بواسطة " + by if by else ""} {"في " + at if at else ""}</div>'

        art_num   = html_lib.escape(str(art.get("article_number","")))
        art_title = html_lib.escape(str(art.get("title","")))
        art_date  = html_lib.escape(str(art.get("enforcement_date","—")))
        art_text  = str(art.get("text",""))

        # الهيدر فقط في HTML — النص في st.write منفصل لتفادي كسر الـ parser
        st.markdown(f"""
<div class="{card_class}">
<div><span class="{num_class}">مادة {art_num}</span>
<span class="article-title-text">{art_title}</span>
{del_stamp}</div>
<div class="article-date">📅 تاريخ النفاذ: {art_date}</div>
{del_info}
<hr style="border-color:rgba(201,168,76,0.2);margin:0.8rem 0 0.6rem;">
</div>
        """, unsafe_allow_html=True)

        # نص المادة منفصل — آمن من أي HTML injection
        text_style = (
            "text-decoration: line-through; text-decoration-color: rgba(224,85,85,0.6); "
            "color: #b0a080; line-height: 2; white-space: pre-wrap; font-size: 0.96rem; "
            "padding: 0 0.5rem;"
        ) if is_deleted else (
            "color: #f0e8d4; line-height: 2; white-space: pre-wrap; font-size: 0.96rem; "
            "padding: 0 0.5rem;"
        )
        st.markdown(
            f'<div style="{text_style}">{html_lib.escape(art_text)}</div>',
            unsafe_allow_html=True
        )

        # ── Action buttons (مختلفة إذا المادة محذوفة) ──
        if is_deleted:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("↩️ استعادة المادة", key=f"btn_restore_{idx}_{art_idx}", use_container_width=True):
                    law["Articles"][art_idx].pop("deleted", None)
                    law["Articles"][art_idx].pop("deleted_at", None)
                    law["Articles"][art_idx].pop("deleted_by", None)
                    law["amended_articles"].append({
                        "type": "استعادة مادة",
                        "article_number": art["article_number"],
                        "text": art.get("text",""),
                        "restored_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "restored_by": st.session_state.get("user_name","")
                    })
                    save_law(law, kind)
                    toast("↩️ تمت الاستعادة")
                    st.rerun()
        else:
            col1, col2, col3, col4 = st.columns([1,1,1,1])
            with col1:
                if st.button("✏️ تعديل المادة", key=f"btn_edit_{idx}_{art_idx}", use_container_width=True):
                    st.session_state["action"] = ("edit", idx, art_idx)
                    st.rerun()
            with col2:
                if st.button("🗑️ حذف المادة", key=f"btn_del_{idx}_{art_idx}", use_container_width=True):
                    st.session_state["action"] = ("confirm_delete", idx, art_idx)
                    st.rerun()
            with col3:
                if st.button("➕ مادة بعد هذه", key=f"btn_add_after_{idx}_{art_idx}", use_container_width=True):
                    st.session_state["action"] = ("add", idx, art_idx + 1)
                    st.rerun()
            with col4:
                if st.button("➕ مادة في النهاية", key=f"btn_add_end_{idx}", use_container_width=True):
                    st.session_state["action"] = ("add", idx, len(articles))
                    st.rerun()

        # ── Confirm Delete (soft delete: set flag, keep in list) ──
        action = st.session_state.get("action")
        if action and action[0] == "confirm_delete" and action[1] == idx and action[2] == art_idx:
            st.warning(f"⚠️ هل أنت متأكد من إلغاء **المادة {art['article_number']}**؟ ستبقى ظاهرة كمحذوفة.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ نعم، ألغِ المادة", type="primary", key="confirm_del_yes"):
                    # soft delete: نضيف flag بدل الحذف الكامل
                    law["Articles"][art_idx]["deleted"]    = True
                    law["Articles"][art_idx]["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    law["Articles"][art_idx]["deleted_by"] = st.session_state.get("user_name","")
                    law["amended_articles"].append({
                        "type": "إلغاء مادة",
                        "article_number": art["article_number"],
                        "text": art.get("text",""),
                        "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "deleted_by": st.session_state.get("user_name","")
                    })
                    save_law(law, kind)
                    st.session_state.pop("action", None)
                    toast("🗑️ تم إلغاء المادة")
                    st.rerun()
            with c2:
                if st.button("❌ إلغاء", key="confirm_del_no"):
                    st.session_state.pop("action", None)
                    st.rerun()

    # ── Add Article Form ──
    action = st.session_state.get("action")
    if action and action[0] == "add" and action[1] == idx:
        position = action[2]
        st.markdown('<div class="section-header">➕ إضافة مادة جديدة</div>', unsafe_allow_html=True)
        with st.form(f"form_add_art_{idx}_{position}"):
            suggested = str(position + 1)
            col_a, col_b = st.columns(2)
            with col_a:
                num = st.text_input("رقم المادة", value=suggested)
                title = st.text_input("عنوان المادة", value=f"المادة {suggested}")
            with col_b:
                date = st.text_input("تاريخ النفاذ", value=datetime.now().strftime("%d-%m-%Y"))
            text = st.text_area("نص المادة", height=200)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 حفظ", type="primary"):
                new_art = {
                    "article_number": num,
                    "title": title,
                    "enforcement_date": date,
                    "text": text
                }
                law["Articles"].insert(position, new_art)
                law["amended_articles"].append({
                    "type": "إضافة مادة",
                    "article_number": num,
                    "text": text,
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "added_by": st.session_state.get("user_name", "")
                })
                save_law(law, kind)
                st.session_state.pop("action", None)
                toast("✅ تمت الإضافة")
                st.rerun()
            if c2.form_submit_button("❌ إلغاء"):
                st.session_state.pop("action", None)
                st.rerun()

    # ── Edit Article Form ──
    if action and action[0] == "edit" and action[1] == idx:
        art_idx_edit = action[2]
        art_edit = law["Articles"][art_idx_edit]
        st.markdown('<div class="section-header">✏️ تعديل المادة</div>', unsafe_allow_html=True)
        with st.form(f"form_edit_art_{idx}_{art_idx_edit}"):
            col_a, col_b = st.columns(2)
            with col_a:
                num   = st.text_input("رقم المادة", value=art_edit["article_number"])
                title = st.text_input("عنوان المادة", value=art_edit.get("title",""))
            with col_b:
                date  = st.text_input("تاريخ النفاذ", value=art_edit.get("enforcement_date",""))
            old_text = art_edit.get("text","")
            text = st.text_area("نص المادة", value=old_text, height=250)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 حفظ التعديل", type="primary"):
                law["Articles"][art_idx_edit] = {
                    "article_number": num,
                    "title": title,
                    "enforcement_date": date,
                    "text": text
                }
                law["amended_articles"].append({
                    "type": "تعديل مادة",
                    "article_number": num,
                    "text": text,
                    "original_text": old_text,
                    "edited_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "edited_by": st.session_state.get("user_name", "")
                })
                save_law(law, kind)
                st.session_state.pop("action", None)
                toast("✅ تم حفظ التعديل")
                st.rerun()
            if c2.form_submit_button("❌ إلغاء"):
                st.session_state.pop("action", None)
                st.rerun()

    # ── Amendments Section ──
    st.markdown('<div class="section-header">🔄 سجل التعديلات التشريعية</div>', unsafe_allow_html=True)
    amended = law.get("amended_articles", [])
    if amended:
        for amend in reversed(amended):  # الأحدث أولاً
            badge_class = AMEND_BADGE_CSS.get(amend.get("type",""), "badge-edit")
            article_ref = amend.get("article_number", "")
            time_str = amend.get("edited_at") or amend.get("added_at") or amend.get("deleted_at") or ""
            user_str = amend.get("edited_by") or amend.get("added_by") or amend.get("deleted_by") or ""
            preview = (amend.get("text","") or "")[:120]
            st.markdown(f"""
            <div class="amend-card">
                <div class="badge-wrap">
                    <span class="amend-badge {badge_class}">{amend.get("type","")}</span>
                    {f'<span class="amend-article-ref">المادة {article_ref}</span>' if article_ref else ''}
                    {f'<span style="color:var(--cream-dim);font-size:0.78rem;">🕐 {time_str}</span>' if time_str else ''}
                    {f'<span style="color:var(--cream-dim);font-size:0.78rem;">👤 {user_str}</span>' if user_str else ''}
                </div>
                <div class="amend-text">{html_lib.escape(preview)}{"..." if len(amend.get("text","")) > 120 else ""}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:var(--cream-dim);font-size:0.9rem;padding:0.5rem 0;">لا توجد تعديلات مسجّلة.</div>', unsafe_allow_html=True)

    # ── Add Manual Amendment ──
    if st.button("📝 إضافة تعديل تشريعي يدوي", key=f"btn_amend_{idx}"):
        st.session_state["action"] = ("add_amendment", idx)
        st.rerun()

    if action and action[0] == "add_amendment" and action[1] == idx:
        with st.form(f"form_add_amend_{idx}"):
            amend_type   = st.selectbox("نوع التعديل", AMEND_TYPES)
            article_num  = st.text_input("رقم المادة المعدلة")
            text         = st.text_area("نص التعديل", height=150)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 حفظ", type="primary"):
                law["amended_articles"].append({
                    "type": amend_type,
                    "article_number": article_num,
                    "text": text,
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "added_by": st.session_state.get("user_name","")
                })
                save_law(law, kind)
                st.session_state.pop("action", None)
                toast()
                st.rerun()
            if c2.form_submit_button("❌ إلغاء"):
                st.session_state.pop("action", None)
                st.rerun()

# =====================================================
# MAIN
# =====================================================
def main():
    try:
        init_db()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return

    # ── One-time migration (safe for concurrent users) ──
    run_initial_migration()

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo"><span>⚖️</span><br>
        <b style="color:var(--gold);font-size:1rem;">التشريعات</b></div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="user-chip">👤 <b>{st.session_state.user_name}</b></div>
        """, unsafe_allow_html=True)
        authenticator.logout("🚪 تسجيل الخروج", location="sidebar", key="logout_widget")
        st.markdown("---")
        st.markdown("**📂 نوع القانون**")
        kind = st.radio("", LAW_KINDS, label_visibility="collapsed")
        st.markdown("---")

    # ── Header ──
    render_header()

    # ── Load laws ──
    laws = load_laws(kind)
    if not laws:
        st.warning(f"لا توجد بيانات في القاعدة لـ {kind}")
        return

    # ── Search / Jump ──
    with st.sidebar:
        st.markdown("**🔍 بحث سريع**")
        search = st.text_input("اسم القانون أو رقمه", key="search_input", label_visibility="collapsed",
                                placeholder="ابحث...")
        if search:
            results = [
                (i, l) for i, l in enumerate(laws)
                if search in l["Leg_Name"] or search in (l["Leg_Number"] or "")
            ]
            if results:
                labels = [f"{l['Leg_Number']} — {l['Leg_Name'][:30]}" for _,l in results]
                chosen = st.selectbox("النتائج", range(len(labels)), format_func=lambda i: labels[i])
                if st.button("🔎 اذهب", use_container_width=True):
                    st.session_state.current_idx = results[chosen][0]
                    st.session_state.pop("action", None)
                    st.rerun()
            else:
                st.info("لا نتائج")

    # ── Navigation ──
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0
    idx = min(st.session_state.current_idx, len(laws) - 1)

    show_law(idx, laws, kind)

    # ── Nav Buttons ──
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if idx > 0:
            if st.button("◄ السابق", use_container_width=True):
                st.session_state.current_idx -= 1
                st.session_state.pop("action", None)
                st.rerun()
    with col2:
        st.markdown(
            f'<div style="text-align:center;color:var(--gold);font-size:0.85rem;padding-top:0.5rem;">'
            f'{idx + 1} / {len(laws)}</div>',
            unsafe_allow_html=True
        )
    with col3:
        if idx < len(laws) - 1:
            if st.button("التالي ►", type="primary", use_container_width=True):
                st.session_state.current_idx += 1
                st.session_state.pop("action", None)
                st.rerun()

if __name__ == "__main__":
    main()
