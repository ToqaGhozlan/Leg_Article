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
    preauthorized = config.get('preauthorized'),
)

authenticator.login(
    location = 'main',
    key = 'login_form',
    fields = {'Form name': 'تسجيل الدخول'},
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

# =====================================================
# STYLES
# =====================================================
def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@300;400;600;700;900&display=swap');
    :root {
        --navy: #0f1e3d;
        --navy-mid: #1a2f5a;
        --gold: #c9a84c;
        --gold-light: #e5c97a;
        --cream: #f8f4ed;
    }
    * { font-family:'Tajawal',sans-serif!important; direction:rtl; text-align:right; }
    .stApp {
        background: var(--navy);
        background-image:
            radial-gradient(ellipse at 80% 10%, rgba(201,168,76,0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 10% 90%, rgba(36,59,110,0.6) 0%, transparent 50%);
        min-height: 100vh;
    }
    .block-container { max-width:980px!important; padding:2rem 3rem!important; }
    [data-testid="stSidebar"] {
        background: var(--navy-mid)!important;
        border-left: 2px solid rgba(201,168,76,0.3)!important;
        border-right: none!important;
    }
    [data-testid="stSidebar"] * { color:var(--cream)!important; text-align:right!important; }
    [data-testid="stSidebarCollapsedControl"] { right:0!important; left:auto!important; }
    .law-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(201,168,76,0.25);
        border-radius: 14px;
        padding: 1.8rem;
        margin: 1.2rem 0;
        direction: rtl;
    }
    .article-text {
        color: var(--cream);
        line-height: 1.9;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 1.05rem;
        text-align: right;
    }
    .record-counter {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: rgba(201,168,76,0.15);
        border: 1px solid rgba(201,168,76,0.4);
        border-radius: 30px;
        padding: 8px 20px;
        color: var(--gold);
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .gold-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
        margin: 1.5rem 0;
        opacity: 0.4;
    }
    /* amend section */
    .amend-section {
        background: rgba(201,168,76,0.07);
        border: 1px solid rgba(201,168,76,0.3);
        border-right: 4px solid var(--gold);
        border-radius: 10px;
        padding: 1.1rem 1.3rem 0.8rem;
        margin: 1rem 0 1.4rem;
    }
    /* badge colours */
    .badge-edit { background:rgba(59,130,246,0.2); border:1px solid rgba(59,130,246,0.5); color:#93c5fd; }
    .badge-add { background:rgba(34,197,94,0.15); border:1px solid rgba(34,197,94,0.45); color:#86efac; }
    .badge-del { background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.45); color:#fca5a5; }
    .amend-badge {
        display: inline-block;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# sidebar header
st.sidebar.markdown(
    f'<div style="color:var(--gold);font-weight:700;font-size:1.1rem;text-align:center;">'
    f'👤 {html_lib.escape(st.session_state.user_name)}</div>',
    unsafe_allow_html=True,
)
authenticator.logout("تسجيل الخروج", location="sidebar", key="logout_widget")

# =====================================================
# DATABASE HELPERS
# =====================================================
def load_laws(kind: str) -> list:
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT * FROM laws WHERE kind = %s ORDER BY id",
                (kind,),
            )
            rows = cur.fetchall()
        return [
            {
                "db_id": row["id"],
                "Leg_Name": row["leg_name"],
                "Leg_Number": row["leg_number"] or "—",
                "Year": row["year"] or "—",
                "Magazine_Number": row["magazine_number"] or "—",
                "Magazine_Page": row["magazine_page"] or "—",
                "Magazine_Date": row["magazine_date"] or "—",
                "is_amendment": bool(row["is_amendment"]),
                "Articles": row["articles"] or [],
                "amended_articles": row["amended_articles"] or [],
            }
            for row in rows
        ]
    except Exception as e:
        st.error(f"خطأ في تحميل القوانين: {e}")
        return []

def save_law(law: dict, kind: str) -> bool:
    try:
        with get_cursor() as cur:
            cur.execute(
                """
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
                """,
                (
                    law["Leg_Name"],
                    law["Leg_Number"],
                    law["Year"],
                    law["Magazine_Number"],
                    law["Magazine_Page"],
                    law["Magazine_Date"],
                    law["is_amendment"],
                    json.dumps(law["Articles"], ensure_ascii=False),
                    json.dumps(law["amended_articles"], ensure_ascii=False),
                    law["db_id"],
                ),
            )
        return True
    except Exception as e:
        st.error(f"خطأ في حفظ القانون: {e}")
        return False

def toast():
    st.toast(random.choice(["✅ محفوظ", "كفو ✅", "تم الحفظ ✅"]), icon="✅")

# =====================================================
# MIGRATION HELPERS
# =====================================================
def has_migration_run(name: str) -> bool:
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM migration_status WHERE migration_name = %s", (name,)
            )
            return cur.fetchone() is not None
    except Exception:
        return False

def mark_migration_done(name: str):
    try:
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO migration_status (migration_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (name,),
            )
    except Exception as e:
        st.error(f"خطأ في تسجيل migration: {e}")

def migrate_law_kind(kind: str, json_filename: str) -> int:
    json_path = f"app/{json_filename}"
    if not os.path.exists(json_path):
        st.error(f"الملف غير موجود: {json_path}")
        return 0
    try:
        with open(json_path, encoding="utf-8-sig") as f:
            data = json.load(f)
        inserted = 0
        with get_cursor() as cur:
            for law in data:
                cur.execute(
                    """
                    INSERT INTO laws (
                        kind, leg_name, leg_number, year,
                        magazine_number, magazine_page, magazine_date,
                        is_amendment, articles, amended_articles
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    (
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
                    ),
                )
                if cur.fetchone():
                    inserted += 1
        st.success(f"{kind}: أُضيف {inserted} سجل (من أصل {len(data)})")
        return inserted
    except Exception as e:
        st.error(f"خطأ أثناء معالجة {kind}: {e}")
        return 0

# =====================================================
# AMENDED ARTICLES HELPERS
# =====================================================
def _normalize_amended(raw: list) -> list:
    out = []
    mapping = {"تعديل": "تعديل مادة", "إضافة": "إضافة مادة", "إلغاء": "إلغاء مادة"}
    for a in raw:
        if isinstance(a, dict):
            t = a.get("type", AMEND_TYPES[0])
            if t not in AMEND_TYPES:
                t = mapping.get(t, AMEND_TYPES[0])
            out.append({"number": str(a.get("number", "")).strip(), "type": t})
        else:
            out.append({"number": str(a).strip(), "type": AMEND_TYPES[0]})
    return out

def render_amended_section(law: dict, kind: str):
    db_id = law["db_id"]
    buf_key = f"amended_buf_{kind}_{db_id}"
    if buf_key not in st.session_state:
        st.session_state[buf_key] = _normalize_amended(law.get("amended_articles", []))

    amended = st.session_state[buf_key]
    to_delete = None

    st.markdown('<div class="amend-section">', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:var(--gold);font-weight:700;font-size:0.92rem;margin-bottom:0.8rem;">'
        '📝 المواد المعدَّلة في هذا القانون</p>',
        unsafe_allow_html=True,
    )

    if amended:
        col_h1, col_h2, _ = st.columns([2, 3, 1])
        col_h1.markdown(
            '<small style="color:rgba(201,168,76,0.7);font-weight:600;">رقم المادة</small>',
            unsafe_allow_html=True,
        )
        col_h2.markdown(
            '<small style="color:rgba(201,168,76,0.7);font-weight:600;">نوع التعديل</small>',
            unsafe_allow_html=True,
        )

        for row_i, row in enumerate(amended):
            c_num, c_type, c_del = st.columns([2, 3, 1])
            with c_num:
                amended[row_i]["number"] = st.text_input(
                    "رقم",
                    value=row["number"],
                    key=f"anum_{kind}_{db_id}_{row_i}",
                    label_visibility="collapsed",
                    placeholder="رقم المادة",
                ).strip()

            with c_type:
                cur_i = AMEND_TYPES.index(row["type"]) if row["type"] in AMEND_TYPES else 0
                amended[row_i]["type"] = st.selectbox(
                    "نوع",
                    AMEND_TYPES,
                    index=cur_i,
                    key=f"atype_{kind}_{db_id}_{row_i}",
                    label_visibility="collapsed",
                )

            with c_del:
                st.markdown('<div style="margin-top:0.4rem;"></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"adel_{kind}_{db_id}_{row_i}",
                             help="حذف", use_container_width=True):
                    to_delete = row_i

    else:
        st.markdown(
            '<p style="color:rgba(248,244,237,0.35);font-size:0.88rem;font-style:italic;">'
            'لا توجد مواد معدَّلة — اضغط ➕ لإضافة</p>',
            unsafe_allow_html=True,
        )

    col_add, col_save = st.columns([3, 2])
    with col_add:
        if st.button("➕ إضافة مادة", key=f"aadd_{kind}_{db_id}"):
            st.session_state[buf_key].append({"number": "", "type": AMEND_TYPES[0]})
            st.rerun()

    with col_save:
        if st.button("💾 حفظ التغييرات", key=f"asave_{kind}_{db_id}", type="primary"):
            if to_delete is not None:
                st.session_state[buf_key].pop(to_delete)
            law["amended_articles"] = [dict(a) for a in st.session_state[buf_key]]
            if save_law(law, kind):
                toast()
            st.rerun()

    if to_delete is not None:
        st.session_state[buf_key].pop(to_delete)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ملخص البادجات
    saved = _normalize_amended(law.get("amended_articles", []))
    if saved:
        badges = "".join(
            f'<span class="amend-badge {AMEND_BADGE_CSS.get(a["type"],"badge-edit")}">'
            f'م {html_lib.escape(a["number"])} · {html_lib.escape(a["type"])}</span> '
            for a in saved
            if a.get("number")
        )
        if badges:
            st.markdown(
                f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:0.5rem 0 1rem;direction:rtl;">'
                f'{badges}</div>',
                unsafe_allow_html=True,
            )

# =====================================================
# EDIT ARTICLE (شاشة منفصلة)
# =====================================================
def edit_article_screen(law: dict, art_idx: int, kind: str):
    articles = law.get("Articles", [])
    if not articles:
        st.warning("لا توجد مواد.")
        st.session_state.editing = False
        st.rerun()
        return

    art_idx = min(art_idx, len(articles) - 1)
    art = articles[art_idx]

    st.markdown(
        f'<p style="color:var(--gold);font-weight:700;font-size:1rem;margin-bottom:0.5rem;">'
        f'✏️ تعديل — {html_lib.escape(law["Leg_Name"])}</p>',
        unsafe_allow_html=True,
    )

    with st.form("edit_article_form"):
        st.subheader(f"المادة {art.get('article_number','?')}")
        num = st.text_input("رقم المادة", value=art.get("article_number", ""))
        title = st.text_input("العنوان", value=art.get("title", ""))
        enf_date = st.text_input("تاريخ النفاذ", value=art.get("enforcement_date", ""))
        text = st.text_area("نص المادة", value=art.get("text", ""), height=340)

        col1, col2 = st.columns(2)
        if col1.form_submit_button("💾 حفظ التعديل", type="primary"):
            law["Articles"][art_idx] = {
                "article_number": num.strip(),
                "title": title.strip(),
                "enforcement_date": enf_date.strip(),
                "text": text.strip(),
            }
            if save_law(law, kind):
                toast()
            st.session_state.editing = False
            st.rerun()

        if col2.form_submit_button("إلغاء"):
            st.session_state.editing = False
            st.rerun()

# =====================================================
# SHOW LAW (الشاشة الرئيسية)
# =====================================================
def show_law(idx: int, laws: list, kind: str):
    law = laws[idx]
    total = len(laws)
    articles = law.get("Articles", [])
    art_count = len(articles)
    is_amendment = law.get("is_amendment", False)

    # counter + progress
    progress = (idx + 1) / total * 100
    st.markdown(
        f'<div class="record-counter">⚖️ القانون {idx+1} من {total}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="margin:0.8rem 0 1.2rem;">'
        f' <div style="display:flex;justify-content:space-between;'
        f' color:rgba(248,244,237,0.6);font-size:0.82rem;margin-bottom:4px;">'
        f' <span>التقدم</span><span>{progress:.0f}%</span></div>'
        f' <div style="background:rgba(255,255,255,0.08);height:6px;border-radius:3px;overflow:hidden;">'
        f' <div style="height:100%;width:{progress:.1f}%;'
        f' background:linear-gradient(90deg,var(--gold),var(--gold-light));"></div>'
        f' </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # law card
    e = html_lib.escape
    amendment_badge = (
        '<span style="background:rgba(201,168,76,0.25);color:var(--gold);font-size:0.75rem;'
        'font-weight:700;padding:3px 12px;border-radius:20px;'
        'border:1px solid rgba(201,168,76,0.5);margin-right:10px;">⚠️ تعديل</span>'
        if is_amendment else ""
    )

    st.markdown(
        '<div class="law-card">'
        ' <div style="display:flex;align-items:center;margin-bottom:0.8rem;">'
        ' <div style="background:var(--gold);color:#0f1e3d;font-size:0.8rem;font-weight:800;'
        ' padding:4px 14px;border-radius:20px;display:inline-block;">نص القانون</div>'
        f' {amendment_badge}'
        ' </div>'
        f' <h3 style="margin:0 0 1rem;color:var(--cream);font-family:\'Amiri\',serif;'
        f' font-size:1.35rem;line-height:1.5;">{e(law["Leg_Name"])}</h3>'
        ' <div style="display:flex;gap:1.4rem;flex-wrap:wrap;color:var(--gold-light);">'
        f' <div><small style="color:rgba(248,244,237,0.5);">رقم القانون</small><br>{e(law["Leg_Number"])}</div>'
        f' <div><small style="color:rgba(248,244,237,0.5);">السنة</small><br>{e(law["Year"])}</div>'
        f' <div><small style="color:rgba(248,244,237,0.5);">رقم الجريدة</small><br>{e(law["Magazine_Number"])}</div>'
        f' <div><small style="color:rgba(248,244,237,0.5);">الصفحة</small><br>{e(law["Magazine_Page"])}</div>'
        f' <div><small style="color:rgba(248,244,237,0.5);">تاريخ الجريدة</small><br>{e(law["Magazine_Date"])}</div>'
        ' </div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # المواد المعدلة
    if is_amendment:
        render_amended_section(law, kind)

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    st.markdown(
        '<p style="color:var(--cream);font-weight:600;font-size:1.05rem;margin-bottom:0.5rem;">'
        '📜 مواد القانون</p>',
        unsafe_allow_html=True,
    )

    if not articles:
        st.info("لا توجد مواد لهذا القانون.")
        if st.button("➕ إضافة أول مادة", key=f"add_first_{law['db_id']}", type="primary"):
            law["Articles"].append({
                "article_number": "1",
                "title": "المادة 1",
                "enforcement_date": datetime.now().strftime("%d-%m-%Y"),
                "text": "",
            })
            if save_law(law, kind):
                toast()
            st.session_state.article_idx = 0
            st.session_state.editing = True
            st.session_state.edit_idx = 0
            st.rerun()
    else:
        col_sel, col_add = st.columns([5, 1])
        with col_sel:
            options = [f"المادة {a.get('article_number','?')}" for a in articles]
            safe_art = min(st.session_state.get("article_idx", 0), art_count - 1)
            selected = st.selectbox("", options, index=safe_art, label_visibility="collapsed")
            art_idx = options.index(selected)
            st.session_state.article_idx = art_idx

        with col_add:
            st.markdown('<div style="margin-top:1.8rem;"></div>', unsafe_allow_html=True)
            if st.button("➕", help="إضافة مادة جديدة",
                         key=f"addart_{law['db_id']}", use_container_width=True):
                law["Articles"].append({
                    "article_number": str(art_count + 1),
                    "title": f"المادة {art_count + 1}",
                    "enforcement_date": datetime.now().strftime("%d-%m-%Y"),
                    "text": "",
                })
                if save_law(law, kind):
                    toast()
                st.session_state.article_idx = art_count
                st.session_state.editing = True
                st.session_state.edit_idx = art_count
                st.rerun()

        art_idx = min(art_idx, art_count - 1)
        art = articles[art_idx]

        col_title, col_edit = st.columns([9, 1])
        with col_title:
            title_display = art.get("title") or f"المادة {art.get('article_number','?')}"
            st.markdown(
                f'<div style="color:var(--gold);font-weight:700;font-size:1.05rem;margin-bottom:0.5rem;">'
                f'{e(title_display)}</div>',
                unsafe_allow_html=True,
            )

        with col_edit:
            st.markdown('<div style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)
            if st.button("✏️", help="تعديل هذه المادة",
                         key=f"editbtn_{law['db_id']}_{art_idx}", use_container_width=True):
                st.session_state.editing = True
                st.session_state.edit_idx = art_idx
                st.rerun()

        st.markdown(
            f'<div class="article-text">{e(art.get("text","—"))}</div>'
            f'<div style="margin-top:0.8rem;font-size:0.9rem;">'
            f' <span style="color:rgba(201,168,76,0.8);">تاريخ النفاذ:</span> '
            f' <span style="color:var(--gold-light);">{e(art.get("enforcement_date","—"))}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # أزرار التنقل
    st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
    _art_idx = art_idx if articles else 0
    _idx = idx

    col_prev, col_next = st.columns(2)
    with col_prev:
        if articles and _art_idx > 0:
            st.button(
                "◄ السابق (مادة)", use_container_width=True,
                on_click=lambda a=_art_idx: st.session_state.update(article_idx=a - 1),
                key=f"prev_art_{law['db_id']}_{_art_idx}",
            )
        elif _idx > 0:
            st.button(
                "◄ السابق (قانون)", use_container_width=True,
                on_click=lambda i=_idx: st.session_state.update(
                    current_idx=i - 1, article_idx=0
                ),
                key=f"prev_law_{_idx}",
            )
        else:
            st.button("◄ السابق", disabled=True, use_container_width=True,
                      key="prev_disabled")

    with col_next:
        if articles and _art_idx < art_count - 1:
            st.button(
                "التالي (مادة) ►", use_container_width=True,
                on_click=lambda a=_art_idx: st.session_state.update(article_idx=a + 1),
                key=f"next_art_{law['db_id']}_{_art_idx}",
            )
        elif _idx < total - 1:
            st.button(
                "التالي (قانون) ►", type="primary", use_container_width=True,
                on_click=lambda i=_idx: st.session_state.update(
                    current_idx=i + 1, article_idx=0
                ),
                key=f"next_law_{_idx}",
            )
        else:
            st.button("التالي ►", disabled=True, use_container_width=True,
                      key="next_disabled")

# =====================================================
# MAIN
# =====================================================
def main():
    st.set_page_config(page_title="مراجعة التشريعات", layout="wide", page_icon="⚖️")

    try:
        init_db()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return

    # migration أولي (معطل - شغله خارجياً فقط)
    # if not has_migration_run("initial_data_load_v1"):
    #     with st.spinner("جاري تحميل البيانات الأولية…"):
    #         t1 = migrate_law_kind("قانون ج1", "V02_Laws_P1.json")
    #         t2 = migrate_law_kind("قانون ج2", "V02_Laws_P2.json")
    #         mark_migration_done("initial_data_load_v1")
    #         st.success(f"تم التحميل! أُضيف {t1 + t2} سجل")
    #         st.rerun()

    st.sidebar.markdown("### نوع القانون")
    kind = st.sidebar.radio("", LAW_KINDS, key="kind_radio")

    if st.sidebar.button("🔄 تحديث البيانات"):
        ck = f"laws_{kind}"
        st.session_state.pop(ck, None)
        for k in [k for k in st.session_state if k.startswith(f"amended_buf_{kind}_")]:
            st.session_state.pop(k)
        st.rerun()

    for key, val in [("current_idx", 0), ("article_idx", 0),
                     ("editing", False), ("edit_idx", 0)]:
        st.session_state.setdefault(key, val)

    cache_key = f"laws_{kind}"
    if st.session_state.get("last_kind") != kind:
        st.session_state.pop(cache_key, None)
        for k in [k for k in st.session_state if k.startswith(f"amended_buf_")]:
            st.session_state.pop(k)
        st.session_state.current_idx = 0
        st.session_state.article_idx = 0
        st.session_state.editing = False
        st.session_state.last_kind = kind

    if cache_key not in st.session_state:
        st.session_state[cache_key] = load_laws(kind)

    laws = st.session_state[cache_key]
    total = len(laws)

    if total == 0:
        st.warning(f"لا توجد بيانات لـ {kind}")
        return

    st.session_state.current_idx = min(st.session_state.current_idx, total - 1)
    idx = st.session_state.current_idx

    if st.session_state.current_idx >= total:
        st.balloons()
        st.markdown("""
            <div style="text-align:center;padding:5rem 1rem;">
                <div style="font-size:6rem;">🏛️</div>
                <h2 style="color:var(--gold);">تمت مراجعة جميع القوانين!</h2>
            </div>
        """, unsafe_allow_html=True)
        if st.button("↺ ابدأ من جديد", type="primary"):
            st.session_state.current_idx = 0
            st.rerun()
        return

    if st.session_state.editing:
        edit_article_screen(laws[idx], st.session_state.edit_idx, kind)
    else:
        show_law(idx, laws, kind)

if __name__ == "__main__":
    main()
