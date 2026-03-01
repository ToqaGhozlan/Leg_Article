import streamlit as st
import json
import os
import html as html_lib
from datetime import datetime
import random
import shutil

# ────────────────────────────────────────────────
# ثوابت معدلة لدعم Railway Volume + التطوير المحلي
# ────────────────────────────────────────────────
DATA_DIR = os.getenv("DATA_DIR", "./data")  # على Railway: /app/data    محليًا: ./data

DATA_PATHS = {
    "قانون ج1": os.path.join(DATA_DIR, "V02_Laws_P1.json"),
    "قانون ج2": os.path.join(DATA_DIR, "V02_Laws_P2.json"),
}

AMEND_TYPES = ["تعديل مادة", "إضافة مادة", "إلغاء مادة"]

AMEND_BADGE_CSS = {
    "تعديل مادة": "badge-edit",
    "إضافة مادة": "badge-add",
    "إلغاء مادة": "badge-del",
}

# ────────────────────────────────────────────────
# نسخ الملفات الأولية من مجلد app/ إلى الـ volume إذا لم تكن موجودة
# ────────────────────────────────────────────────
def initialize_data_files():
    """
    تنسخ الملفات الأولية من مجلد app/ في الـ repository
    إلى مسار الـ volume في أول تشغيل
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # الملفات موجودة داخل مجلد app/ في الـ repo
    initial_files = {
        "قانون ج1": os.path.join("app", "V02_Laws_P1.json"),
        "قانون ج2": os.path.join("app", "V02_Laws_P2.json")
    }

    for kind, src_path in initial_files.items():
        target_path = DATA_PATHS[kind]

        if not os.path.exists(target_path) and os.path.exists(src_path):
            try:
                shutil.copy(src_path, target_path)
                st.toast(f"تم نسخ الملف الأولي: {os.path.basename(src_path)}")
            except Exception as e:
                st.warning(f"فشل نسخ الملف الأولي {os.path.basename(src_path)}: {e}")

# ────────────────────────────────────────────────
# تسجيل الدخول
# ────────────────────────────────────────────────
def authenticate(username: str, password: str) -> bool:
    try:
        users = st.secrets.get("users", {"admin": "password"})
    except Exception:
        users = {"admin": "password"}
    return users.get(username.strip(), "") == password.strip()

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
                st.session_state.user_name = username.strip()
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة")
    st.stop()

user_name = st.session_state.user_name

# ────────────────────────────────────────────────
# Styles
# ────────────────────────────────────────────────
def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Tajawal:wght@300;400;500;700;800&display=swap');
        :root {
            --navy: #0f1e3d;
            --navy-mid: #1a2f5a;
            --gold: #c9a84c;
            --gold-light: #e5c97a;
            --cream: #f8f4ed;
        }
        * { font-family: 'Tajawal', sans-serif !important; direction: rtl; text-align: right; }
        .stApp {
            background: var(--navy);
            background-image:
                radial-gradient(ellipse at 80% 10%, rgba(201,168,76,0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 10% 90%, rgba(36,59,110,0.6) 0%, transparent 50%);
            min-height: 100vh;
        }
        .block-container { padding: 2rem 3rem !important; max-width: 980px !important; }
        [data-testid="stSidebar"] {
            background: var(--navy-mid) !important;
            border-left: 2px solid rgba(201,168,76,0.3) !important;
            border-right: none !important;
        }
        [data-testid="stSidebar"] * { color: var(--cream) !important; text-align: right !important; }
        [data-testid="stSidebarCollapsedControl"] { right: 0 !important; left: auto !important; }

        .app-header { text-align:center; padding:2.5rem 0 1.5rem; border-bottom:1px solid rgba(201,168,76,0.3); margin-bottom:2rem; }
        .app-header .seal { font-size:3.5rem; line-height:1; margin-bottom:0.5rem; }
        .app-header h1 { font-family:'Amiri',serif !important; font-size:2.4rem !important; font-weight:700 !important; color:var(--gold) !important; margin:0 0 0.4rem !important; }
        .app-header .subtitle { color:rgba(248,244,237,0.55) !important; font-size:0.95rem; font-weight:300; letter-spacing:2px; }

        .wizard-row { display:flex; justify-content:center; align-items:flex-start; gap:0; margin:1.5rem 0 2rem; direction:ltr; }
        .wizard-item { display:flex; flex-direction:column; align-items:center; position:relative; flex:1; max-width:160px; }
        .wizard-item:not(:last-child)::after { content:''; position:absolute; top:22px; left:50%; width:100%; height:2px; background:rgba(255,255,255,0.1); z-index:0; }
        .wizard-item.done::after { background:var(--gold); }
        .wizard-dot { width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.1rem; font-weight:700; border:2px solid transparent; }
        .wizard-dot.done   { background:var(--gold); color:var(--navy); border-color:var(--gold); }
        .wizard-dot.active { background:transparent; color:var(--gold); border-color:var(--gold); box-shadow:0 0 0 4px rgba(201,168,76,0.3); }
        .wizard-dot.pending{ background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.3); border-color:rgba(255,255,255,0.15); }
        .wizard-label { font-size:0.65rem; margin-top:6px; font-weight:500; text-align:center; line-height:1.25; max-width:140px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .wizard-meta  { font-size:0.58rem; color:rgba(201,168,76,0.7); text-align:center; margin-top:2px; max-width:140px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .wizard-label.done,  .wizard-meta.done  { color:var(--gold); }
        .wizard-label.active,.wizard-meta.active{ color:var(--gold-light); }
        .wizard-label.pending,.wizard-meta.pending{ color:rgba(255,255,255,0.3); }

        .law-card { background:rgba(255,255,255,0.04); border:1px solid rgba(201,168,76,0.25); border-radius:14px; padding:1.8rem; margin:1.2rem 0; direction:rtl; }
        .ac-label { font-size:1.05rem; color:var(--gold); font-weight:700; margin-bottom:0.6rem; }
        .article-text { color:var(--cream); line-height:1.9; white-space:pre-wrap; word-break:break-word; font-size:1.05rem; text-align:right; }
        .record-counter { display:inline-flex; align-items:center; gap:10px; background:rgba(201,168,76,0.15); border:1px solid rgba(201,168,76,0.4); border-radius:30px; padding:8px 20px; color:var(--gold); font-weight:700; margin-bottom:1rem; }
        .gold-divider { height:1px; background:linear-gradient(90deg,transparent,var(--gold),transparent); margin:1.8rem 0; opacity:0.4; }
        .section-title { color:var(--cream) !important; font-size:1.1rem !important; font-weight:600 !important; margin:1.6rem 0 0.9rem !important; }

        /* amend section */
        .amend-section { background:rgba(201,168,76,0.07); border:1px solid rgba(201,168,76,0.3); border-right:4px solid var(--gold); border-radius:10px; padding:1.1rem 1.3rem 0.8rem; margin:1rem 0 1.4rem; }
        .amend-section-title { color:var(--gold); font-weight:700; font-size:0.92rem; margin-bottom:0.8rem; }
        .amend-table-header { display:grid; grid-template-columns:2fr 3fr 1fr; gap:8px; padding:0 4px 6px; border-bottom:1px solid rgba(201,168,76,0.2); margin-bottom:6px; }
        .amend-table-header span { font-size:0.75rem; color:rgba(201,168,76,0.7); font-weight:600; }

        .badge-edit { background:rgba(59,130,246,0.2);  border:1px solid rgba(59,130,246,0.5);  color:#93c5fd; }
        .badge-add  { background:rgba(34,197,94,0.15);  border:1px solid rgba(34,197,94,0.45);  color:#86efac; }
        .badge-del  { background:rgba(239,68,68,0.15);  border:1px solid rgba(239,68,68,0.45);  color:#fca5a5; }
        .amend-badge { display:inline-block; border-radius:20px; padding:3px 12px; font-size:0.8rem; font-weight:700; }

        .save-toast { position:fixed; bottom:1.5rem; left:50%; transform:translateX(-50%); background:rgba(34,197,94,0.9); color:#fff; padding:8px 24px; border-radius:30px; font-weight:700; font-size:0.9rem; z-index:9999; animation: fadeout 2s forwards; }
        @keyframes fadeout { 0%{opacity:1} 70%{opacity:1} 100%{opacity:0} }

        #MainMenu, footer, header { visibility:hidden; }
        </style>
    """, unsafe_allow_html=True)

apply_styles()

st.sidebar.markdown(
    f'<div style="color:var(--gold);font-weight:700;font-size:1.1rem;text-align:center;">👤 {html_lib.escape(user_name)}</div>',
    unsafe_allow_html=True
)
if st.sidebar.button("تسجيل الخروج"):
    for k in ["authenticated", "user_name", "current_idx", "article_idx",
              "editing", "edit_idx", "last_kind", "laws_قانون ج1", "laws_قانون ج2"]:
        st.session_state.pop(k, None)
    st.rerun()

# ────────────────────────────────────────────────
# Data helpers
# ────────────────────────────────────────────────
def _normalize_amended(raw_list: list) -> list:
    out = []
    for a in raw_list:
        if isinstance(a, dict):
            t = a.get("type", "تعديل مادة")
            if t not in AMEND_TYPES:
                mapping = {"تعديل": "تعديل مادة", "إضافة": "إضافة مادة", "إلغاء": "إلغاء مادة"}
                t = mapping.get(t, AMEND_TYPES[0])
            out.append({"number": str(a.get("number", "")).strip(), "type": t})
        else:
            out.append({"number": str(a).strip(), "type": AMEND_TYPES[0]})
    return out

def load_data(kind: str) -> list:
    path = DATA_PATHS.get(kind, "")
    if not os.path.exists(path):
        st.error(f"الملف غير موجود: {path}")
        return []
    try:
        with open(path, encoding="utf-8-sig") as f:
            raw = json.load(f)
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        return []
    result = []
    for item in raw:
        amended_raw = item.get("amended_articles", [])
        result.append({
            "Leg_Name":         str(item.get("Leg_Name", "")).strip(),
            "Leg_Number":       str(item.get("Leg_Number", "")).strip(),
            "Year":             str(item.get("Year", "")).strip(),
            "Magazine_Number":  str(item.get("Magazine_Number", "")).strip() or "—",
            "Magazine_Page":    str(item.get("Magazine_Page", "")).strip() or "—",
            "Magazine_Date":    str(item.get("Magazine_Date", "")).strip() or "—",
            "is_amendment":     bool(item.get("is_amendment", False)),
            "amended_articles": _normalize_amended(amended_raw),
            "Articles":         item.get("Articles", []),
        })
    return result

def save_data(kind: str, data: list) -> bool:
    path = DATA_PATHS.get(kind, "")
    if not path:
        st.error("لم يتم تحديد مسار الملف")
        return False
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8-sig") as f:
                bk = f.read()
            with open(path + ".backup", "w", encoding="utf-8-sig") as f:
                f.write(bk)
    except Exception:
        pass
    try:
        with open(path, "w", encoding="utf-8-sig") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"خطأ في الحفظ: {e}")
        return False

def _show_save_toast():
    msg = random.choice(["✅ حُفظ", "✅ تمام!", "كفو ✅", "✅ محفوظ"])
    st.toast(msg, icon="✅")

# ────────────────────────────────────────────────
# Wizard
# ────────────────────────────────────────────────
def render_wizard(current_idx: int, total: int, data: list):
    visible_count = min(7, total)
    if total <= 7:
        indices = list(range(total))
    elif current_idx < 3:
        indices = list(range(visible_count))
    elif current_idx >= total - 4:
        indices = list(range(total - visible_count, total))
    else:
        indices = list(range(current_idx - 3, current_idx - 3 + visible_count))

    parts = []
    for i in indices:
        if i >= len(data):
            continue
        law = data[i]
        short_name = law["Leg_Name"][:35] + ("..." if len(law["Leg_Name"]) > 35 else "")
        meta = (f"{law['Leg_Number'] or '?'} / {law['Year'] or '?'} "
                f"| جـ {law['Magazine_Number'] or '—'} ص {law['Magazine_Page'] or '—'}")
        cls = "done" if i < current_idx else ("active" if i == current_idx else "pending")
        dot = "✓" if i < current_idx else ("●" if i == current_idx else str(i + 1))
        connector = "done" if i < current_idx else ""
        parts.append(
            f'<div class="wizard-item {connector}">'
            f'  <div class="wizard-dot {cls}">{dot}</div>'
            f'  <div class="wizard-label {cls}">{html_lib.escape(short_name)}</div>'
            f'  <div class="wizard-meta {cls}">{html_lib.escape(meta)}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="wizard-row">{"".join(parts)}</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# قسم المواد المعدَّلة
# ────────────────────────────────────────────────
def render_amended_section(idx: int, data: list, kind: str):
    law = data[idx]
    buf_key = f"amended_buf_{kind}_{idx}"
    if buf_key not in st.session_state:
        st.session_state[buf_key] = [dict(a) for a in law.get("amended_articles", [])]

    amended = st.session_state[buf_key]

    st.markdown('<div class="amend-section">', unsafe_allow_html=True)
    st.markdown('<div class="amend-section-title">📝 المواد المعدَّلة في هذا القانون</div>', unsafe_allow_html=True)

    to_delete = None

    if amended:
        st.markdown("""
            <div class="amend-table-header">
                <span>رقم المادة</span><span>نوع التعديل</span><span></span>
            </div>
        """, unsafe_allow_html=True)

        for row_i, row in enumerate(amended):
            col_num, col_type, col_del = st.columns([2, 3, 1])
            with col_num:
                amended[row_i]["number"] = st.text_input(
                    "رقم", value=row["number"],
                    key=f"amend_num_{kind}_{idx}_{row_i}",
                    label_visibility="collapsed",
                    placeholder="رقم المادة"
                ).strip()
            with col_type:
                cur_idx = AMEND_TYPES.index(row["type"]) if row["type"] in AMEND_TYPES else 0
                amended[row_i]["type"] = st.selectbox(
                    "نوع", AMEND_TYPES,
                    index=cur_idx,
                    key=f"amend_type_{kind}_{idx}_{row_i}",
                    label_visibility="collapsed"
                )
            with col_del:
                st.markdown('<div style="margin-top:0.4rem;"></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"amend_del_{kind}_{idx}_{row_i}",
                             help="حذف هذا السطر", use_container_width=True):
                    to_delete = row_i
    else:
        st.markdown(
            '<p style="color:rgba(248,244,237,0.35);font-size:0.88rem;font-style:italic;margin:0.3rem 0 0.8rem;">'
            'لا توجد مواد معدَّلة — اضغط ➕ لإضافة</p>',
            unsafe_allow_html=True
        )

    col_add, col_save = st.columns([3, 2])
    with col_add:
        if st.button("➕ إضافة مادة", key=f"amend_add_{kind}_{idx}"):
            st.session_state[buf_key].append({"number": "", "type": AMEND_TYPES[0]})
            st.rerun()
    with col_save:
        if st.button("💾 حفظ التغييرات", key=f"amend_save_{kind}_{idx}", type="primary"):
            if to_delete is not None:
                st.session_state[buf_key].pop(to_delete)
            data[idx]["amended_articles"] = [dict(a) for a in st.session_state[buf_key]]
            if save_data(kind, data):
                _show_save_toast()
            st.rerun()

    if to_delete is not None and not st.session_state.get(f"amend_save_{kind}_{idx}"):
        st.session_state[buf_key].pop(to_delete)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    saved_amended = law.get("amended_articles", [])
    if saved_amended:
        badges = "".join(
            f'<span class="amend-badge {AMEND_BADGE_CSS.get(a["type"], "badge-edit")}">'
            f'م {html_lib.escape(a["number"])} · {html_lib.escape(a["type"])}</span>'
            for a in saved_amended if a.get("number")
        )
        if badges:
            st.markdown(
                f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:0.5rem 0 1rem;direction:rtl;">{badges}</div>',
                unsafe_allow_html=True
            )

# ────────────────────────────────────────────────
# عرض القانون
# ────────────────────────────────────────────────
def show_law(idx: int, data: list, total: int, kind: str):
    law = data[idx]
    articles   = law.get("Articles", [])
    art_count  = len(articles)
    current_art = st.session_state.get("article_idx", 0)
    is_amendment = law.get("is_amendment", False)
    progress   = (idx + 1) / total * 100

    st.markdown(f'<div class="record-counter">⚖️ القانون {idx+1} من {total}</div>', unsafe_allow_html=True)
    render_wizard(idx, total, data)

    st.markdown(
        f'<div style="margin:1.2rem 0;">'
        f'  <div style="display:flex;justify-content:space-between;color:rgba(248,244,237,0.7);font-size:0.85rem;margin-bottom:0.4rem;">'
        f'    <span>التقدم</span><span>{progress:.0f}%</span></div>'
        f'  <div style="background:rgba(255,255,255,0.08);height:6px;border-radius:3px;overflow:hidden;">'
        f'    <div style="height:100%;width:{progress:.1f}%;background:linear-gradient(90deg,var(--gold),var(--gold-light));"></div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True
    )

    e = html_lib.escape
    amendment_badge = (
        '<span style="background:rgba(201,168,76,0.25);color:var(--gold);font-size:0.75rem;'
        'font-weight:700;padding:3px 12px;border-radius:20px;'
        'border:1px solid rgba(201,168,76,0.5);margin-right:10px;">⚠️ تعديل</span>'
        if is_amendment else ""
    )
    st.markdown(
        '<div class="law-card">'
        '  <div style="display:flex;align-items:center;margin-bottom:0.8rem;">'
        '    <div style="background:var(--gold);color:var(--navy);font-size:0.8rem;font-weight:800;'
        '         padding:4px 14px;border-radius:20px;display:inline-block;">نص القانون</div>'
        f'   {amendment_badge}'
        '  </div>'
        f' <h3 style="margin:0 0 1rem;color:var(--cream);font-family:\'Amiri\',serif;font-size:1.4rem;line-height:1.5;">{e(law["Leg_Name"])}</h3>'
        '  <div style="display:flex;gap:1.4rem;flex-wrap:wrap;color:var(--gold-light);">'
        f'   <div><small style="color:rgba(248,244,237,0.5);">رقم القانون</small><br>{e(law["Leg_Number"] or "—")}</div>'
        f'   <div><small style="color:rgba(248,244,237,0.5);">السنة</small><br>{e(law["Year"] or "—")}</div>'
        f'   <div><small style="color:rgba(248,244,237,0.5);">رقم الجريدة</small><br>{e(law["Magazine_Number"])}</div>'
        f'   <div><small style="color:rgba(248,244,237,0.5);">الصفحة</small><br>{e(law.get("Magazine_Page","—"))}</div>'
        f'   <div><small style="color:rgba(248,244,237,0.5);">تاريخ الجريدة</small><br>{e(law["Magazine_Date"])}</div>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True
    )

    if is_amendment:
        render_amended_section(idx, data, kind)

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">📜 مواد القانون</p>', unsafe_allow_html=True)

    if not articles:
        st.info("لا توجد مواد لهذا القانون.")
        if st.button("➕ إضافة أول مادة", key=f"add_first_{idx}", type="primary"):
            data[idx]["Articles"].append({
                "article_number": "1", "title": "المادة 1",
                "enforcement_date": datetime.now().strftime("%d-%m-%Y"), "text": ""
            })
            save_data(kind, data)
            st.session_state.article_idx = 0
            st.session_state.editing     = True
            st.session_state.edit_idx    = 0
            st.rerun()
        return

    col_select, col_add = st.columns([5, 1])
    with col_select:
        options   = [f"المادة {a.get('article_number','?')}" for a in articles]
        safe_art  = min(current_art, len(articles) - 1)
        selected  = st.selectbox("", options, index=safe_art, label_visibility="collapsed")
        art_idx   = options.index(selected)
        st.session_state.article_idx = art_idx
    with col_add:
        st.markdown('<div style="margin-top:1.8rem;"></div>', unsafe_allow_html=True)
        if st.button("➕", help="إضافة مادة جديدة", key=f"add_art_{idx}", use_container_width=True):
            data[idx]["Articles"].append({
                "article_number": str(art_count + 1),
                "title": f"المادة {art_count + 1}",
                "enforcement_date": datetime.now().strftime("%d-%m-%Y"), "text": ""
            })
            save_data(kind, data)
            st.session_state.article_idx = art_count
            st.session_state.editing     = True
            st.session_state.edit_idx    = art_count
            st.rerun()

    art_idx = min(art_idx, len(articles) - 1)
    art = articles[art_idx]

    col_title, col_edit = st.columns([9, 1])
    with col_title:
        title_display = art.get("title") or f"المادة {art.get('article_number','?')}"
        st.markdown(f"<div class='ac-label'>{html_lib.escape(title_display)}</div>", unsafe_allow_html=True)
    with col_edit:
        st.markdown('<div style="margin-top:0.8rem;"></div>', unsafe_allow_html=True)
        if st.button("✏️", help="تعديل هذه المادة", key=f"edit_{idx}_{art_idx}", use_container_width=True):
            st.session_state.editing  = True
            st.session_state.edit_idx = art_idx
            st.rerun()

    st.markdown(
        f'<div class="article-text" style="margin-top:0.5rem;">{html_lib.escape(art.get("text","—"))}</div>'
        f'<div style="margin-top:1rem;font-size:0.9rem;">'
        f'  <span style="color:rgba(201,168,76,0.8);">تاريخ النفاذ:</span> '
        f'  <span style="color:var(--gold-light);">{html_lib.escape(art.get("enforcement_date","—"))}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    _art_idx = art_idx
    _idx     = idx
    col_prev, col_next = st.columns(2)
    with col_prev:
        if _art_idx > 0:
            st.button("► السابق (مادة)", use_container_width=True,
                      on_click=lambda a=_art_idx: st.session_state.update(article_idx=a - 1))
        elif _idx > 0:
            st.button("► السابق (قانون)", use_container_width=True,
                      on_click=lambda i=_idx: st.session_state.update(current_idx=i - 1, article_idx=0))
        else:
            st.button("► السابق", disabled=True, use_container_width=True)
    with col_next:
        if _art_idx < art_count - 1:
            st.button("التالي (مادة) ◄", use_container_width=True,
                      on_click=lambda a=_art_idx: st.session_state.update(article_idx=a + 1))
        elif _idx < total - 1:
            st.button("التالي (قانون) ◄", type="primary", use_container_width=True,
                      on_click=lambda i=_idx: st.session_state.update(current_idx=i + 1, article_idx=0))
        else:
            st.button("التالي ◄", disabled=True, use_container_width=True)

# ────────────────────────────────────────────────
# تعديل مادة
# ────────────────────────────────────────────────
def edit_article(law_idx: int, data: list, kind: str):
    law     = data[law_idx]
    max_idx = len(law["Articles"]) - 1
    if max_idx < 0:
        st.warning("لا توجد مواد لهذا القانون.")
        st.session_state.editing = False
        st.rerun()
        return
    art_idx = min(st.session_state.edit_idx, max_idx)
    st.session_state.edit_idx = art_idx
    article = law["Articles"][art_idx]

    with st.form("edit_article_form"):
        st.subheader(f"تعديل المادة {article.get('article_number','?')}")
        num      = st.text_input("رقم المادة",   value=article.get("article_number", ""))
        title    = st.text_input("العنوان",       value=article.get("title", ""))
        enf_date = st.text_input("تاريخ النفاذ",  value=article.get("enforcement_date", ""))
        text     = st.text_area("نص المادة",      value=article.get("text", ""), height=320)

        col1, col2 = st.columns(2)
        if col1.form_submit_button("💾 حفظ التعديل", type="primary"):
            data[law_idx]["Articles"][art_idx] = {
                "article_number": num.strip(),
                "title":          title.strip(),
                "enforcement_date": enf_date.strip(),
                "text":           text.strip(),
            }
            if save_data(kind, data):
                _show_save_toast()
            st.session_state.editing = False
            st.rerun()
        if col2.form_submit_button("إلغاء"):
            st.session_state.editing = False
            st.rerun()

# ────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="مراجعة التشريعات", layout="wide", page_icon="⚖️")

    # نسخ الملفات الأولية مرة واحدة في البداية
    initialize_data_files()

    st.sidebar.markdown("### نوع التشريع")
    kind = st.sidebar.radio("", list(DATA_PATHS.keys()))

    for key, val in [("current_idx", 0), ("article_idx", 0),
                     ("editing", False), ("edit_idx", 0)]:
        if key not in st.session_state:
            st.session_state[key] = val

    cache_key = f"laws_{kind}"

    if st.session_state.get("last_kind") != kind:
        st.session_state[cache_key]  = load_data(kind)
        st.session_state.last_kind   = kind
        st.session_state.current_idx = 0
        st.session_state.article_idx = 0
        st.session_state.editing     = False
        old_kind = st.session_state.get("last_kind", "")
        for k in list(st.session_state.keys()):
            if k.startswith(f"amended_buf_{old_kind}_"):
                del st.session_state[k]

    if cache_key not in st.session_state:
        st.session_state[cache_key] = load_data(kind)

    if st.sidebar.button("🔄 تحديث البيانات"):
        st.session_state[cache_key] = load_data(kind)
        for k in list(st.session_state.keys()):
            if k.startswith(f"amended_buf_{kind}_"):
                del st.session_state[k]
        st.rerun()

    laws  = st.session_state[cache_key]
    total = len(laws)

    if total == 0:
        st.error("لم يتم العثور على قوانين في الملف المحدد")
        return

    st.session_state.current_idx = min(st.session_state.current_idx, total)

    if st.session_state.current_idx >= total:
        st.balloons()
        st.markdown("""
            <div style="text-align:center;padding:6rem 1rem;">
                <div style="font-size:7rem;">🏛️</div>
                <h2 style="color:var(--gold);">تمت مراجعة جميع القوانين بنجاح</h2>
                <p style="color:rgba(248,244,237,0.85);font-size:1.2rem;">عمل ممتاز!</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("↺ ابدأ من جديد", type="primary"):
            st.session_state.current_idx = 0
            st.rerun()
        return

    if st.session_state.editing:
        edit_article(st.session_state.current_idx, laws, kind)
    else:
        show_law(st.session_state.current_idx, laws, total, kind)

if __name__ == "__main__":
    main()
