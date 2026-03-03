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
    "تعديل مادة":   "badge-edit",
    "إضافة مادة":   "badge-add",
    "إلغاء مادة":   "badge-del",
    "استعادة مادة": "badge-add",
}

LAW_KINDS = ["قانون ج1", "قانون ج2", "قانون ج3"]

KIND_TO_TABLE = {
    "قانون ج1": {"modified": "laws_p1_modified"},
    "قانون ج2": {"modified": "laws_p2_modified"},
    "قانون ج3": {"modified": "laws_p3_modified"},
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
        --navy:         #0a1628;
        --navy-mid:     #0f2044;
        --navy-card:    #132252;
        --navy-light:   #1a2f6a;
        --gold:         #c9a84c;
        --gold-light:   #e8c96a;
        --gold-dim:     #7a6030;
        --cream:        #f0e8d4;
        --cream-dim:    #b0a080;
        --border:       rgba(201,168,76,0.25);
        --border-hover: rgba(201,168,76,0.55);
        --glass:        rgba(255,255,255,0.04);
        --glass-hover:  rgba(255,255,255,0.08);
        --shadow:       0 8px 32px rgba(0,0,0,0.4);
        --radius:       14px;
        --radius-sm:    8px;
    }

    * { font-family: 'Tajawal', sans-serif !important; direction: rtl; text-align: right; box-sizing: border-box; }

    .stApp {
        background: var(--navy);
        background-image:
            radial-gradient(ellipse at 20% 10%, rgba(201,168,76,0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 90%, rgba(21,45,110,0.8) 0%, transparent 50%);
    }
    .block-container { max-width: 1100px !important; padding: 1.5rem 2.5rem !important; }

    /* ── HEADER ── */
    .app-header {
        text-align: center; padding: 2rem 0 1.5rem;
        margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); position: relative;
    }
    .app-header::after {
        content: ''; position: absolute;
        bottom: -1px; left: 50%; transform: translateX(-50%);
        width: 120px; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }
    .app-header h1 {
        font-family: 'Amiri', serif !important; color: var(--gold) !important;
        font-size: 2.4rem !important; margin: 0 0 0.3rem !important;
        text-shadow: 0 0 40px rgba(201,168,76,0.3); letter-spacing: 1px;
    }
    .header-sub { color: var(--cream-dim); font-size: 0.9rem; margin: 0; }

    /* ── LAW CARD ── */
    .law-header-card {
        background: linear-gradient(135deg, var(--navy-card) 0%, var(--navy-light) 100%);
        border: 1px solid var(--border-hover); border-radius: var(--radius);
        padding: 1.5rem 2rem; margin-bottom: 1.5rem;
        box-shadow: var(--shadow), inset 0 1px 0 rgba(201,168,76,0.15);
        position: relative; overflow: hidden;
    }
    .law-header-card::before {
        content: '⚖'; position: absolute;
        left: 1.5rem; top: 50%; transform: translateY(-50%);
        font-size: 3rem; opacity: 0.05;
    }
    .law-title {
        font-family: 'Amiri', serif !important; color: var(--gold-light) !important;
        font-size: 1.6rem !important; margin: 0 0 0.7rem !important; line-height: 1.5;
    }
    .law-meta { display: flex; gap: 1.5rem; flex-wrap: wrap; }
    .meta-chip {
        background: rgba(201,168,76,0.1); border: 1px solid rgba(201,168,76,0.2);
        border-radius: 20px; padding: 3px 14px; font-size: 0.82rem; color: var(--cream-dim);
    }
    .meta-chip b { color: var(--gold); }

    /* ── ARTICLE CARD ── */
    .article-card {
        background: var(--glass); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 1.4rem 1.8rem; margin-bottom: 1rem; transition: all 0.2s ease;
    }
    .article-card.selected {
        background: rgba(201,168,76,0.07); border-color: var(--gold);
        box-shadow: 0 0 0 1px rgba(201,168,76,0.3), var(--shadow);
    }
    .article-card.deleted {
        background: rgba(224,85,85,0.04); border-color: rgba(224,85,85,0.25);
        border-right: 3px solid rgba(224,85,85,0.5); opacity: 0.7;
    }
    .deleted-stamp {
        display: inline-flex; align-items: center; gap: 0.3rem;
        background: rgba(224,85,85,0.15); border: 1px solid rgba(224,85,85,0.3);
        border-radius: 20px; padding: 2px 10px; font-size: 0.72rem; color: #fca5a5; font-weight: 700; margin-right: 0.5rem;
    }
    .article-num {
        display: inline-block; background: linear-gradient(135deg, var(--gold-dim), var(--gold));
        color: var(--navy) !important; font-weight: 900; font-size: 0.75rem;
        padding: 2px 10px; border-radius: 12px; margin-left: 0.6rem; letter-spacing: 0.5px;
    }
    .article-num.deleted-num { background: linear-gradient(135deg, #7a3030, #e05555); }
    .article-title-text { color: var(--cream); font-size: 1rem; font-weight: 600; }
    .article-date { color: var(--cream-dim); font-size: 0.78rem; margin-top: 0.3rem; }
    .article-body {
        color: var(--cream); line-height: 2; white-space: pre-wrap;
        font-size: 0.96rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);
    }

    /* ── BADGES ── */
    .badge-wrap { display: inline-flex; align-items: center; gap: 0.4rem; }
    .amend-badge { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: 0.73rem; font-weight: 700; letter-spacing: 0.3px; }
    .badge-edit { background: rgba(85,136,224,.18); color: #93c5fd; border: 1px solid rgba(85,136,224,.3); }
    .badge-add  { background: rgba(76,175,130,.18); color: #86efac; border: 1px solid rgba(76,175,130,.3); }
    .badge-del  { background: rgba(224,85,85,.18);  color: #fca5a5; border: 1px solid rgba(224,85,85,.3); }

    /* ── AMENDMENT CARD ── */
    .amend-card {
        background: rgba(201,168,76,0.05); border: 1px solid rgba(201,168,76,0.2);
        border-right: 3px solid var(--gold); border-radius: var(--radius-sm);
        padding: 0.9rem 1.2rem; margin-bottom: 0.7rem;
    }
    .amend-article-ref { color: var(--gold); font-weight: 700; font-size: 0.85rem; margin: 0.3rem 0; }
    .amend-text { color: var(--cream-dim); font-size: 0.9rem; line-height: 1.7; }

    /* ── SECTION HEADER ── */
    .section-header {
        display: flex; align-items: center; gap: 0.8rem;
        margin: 1.8rem 0 1rem; color: var(--gold); font-weight: 700; font-size: 1rem;
    }
    .section-header::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--gold-dim), transparent); }

    /* ── MISC ── */
    .law-counter {
        background: rgba(201,168,76,0.1); border: 1px solid var(--border);
        border-radius: 20px; padding: 4px 18px; color: var(--gold); font-size: 0.85rem;
    }
    [data-testid="stSidebar"] { background: var(--navy-mid) !important; border-left: 1px solid var(--border) !important; }
    [data-testid="stSidebar"] * { color: var(--cream) !important; }
    .sidebar-logo { text-align: center; padding: 1rem; border-bottom: 1px solid var(--border); margin-bottom: 1rem; }
    .sidebar-logo span { font-size: 2rem; }
    .user-chip {
        background: rgba(201,168,76,0.1); border: 1px solid var(--border);
        border-radius: 10px; padding: 0.6rem 1rem; margin-bottom: 1rem; font-size: 0.85rem; color: var(--cream-dim) !important;
    }
    .user-chip b { color: var(--gold) !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: var(--navy-card) !important; border: 1px solid var(--border) !important;
        color: var(--cream) !important; border-radius: var(--radius-sm) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--gold) !important; box-shadow: 0 0 0 2px rgba(201,168,76,0.15) !important;
    }
    .stButton > button { border-radius: var(--radius-sm) !important; font-weight: 600 !important; transition: all 0.15s !important; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--gold-dim), var(--gold)) !important;
        color: var(--navy) !important; border: none !important;
    }
    .stButton > button[kind="primary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(201,168,76,0.35) !important; }
    .stButton > button[kind="secondary"] { background: var(--glass) !important; border: 1px solid var(--border) !important; color: var(--cream) !important; }
    .empty-state { text-align: center; padding: 3rem; color: var(--cream-dim); }
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
name     = st.session_state.get("name")
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
# DATA HELPERS
# =====================================================
JSON_FILES = {
    "قانون ج1": "app/V02_Laws_P1.json",
    "قانون ج2": "app/V02_Laws_P2.json",
}

@st.cache_data(show_spinner=False)
def load_json(kind):
    """قراءة ملف JSON مرة واحدة وتخزينه في cache."""
    path = JSON_FILES[kind]
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    laws = []
    for i, law in enumerate(data):
        laws.append({
            "db_id":           None,
            "Leg_Name":        law.get("Leg_Name", ""),
            "Leg_Number":      law.get("Leg_Number", ""),
            "Year":            law.get("Year", ""),
            "Magazine_Number": law.get("Magazine_Number", ""),
            "Magazine_Page":   law.get("Magazine_Page", ""),
            "Magazine_Date":   law.get("Magazine_Date", ""),
            "is_amendment":    law.get("is_amendment", False),
            "Articles":        law.get("Articles", []),
            "amended_articles":law.get("amended_articles", []),
            "_json_idx":       i,
        })
    return laws

def load_laws(kind):
    """
    JSON كـ source of truth.
    القوانين المعدَّلة في DB تُستبدَل بها.
    المفتاح: (Leg_Number, Year) معاً.
    """
    table_modified = KIND_TO_TABLE[kind]["modified"]
    laws = [dict(l) for l in load_json(kind)]
    if not laws:
        st.error(f"الملف غير موجود أو فارغ: {JSON_FILES[kind]}")
        return []
    try:
        with get_cursor() as cur:
            cur.execute(f"SELECT * FROM {table_modified} ORDER BY id")
            modified_rows = cur.fetchall()
        mod_dict = {}
        for row in modified_rows:
            key = (row["leg_number"], row["year"])
            mod_dict[key] = row_to_law(row)
        for i, law in enumerate(laws):
            key = (law["Leg_Number"], law["Year"])
            if key in mod_dict:
                laws[i] = mod_dict[key]
        return laws
    except Exception as e:
        st.error(f"خطأ في تحميل التعديلات من DB: {str(e)}")
        return laws

def row_to_law(row):
    return {
        "db_id":           row["id"],
        "Leg_Name":        row["leg_name"],
        "Leg_Number":      row["leg_number"],
        "Year":            row["year"],
        "Magazine_Number": row["magazine_number"],
        "Magazine_Page":   row["magazine_page"],
        "Magazine_Date":   row["magazine_date"],
        "is_amendment":    row["is_amendment"],
        "Articles":        row["articles"] or [],
        "amended_articles":row["amended_articles"] or [],
    }

def save_law(law, kind):
    """upsert في جدول modified بمفتاح (leg_number, year)."""
    table_modified = KIND_TO_TABLE[kind]["modified"]
    leg_number = law["Leg_Number"]
    year       = law["Year"]
    try:
        with get_cursor() as cur:
            cur.execute(
                f"SELECT id FROM {table_modified} WHERE leg_number=%s AND year=%s",
                (leg_number, year)
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(f"""
                UPDATE {table_modified} SET
                    leg_name=%s, magazine_number=%s, magazine_page=%s,
                    magazine_date=%s, is_amendment=%s,
                    articles=%s::jsonb, amended_articles=%s::jsonb
                WHERE leg_number=%s AND year=%s
                """, (
                    law["Leg_Name"], law["Magazine_Number"], law["Magazine_Page"],
                    law["Magazine_Date"], law["is_amendment"],
                    json.dumps(law["Articles"], ensure_ascii=False),
                    json.dumps(law["amended_articles"], ensure_ascii=False),
                    leg_number, year
                ))
            else:
                cur.execute(f"""
                INSERT INTO {table_modified}
                    (leg_name, leg_number, year, magazine_number, magazine_page,
                     magazine_date, is_amendment, articles, amended_articles)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)
                """, (
                    law["Leg_Name"], leg_number, year,
                    law["Magazine_Number"], law["Magazine_Page"],
                    law["Magazine_Date"], law["is_amendment"],
                    json.dumps(law["Articles"], ensure_ascii=False),
                    json.dumps(law["amended_articles"], ensure_ascii=False),
                ))
        load_json.clear()
    except Exception as e:
        st.error(f"خطأ في حفظ القانون: {str(e)}")
        raise

def toast(msg=None):
    msgs = ["✅ تم الحفظ بنجاح", "💾 محفوظ", "✅ تمّ"]
    st.toast(msg or random.choice(msgs), icon="✅")

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
        def art_label(a):
            deleted_mark = " 🚫" if a.get("deleted") else ""
            return f"المادة {a['article_number']}{deleted_mark} — {a.get('title','')[:35]}"

        art_idx = st.selectbox(
            "اختر مادة",
            range(len(articles)),
            format_func=lambda i: art_label(articles[i]),
            key=f"art_select_{idx}"
        )
        art        = articles[art_idx]
        is_deleted = art.get("deleted", False)

        # ── Render article card ──
        art_num   = html_lib.escape(str(art.get("article_number", "")))
        art_title = html_lib.escape(str(art.get("title", "")))
        art_date  = html_lib.escape(str(art.get("enforcement_date", "—")))
        art_text  = html_lib.escape(str(art.get("text", "")))

        if is_deleted:
            by = html_lib.escape(art.get("deleted_by", ""))
            at = html_lib.escape(art.get("deleted_at", ""))
            del_meta = ('🗑️ ' + ('بواسطة ' + by if by else '') + ' ' + ('في ' + at if at else '')).strip()
            st.markdown(
                '<div style="background:rgba(224,85,85,0.04);border:1px solid rgba(224,85,85,0.25);'
                'border-right:3px solid rgba(224,85,85,0.5);border-radius:14px;padding:1.4rem 1.8rem;margin-bottom:1rem;">'
                '<div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">'
                '<span style="background:linear-gradient(135deg,#7a3030,#e05555);color:#0a1628;font-weight:900;'
                'font-size:0.75rem;padding:2px 10px;border-radius:12px;">مادة ' + art_num + '</span>'
                '<span style="color:#b0a080;font-size:1rem;font-weight:600;text-decoration:line-through;'
                'text-decoration-color:rgba(224,85,85,0.6);">' + art_title + '</span>'
                '<span style="background:rgba(224,85,85,0.15);border:1px solid rgba(224,85,85,0.3);'
                'border-radius:20px;padding:2px 10px;font-size:0.72rem;color:#fca5a5;font-weight:700;">🚫 ملغاة</span>'
                '</div>'
                '<div style="color:#b0a080;font-size:0.78rem;margin-top:0.4rem;">📅 تاريخ النفاذ: ' + art_date + '</div>'
                '<div style="color:#fca5a5;font-size:0.78rem;margin-top:0.2rem;">' + del_meta + '</div>'
                '<hr style="border-color:rgba(224,85,85,0.15);margin:0.8rem 0;">'
                '<div style="color:#b0a080;line-height:2;white-space:pre-wrap;font-size:0.96rem;'
                'text-decoration:line-through;text-decoration-color:rgba(224,85,85,0.4);">' + art_text + '</div>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="background:rgba(201,168,76,0.07);border:1px solid #c9a84c;border-radius:14px;'
                'padding:1.4rem 1.8rem;margin-bottom:1rem;box-shadow:0 0 0 1px rgba(201,168,76,0.3),0 8px 32px rgba(0,0,0,0.4);">'
                '<div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">'
                '<span style="background:linear-gradient(135deg,#7a6030,#c9a84c);color:#0a1628;font-weight:900;'
                'font-size:0.75rem;padding:2px 10px;border-radius:12px;letter-spacing:0.5px;">مادة ' + art_num + '</span>'
                '<span style="color:#f0e8d4;font-size:1rem;font-weight:600;">' + art_title + '</span>'
                '</div>'
                '<div style="color:#b0a080;font-size:0.78rem;margin-top:0.4rem;">📅 تاريخ النفاذ: ' + art_date + '</div>'
                '<hr style="border-color:rgba(201,168,76,0.2);margin:0.8rem 0;">'
                '<div style="color:#f0e8d4;line-height:2;white-space:pre-wrap;font-size:0.96rem;">' + art_text + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

        # ── Action buttons ──
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
                        "text": art.get("text", ""),
                        "restored_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "restored_by": st.session_state.get("user_name", "")
                    })
                    save_law(law, kind)
                    toast("↩️ تمت الاستعادة")
                    st.rerun()
        else:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
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

        # ── Confirm Delete ──
        action = st.session_state.get("action")
        if action and action[0] == "confirm_delete" and action[1] == idx and action[2] == art_idx:
            st.warning(f"⚠️ هل أنت متأكد من إلغاء **المادة {art['article_number']}**؟ ستبقى ظاهرة كمحذوفة.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ نعم، ألغِ المادة", type="primary", key="confirm_del_yes"):
                    law["Articles"][art_idx]["deleted"]    = True
                    law["Articles"][art_idx]["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    law["Articles"][art_idx]["deleted_by"] = st.session_state.get("user_name", "")
                    law["amended_articles"].append({
                        "type": "إلغاء مادة",
                        "article_number": art["article_number"],
                        "text": art.get("text", ""),
                        "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "deleted_by": st.session_state.get("user_name", "")
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
                num   = st.text_input("رقم المادة", value=suggested)
                title = st.text_input("عنوان المادة", value=f"المادة {suggested}")
            with col_b:
                date  = st.text_input("تاريخ النفاذ", value=datetime.now().strftime("%d-%m-%Y"))
            text = st.text_area("نص المادة", height=200)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 حفظ", type="primary"):
                new_art = {"article_number": num, "title": title, "enforcement_date": date, "text": text}
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
        art_edit     = law["Articles"][art_idx_edit]
        st.markdown('<div class="section-header">✏️ تعديل المادة</div>', unsafe_allow_html=True)
        with st.form(f"form_edit_art_{idx}_{art_idx_edit}"):
            col_a, col_b = st.columns(2)
            with col_a:
                num   = st.text_input("رقم المادة", value=art_edit["article_number"])
                title = st.text_input("عنوان المادة", value=art_edit.get("title", ""))
            with col_b:
                date  = st.text_input("تاريخ النفاذ", value=art_edit.get("enforcement_date", ""))
            old_text = art_edit.get("text", "")
            text = st.text_area("نص المادة", value=old_text, height=250)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 حفظ التعديل", type="primary"):
                law["Articles"][art_idx_edit] = {
                    "article_number": num, "title": title,
                    "enforcement_date": date, "text": text
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

    # =====================================================
    # SECTION 1: المواد التي يعدّلها هذا القانون
    # يظهر فقط إذا is_amendment == True
    # يعرض العناصر المُضافة يدوياً (ليس لها edited_at/deleted_at/restored_at)
    # =====================================================
    if law.get("is_amendment"):
        st.markdown('<div class="section-header">📝 المواد التي يعدّلها هذا القانون</div>', unsafe_allow_html=True)

        declared = [
            a for a in law.get("amended_articles", [])
            if a.get("type") in AMEND_TYPES
            and not (a.get("edited_at") or a.get("deleted_at") or a.get("restored_at"))
        ]

        if declared:
            for amend in declared:
                bc  = AMEND_BADGE_CSS.get(amend.get("type", ""), "badge-edit")
                ar  = html_lib.escape(str(amend.get("article_number", "")))
                ab  = html_lib.escape(str(amend.get("added_by", "")))
                at  = html_lib.escape(str(amend.get("added_at", "")))
                bys = ('<span style="color:var(--cream-dim);font-size:0.78rem;">👤 ' + ab + '</span>') if ab else ""
                ats = ('<span style="color:var(--cream-dim);font-size:0.78rem;">🕐 ' + at + '</span>') if at else ""
                st.markdown(
                    '<div style="background:rgba(201,168,76,0.05);border:1px solid rgba(201,168,76,0.2);'
                    'border-right:3px solid var(--gold);border-radius:8px;padding:0.7rem 1.1rem;'
                    'margin-bottom:0.5rem;display:flex;align-items:center;gap:0.7rem;flex-wrap:wrap;">'
                    + '<span class="amend-badge ' + bc + '">' + amend.get("type", "") + '</span>'
                    + '<span style="color:var(--gold);font-weight:700;">المادة ' + ar + '</span>'
                    + bys + ats + '</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div style="color:var(--cream-dim);font-size:0.9rem;padding:0.3rem 0 0.8rem;">'
                'لم تُسجَّل مواد معدَّلة بعد.</div>',
                unsafe_allow_html=True
            )

        if st.button("➕ إضافة مادة معدَّلة", key=f"btn_amend_{idx}"):
            st.session_state["action"] = ("add_amendment", idx)
            st.rerun()

        if action and action[0] == "add_amendment" and action[1] == idx:
            with st.form(f"form_add_amend_{idx}"):
                col_x, col_y = st.columns(2)
                with col_x:
                    amend_type  = st.selectbox("نوع التعديل", AMEND_TYPES)
                with col_y:
                    article_num = st.text_input("رقم المادة المعدَّلة")
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 حفظ", type="primary"):
                    law["amended_articles"].append({
                        "type": amend_type,
                        "article_number": article_num,
                        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "added_by": st.session_state.get("user_name", "")
                    })
                    save_law(law, kind)
                    st.session_state.pop("action", None)
                    toast()
                    st.rerun()
                if c2.form_submit_button("❌ إلغاء"):
                    st.session_state.pop("action", None)
                    st.rerun()

    # =====================================================
    # SECTION 2: سجل عمليات النظام
    # يظهر دائماً إذا في عمليات (تعديل/حذف/استعادة)
    # يعرض فقط العناصر التي لها edited_at أو deleted_at أو restored_at
    # =====================================================
    syslog = [
        a for a in law.get("amended_articles", [])
        if a.get("edited_at") or a.get("deleted_at") or a.get("restored_at")
    ]
    if syslog:
        st.markdown('<div class="section-header">🔄 سجل عمليات التعديل</div>', unsafe_allow_html=True)
        for amend in reversed(syslog):
            bc   = AMEND_BADGE_CSS.get(amend.get("type", ""), "badge-edit")
            ar   = amend.get("article_number", "")
            ts   = amend.get("edited_at") or amend.get("deleted_at") or amend.get("restored_at") or ""
            us   = amend.get("edited_by") or amend.get("deleted_by") or amend.get("restored_by") or ""
            prev = (amend.get("text", "") or "")[:120]
            dots = "..." if len(amend.get("text", "")) > 120 else ""
            ar_h = ('<span class="amend-article-ref">المادة ' + ar + '</span>') if ar else ""
            ts_h = ('<span style="color:var(--cream-dim);font-size:0.78rem;">🕐 ' + ts + '</span>') if ts else ""
            us_h = ('<span style="color:var(--cream-dim);font-size:0.78rem;">👤 ' + us + '</span>') if us else ""
            st.markdown(
                '<div class="amend-card"><div class="badge-wrap">'
                + '<span class="amend-badge ' + bc + '">' + amend.get("type", "") + '</span>'
                + ar_h + ts_h + us_h + '</div>'
                + '<div class="amend-text">' + html_lib.escape(prev) + dots + '</div></div>',
                unsafe_allow_html=True
            )

# =====================================================
# MAIN
# =====================================================
def main():
    try:
        init_db()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo"><span>⚖️</span><br>
        <b style="color:var(--gold);font-size:1rem;">التشريعات</b></div>
        """, unsafe_allow_html=True)
        st.markdown(
            f'<div class="user-chip">👤 <b>{st.session_state.user_name}</b></div>',
            unsafe_allow_html=True
        )
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
        st.warning(f"لا توجد بيانات لـ {kind}")
        return

    # ── Search ──
    with st.sidebar:
        st.markdown("**🔍 بحث سريع**")
        search = st.text_input(
            "بحث", key="search_input",
            label_visibility="collapsed", placeholder="ابحث باسم القانون أو رقمه..."
        )
        if search:
            results = [
                (i, l) for i, l in enumerate(laws)
                if search in l["Leg_Name"] or search in (l["Leg_Number"] or "")
            ]
            if results:
                labels = [f"{l['Leg_Number']} — {l['Leg_Name'][:30]}" for _, l in results]
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
