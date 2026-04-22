# app.py - منصة التدقيق القانوني على Streamlit مع دعم Railway
import streamlit as st
import json
import os
import yaml
from datetime import datetime
import streamlit_authenticator as stauth
from db import (
    init_db, save_base_law, save_modification, save_amendment,
    load_all_data, save_progress, load_progress, load_all_progress,
    get_law_by_id, get_modifications_by_law
)

# =====================================================
# PAGE CONFIG - MUST BE FIRST
# =====================================================
st.set_page_config(
    page_title="منصة التدقيق القانوني",
    layout="wide",
    page_icon="⚖️",
    initial_sidebar_state="expanded"
)

# =====================================================
# CONSTANTS
# =====================================================
LAW_KINDS = ["قانون ج1", "قانون ج2", "قانون ج3", "قانون ج4", "قانون ج5"]
KIND_TO_KEY = {
    "قانون ج1": "p1",
    "قانون ج2": "p2", 
    "قانون ج3": "p3",
    "قانون ج4": "p4",
    "قانون ج5": "p5",
}

# =====================================================
# CUSTOM CSS - نفس تصميم HTML الأصلي
# =====================================================
def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@300;400;600;700;900&display=swap');
    
    * {
        font-family: 'Cairo', sans-serif !important;
    }
    
    .stApp {
        background: #0d1117;
        background-image: radial-gradient(ellipse 800px 600px at 20% 10%, rgba(201,168,76,0.06), transparent 70%),
                          radial-gradient(ellipse 600px 400px at 80% 90%, rgba(45,212,191,0.05), transparent 70%);
    }
    
    /* Main container */
    .main-header {
        text-align: center;
        padding: 2rem 0 1.5rem;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid rgba(201,168,76,0.25);
        position: relative;
    }
    
    .main-header h1 {
        font-family: 'Amiri', serif !important;
        color: #c9a84c !important;
        font-size: 2.2rem !important;
        margin: 0 !important;
        text-shadow: 0 0 40px rgba(201,168,76,0.3);
    }
    
    .main-header p {
        color: #8898aa;
        margin: 0;
        font-size: 0.85rem;
    }
    
    /* Law Card */
    .law-card {
        background: linear-gradient(135deg, #132252 0%, #1a2f6a 100%);
        border: 1px solid rgba(201,168,76,0.55);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    
    .law-title {
        font-family: 'Amiri', serif !important;
        color: #e8c96a !important;
        font-size: 1.3rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    .law-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
    }
    
    .meta-chip {
        background: rgba(201,168,76,0.1);
        border: 1px solid rgba(201,168,76,0.2);
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 0.75rem;
        color: #b0a080;
    }
    
    .meta-chip strong {
        color: #c9a84c;
    }
    
    /* Modification Card */
    .mod-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(201,168,76,0.2);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        transition: all 0.2s;
    }
    
    .mod-card:hover {
        border-color: rgba(201,168,76,0.4);
        background: rgba(255,255,255,0.06);
    }
    
    .mod-title {
        color: #2dd4bf !important;
        font-size: 1rem !important;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* Diff styling */
    .diff-added {
        background: rgba(74,222,128,0.2);
        color: #4ade80;
        padding: 0 2px;
        border-radius: 3px;
    }
    
    .diff-removed {
        background: rgba(248,113,113,0.2);
        color: #f87171;
        text-decoration: line-through;
        padding: 0 2px;
        border-radius: 3px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #0f2044 !important;
        border-left: 1px solid rgba(201,168,76,0.25) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    
    /* Custom divider */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #c9a84c, transparent);
        margin: 1.5rem 0;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(45,212,191,0.08);
        border: 1px solid rgba(45,212,191,0.2);
        border-radius: 50px;
        padding: 4px 14px;
        font-size: 0.7rem;
        color: #2dd4bf;
    }
    
    .status-dot {
        width: 6px;
        height: 6px;
        background: #2dd4bf;
        border-radius: 50%;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }
    
    /* Streamlit component overrides */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: #1e2530 !important;
        border: 1px solid #2d3748 !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #7a6030, #c9a84c) !important;
        color: #0a1628 !important;
        border: none !important;
    }
    
    hr {
        border-color: rgba(201,168,76,0.25) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 5px;
        height: 5px;
    }
    ::-webkit-scrollbar-track {
        background: #0d1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #3d4f6a;
        border-radius: 3px;
    }
    </style>
    
    <script>
    // JavaScript for theme toggling (will work via st.markdown with HTML)
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }
    </script>
    """, unsafe_allow_html=True)

# =====================================================
# AUTHENTICATION
# =====================================================
credentials_str = os.environ.get("CREDENTIALS_YAML")
if not credentials_str:
    st.error("❌ لم يتم العثور على متغير CREDENTIALS_YAML في Railway")
    st.info("📌 أضف المتغير في Railway Dashboard > Variables")
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
    preauthorized=config.get('preauthorized', [])
)

# Display login form
authenticator.login(location='main')

# Check authentication status
if st.session_state.get("authentication_status"):
    st.session_state.authenticated = True
    st.session_state.user_name = st.session_state.get("name") or st.session_state.get("username")
elif st.session_state.get("authentication_status") is False:
    st.error('❌ اسم المستخدم أو كلمة المرور غير صحيحة')
    st.stop()
else:
    st.warning('🔐 الرجاء إدخال اسم المستخدم وكلمة المرور')
    st.stop()

# =====================================================
# INIT DATABASE
# =====================================================
try:
    init_db()
    st.session_state.db_ready = True
except Exception as e:
    st.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
    st.stop()

# Apply custom CSS
apply_custom_css()

# =====================================================
# HELPER FUNCTIONS
# =====================================================
def format_diff(old_text, new_text):
    """Simple diff formatter for display"""
    if old_text == new_text:
        return new_text
    
    # Simple word-by-word diff
    old_words = old_text.split() if old_text else []
    new_words = new_text.split() if new_text else []
    
    result = []
    i, j = 0, 0
    
    while i < len(old_words) or j < len(new_words):
        if i < len(old_words) and j < len(new_words) and old_words[i] == new_words[j]:
            result.append(new_words[j])
            i += 1
            j += 1
        elif j < len(new_words) and (i >= len(old_words) or new_words[j] not in old_words):
            result.append(f'<span class="diff-added">{new_words[j]}</span>')
            j += 1
        else:
            result.append(f'<span class="diff-removed">{old_words[i]}</span>')
            i += 1
    
    return ' '.join(result)

def render_law_card(law, idx, total):
    """عرض بطاقة القانون بشكل جميل"""
    st.markdown(f"""
    <div class="law-card">
        <div class="law-title">⚖️ {law.get('law_name', 'غير مسمى')}</div>
        <div class="law-meta">
            <span class="meta-chip"><strong>رقم:</strong> {law.get('law_number', '—')}</span>
            <span class="meta-chip"><strong>سنة:</strong> {law.get('year', '—')}</span>
            <span class="meta-chip"><strong>الجريدة:</strong> {law.get('magazine_number', '—')}</span>
            <span class="meta-chip"><strong>الصفحة:</strong> {law.get('magazine_page', '—')}</span>
            <span class="meta-chip"><strong>📚 القانون {idx + 1} من {total}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_modification_card(mod, idx, total_mods):
    """عرض بطاقة التعديل"""
    st.markdown(f"""
    <div class="mod-card">
        <div class="mod-title">✏️ {mod.get('mod_name', 'تعديل غير مسمى')}</div>
        <div class="law-meta">
            <span class="meta-chip"><strong>رقم التعديل:</strong> {mod.get('mod_number', '—')}</span>
            <span class="meta-chip"><strong>سنة:</strong> {mod.get('mod_year', '—')}</span>
            <span class="meta-chip"><strong>الجريدة:</strong> {mod.get('mod_mg_number', '—')}</span>
            <span class="meta-chip"><strong>المواد:</strong> {len(mod.get('mod_articles', []))}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# MAIN APP
# =====================================================
def main():
    # Header with custom styling
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ منصة التدقيق القانوني</h1>
        <p>مراجعة وتدقيق التشريعات والقوانين</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(201,168,76,0.25); margin-bottom: 1rem;">
            <div style="font-size: 2.5rem;">⚖️</div>
            <div style="font-family: 'Amiri', serif; font-size: 1.2rem; color: #c9a84c;">التشريعات</div>
        </div>
        """, unsafe_allow_html=True)
        
        # User info
        st.markdown(f"""
        <div style="background: rgba(201,168,76,0.1); border: 1px solid rgba(201,168,76,0.2); border-radius: 10px; padding: 0.6rem 1rem; margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; color: #8898aa;">👤 المستخدم</div>
            <div style="font-weight: 600;">{st.session_state.user_name}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Law kind selection
        st.markdown("### 📂 نوع القانون")
        kind = st.radio("", LAW_KINDS, label_visibility="collapsed")
        
        st.markdown("---")
        
        # Progress display
        all_progress = load_all_progress(st.session_state.user_name)
        if any(v > 0 for v in all_progress.values()):
            st.markdown("### 📊 تقدمك")
            for k, idx in all_progress.items():
                if idx > 0:
                    st.markdown(f"- {k}: القانون #{idx + 1}")
        
        st.markdown("---")
        
        # Logout button
        authenticator.logout("🚪 تسجيل الخروج", location="sidebar")
        
        # Status indicator
        st.markdown(f"""
        <div class="status-badge">
            <div class="status-dot"></div>
            جلسة تدقيق نشطة
        </div>
        """, unsafe_allow_html=True)
    
    # Load data from database
    data_key = KIND_TO_KEY[kind]
    data = load_all_data(data_key)
    
    if not data:
        st.info("📭 لا توجد بيانات في قاعدة البيانات")
        
        # Upload JSON option
        with st.expander("📤 استيراد بيانات من JSON", expanded=True):
            st.markdown("قم برفع ملف `data.js` أو ملف JSON يحتوي على البيانات")
            uploaded_file = st.file_uploader("اختر ملف JSON", type=["json", "js"])
            
            if uploaded_file:
                try:
                    content = uploaded_file.read().decode("utf-8")
                    # Clean up if it's a JS file with variable assignment
                    if "LAW_DATA =" in content:
                        content = content.split("LAW_DATA =")[1].strip()
                        if content.endswith(";"):
                            content = content[:-1]
                    
                    law_data = json.loads(content)
                    
                    if isinstance(law_data, list) and len(law_data) > 0:
                        # Import data to database
                        with st.spinner("جاري استيراد البيانات..."):
                            for law_entry in law_data:
                                base_law = law_entry.get("base_law", {})
                                law_id = save_base_law(data_key, base_law)
                                
                                modifications = law_entry.get("modifications", [])
                                for mod in modifications:
                                    save_modification(data_key, law_id, mod)
                            
                            st.success(f"✅ تم استيراد {len(law_data)} قانون بنجاح!")
                            st.rerun()
                    else:
                        st.error("تنسيق الملف غير صحيح")
                except Exception as e:
                    st.error(f"خطأ في قراءة الملف: {str(e)}")
        
        return
    
    # Progress tracking
    progress_key = f"progress_{kind}"
    if progress_key not in st.session_state:
        saved_idx = load_progress(st.session_state.user_name, kind)
        st.session_state.current_idx = min(saved_idx, len(data) - 1)
        st.session_state[progress_key] = True
    
    # Law selector with custom styling
    current_idx = st.session_state.current_idx
    current_law_data = data[current_idx]
    current_law = current_law_data["base_law"]
    modifications = current_law_data["modifications"]
    
    # Law navigation
    col_prev, col_selector, col_next = st.columns([1, 3, 1])
    
    with col_prev:
        if current_idx > 0:
            if st.button("◄ السابق", use_container_width=True):
                st.session_state.current_idx = current_idx - 1
                save_progress(st.session_state.user_name, kind, current_idx - 1)
                st.rerun()
    
    with col_selector:
        law_names = [f"{i+1}. {d['base_law'].get('law_name', 'غير مسمى')} ({d['base_law'].get('year', '—')})" 
                     for i, d in enumerate(data)]
        selected = st.selectbox(
            "اختر القانون",
            range(len(law_names)),
            format_func=lambda i: law_names[i],
            index=current_idx,
            label_visibility="collapsed"
        )
        if selected != current_idx:
            st.session_state.current_idx = selected
            save_progress(st.session_state.user_name, kind, selected)
            st.rerun()
    
    with col_next:
        if current_idx < len(data) - 1:
            if st.button("التالي ►", use_container_width=True, type="primary"):
                st.session_state.current_idx = current_idx + 1
                save_progress(st.session_state.user_name, kind, current_idx + 1)
                st.rerun()
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Display current law
    render_law_card(current_law, current_idx, len(data))
    
    # Base law articles (collapsible)
    base_articles = current_law.get("base_articles", {})
    if isinstance(base_articles, str):
        try:
            base_articles = json.loads(base_articles)
        except:
            base_articles = {}
    
    articles_list = base_articles.get("full_text_subjects", []) if isinstance(base_articles, dict) else []
    
    with st.expander(f"📜 مواد القانون الأساسي ({len(articles_list)} مادة)", expanded=False):
        if articles_list:
            for article in articles_list[:10]:  # Show first 10
                st.markdown(f"""
                <div style="background: rgba(45,212,191,0.03); border-right: 2px solid #2dd4bf; padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-radius: 8px;">
                    <strong style="color: #2dd4bf;">المادة {article.get('article_num', '?')}</strong>
                    {f' - {article.get("title", "")}' if article.get("title") else ''}
                    <div style="font-size: 0.85rem; margin-top: 0.5rem; line-height: 1.6;">{article.get('content', 'لا يوجد نص')[:300]}...</div>
                </div>
                """, unsafe_allow_html=True)
            if len(articles_list) > 10:
                st.info(f"... و {len(articles_list) - 10} مواد أخرى")
        else:
            st.info("لا توجد مواد مسجلة")
    
    # Modifications section
    if modifications:
        st.markdown("### 📝 التعديلات التشريعية")
        st.markdown(f'<span class="meta-chip" style="margin-bottom: 1rem; display: inline-block;">📊 عدد التعديلات: {len(modifications)}</span>', unsafe_allow_html=True)
        
        # Modification selector
        mod_options = [f"{m.get('mod_name', 'تعديل')} - {m.get('mod_year', '?')} (رقم {m.get('mod_number', '?')})" 
                       for m in modifications]
        
        selected_mod_idx = st.selectbox(
            "اختر التعديل للاطلاع على التفاصيل",
            range(len(mod_options)),
            format_func=lambda i: mod_options[i],
            key="mod_selector"
        )
        
        selected_mod = modifications[selected_mod_idx]
        render_modification_card(selected_mod, selected_mod_idx, len(modifications))
        
        # Modified articles
        mod_articles = selected_mod.get("mod_articles", [])
        if mod_articles:
            with st.expander(f"📋 المواد المعدلة في هذا التعديل ({len(mod_articles)} مادة)", expanded=True):
                for article in mod_articles:
                    st.markdown(f"""
                    <div style="background: rgba(45,212,191,0.03); border-right: 2px solid #c9a84c; padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-radius: 8px;">
                        <strong style="color: #c9a84c;">المادة {article.get('article_num', '?')}</strong>
                        {f' - {article.get("title", "")}' if article.get("title") else ''}
                        <div style="font-size: 0.85rem; margin-top: 0.5rem; line-height: 1.6;">{article.get('content', 'لا يوجد نص')[:300]}...</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Description articles (descArticles)
        desc_articles = selected_mod.get("desc_articles", [])
        if desc_articles:
            with st.expander(f"📖 وصف التعديل - المواد المذكورة ({len(desc_articles)} مادة)", expanded=False):
                for article in desc_articles:
                    st.markdown(f"""
                    <div style="background: rgba(192,132,252,0.03); border-right: 2px solid #c084fc; padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-radius: 8px;">
                        <strong style="color: #c084fc;">المادة {article.get('article_number', '?')}</strong>
                        {f' - {article.get("title", "")}' if article.get("title") else ''}
                        <div style="font-size: 0.85rem; margin-top: 0.5rem; line-height: 1.6;">{article.get('text', 'لا يوجد نص')[:300]}...</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # =====================================================
    # COMPARISON SECTION - Where users can edit articles
    # =====================================================
    if modifications:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 🔍 المقارنة التفصيلية مع إمكانية التعديل")
        st.caption("في هذا القسم يمكنك مقارنة النصوص قبل وبعد التعديل، وتعديل النصوص حسب الحاجة - سيتم حفظ التعديلات في قاعدة البيانات")
        
        # Create comparison between original and selected modification
        comparison_mod_idx = st.selectbox(
            "اختر التعديل للمقارنة",
            range(len(mod_options)),
            format_func=lambda i: mod_options[i],
            key="compare_selector"
        )
        
        compare_mod = modifications[comparison_mod_idx]
        
        # Get articles from base law
        base_articles_list = base_articles.get("full_text_subjects", []) if isinstance(base_articles, dict) else []
        mod_articles_list = compare_mod.get("mod_articles", [])
        
        # Create maps for easy lookup
        base_map = {str(a.get('article_num', '')): a for a in base_articles_list}
        mod_map = {str(a.get('article_num', '')): a for a in mod_articles_list}
        
        # Get all article numbers
        all_article_nums = sorted(set(list(base_map.keys()) + list(mod_map.keys())), 
                                   key=lambda x: int(x) if x.isdigit() else 0)
        
        if all_article_nums:
            # Article selector
            article_options = [f"المادة {num}" for num in all_article_nums]
            selected_article_idx = st.selectbox(
                "اختر المادة للمقارنة",
                range(len(article_options)),
                format_func=lambda i: article_options[i],
                key="article_selector"
            )
            
            article_num = all_article_nums[selected_article_idx]
            base_article = base_map.get(article_num, {})
            mod_article = mod_map.get(article_num, {})
            
            base_text = base_article.get('content', 'لا يوجد نص')
            mod_text = mod_article.get('content', 'لا يوجد نص')
            
            # Display comparison with edit capability
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div style="background: rgba(248,113,113,0.02); border: 1px solid rgba(248,113,113,0.2); border-radius: 10px; padding: 1rem;">
                    <div style="font-weight: 700; color: #f87171; margin-bottom: 0.5rem;">📜 قبل التعديل</div>
                </div>
                """, unsafe_allow_html=True)
                original_text = st.text_area(
                    "نص المادة قبل التعديل",
                    value=base_text,
                    height=250,
                    key=f"orig_text_{comparison_mod_idx}_{article_num}",
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            with col2:
                st.markdown("""
                <div style="background: rgba(74,222,128,0.02); border: 1px solid rgba(74,222,128,0.2); border-radius: 10px; padding: 1rem;">
                    <div style="font-weight: 700; color: #4ade80; margin-bottom: 0.5rem;">✨ بعد التعديل (قابل للتعديل)</div>
                </div>
                """, unsafe_allow_html=True)
                edited_text = st.text_area(
                    "نص المادة بعد التعديل",
                    value=mod_text,
                    height=250,
                    key=f"edit_text_{comparison_mod_idx}_{article_num}",
                    help="يمكنك تعديل هذا النص وسيتم حفظ التغيير",
                    label_visibility="collapsed"
                )
            
            # Save button
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button("💾 حفظ التعديل", type="primary", use_container_width=True):
                    if edited_text != mod_text:
                        # Save the amendment to database
                        mod_id = compare_mod.get('id')
                        if mod_id:
                            success = save_amendment(
                                kind=data_key,
                                mod_id=mod_id,
                                article_num=article_num,
                                old_text=mod_text,
                                new_text=edited_text,
                                user=st.session_state.user_name
                            )
                            if success:
                                st.success(f"✅ تم حفظ تعديل المادة {article_num} بنجاح!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ حدث خطأ أثناء حفظ التعديل")
                        else:
                            st.error("❌ لم يتم العثور على معرف التعديل")
                    else:
                        st.info("ℹ️ لم يتم إجراء أي تغيير في النص")
            
            # Show amendment history for this article
            amended_articles = compare_mod.get("amended_articles", [])
            if isinstance(amended_articles, str):
                try:
                    amended_articles = json.loads(amended_articles)
                except:
                    amended_articles = []
            
            article_amendments = [a for a in amended_articles if a.get('article_number') == article_num]
            
            if article_amendments:
                st.markdown("---")
                st.markdown("#### 📋 سجل تعديلات هذه المادة")
                for amend in reversed(article_amendments[-5:]):
                    st.markdown(f"""
                    <div style="background: rgba(45,212,191,0.05); border-radius: 8px; padding: 0.8rem; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span>👤 <strong>{amend.get('edited_by', 'مجهول')}</strong></span>
                            <span>📅 {amend.get('edited_at', '')[:19]}</span>
                            <span>🔄 {amend.get('type', 'تعديل')}</span>
                        </div>
                        <details>
                            <summary style="cursor: pointer; color: #2dd4bf;">عرض التفاصيل</summary>
                            <div style="margin-top: 0.5rem;">
                                <div style="background: rgba(248,113,113,0.1); padding: 0.5rem; border-radius: 6px; margin-bottom: 0.5rem;">
                                    <strong>النص القديم:</strong><br/>
                                    <code style="font-size: 0.8rem;">{amend.get('old_text', '')[:200]}...</code>
                                </div>
                                <div style="background: rgba(74,222,128,0.1); padding: 0.5rem; border-radius: 6px;">
                                    <strong>النص الجديد:</strong><br/>
                                    <code style="font-size: 0.8rem;">{amend.get('new_text', '')[:200]}...</code>
                                </div>
                            </div>
                        </details>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("لا توجد مواد للمقارنة في هذا التعديل")
    
    # Footer
    st.markdown("""
    <div style="border-top: 1px solid rgba(201,168,76,0.25); margin-top: 2rem; padding: 1rem 0; text-align: center;">
        <div style="font-size: 0.7rem; color: #8898aa;">
            منصة التدقيق القانوني · جميع الحقوق محفوظة · أداة تدقيق مساعدة ولا تُعدّ مرجعاً قانونياً رسمياً
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
