import streamlit as st
import config
from modules import llm, ui
from modules.languages import LANGS
from modules.translate import tr, tr_list
from views import community, dashboard, learn, translator, relaxer
from auth_ui import render_auth_ui

# 1. Page Config & CSS Injection
st.set_page_config(page_title=config.APP_TITLE, page_icon="🌸", layout="wide", initial_sidebar_state="collapsed")
ui.inject_css()

# 2. Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'nav_page' not in st.session_state:
    st.session_state.nav_page = "Home"

# page key -> (nav label, material icon, render function)
PAGES = {
    "Home": ("Home", "home", dashboard.render),
    "Translator": ("Translator", "description", translator.render),
    "Community": ("Community", "group", community.render),
    "Learn": ("Learn", "menu_book", learn.render),
    "Relax": [":material/air:", "Relax & Breathe", relaxer.render],
}

if st.session_state["nav_page"] not in PAGES:
    st.session_state["nav_page"] = "Home"

st.session_state["lang_code"] = LANGS.get(st.session_state.get("lang_name", "English"), "en")
labels = dict(zip(PAGES, tr_list([v[0] for v in PAGES.values()])))

# --- Navigation Callbacks ---
def go_to_signin():
    st.session_state.nav_page = "Community"

def do_signout():
    st.session_state.logged_in = False

# 3. Custom Top Bar Render
with st.container(key="topbar"):
    c_brand, c_nav, c_lang, c_auth = st.columns([1.9, 7.5, 1.75, 1.2], vertical_alignment="center")
    c_brand.markdown(ui.brand(), unsafe_allow_html=True)
    
    with c_nav:
        page_keys = list(PAGES.keys())
        current_index = page_keys.index(st.session_state["nav_page"]) if st.session_state["nav_page"] in page_keys else 0
        
        # Using index instead of a strict widget key avoids state collision errors
        selected_page = st.radio(
            "Go to", 
            page_keys, 
            index=current_index, 
            horizontal=True, 
            label_visibility="collapsed",
            format_func=lambda k: f":material/{PAGES[k][1]}: {labels[k]}"
        )
        
        if selected_page != st.session_state["nav_page"]:
            st.session_state["nav_page"] = selected_page
            st.rerun()

    with c_lang:
        ic, sel = st.columns([1, 4], vertical_alignment="center", gap="small")
        ic.markdown(ui.icon("languages", 18, "#5b5870"), unsafe_allow_html=True)
        lang_name = sel.selectbox("Language", list(LANGS), key="lang_name", label_visibility="collapsed")
    
    with c_auth:
        if st.session_state.logged_in:
            st.button("Sign Out", type="secondary", on_click=do_signout)
        else:
            st.button("Sign In", type="primary", on_click=go_to_signin)

st.session_state["lang_code"] = LANGS[lang_name]

# 4. Routing Logic
page = st.session_state["nav_page"]
if page == "Community" and not st.session_state.logged_in:
    render_auth_ui()
else:
    if page == "Translator":
        ui.notice(tr("Educational information only. This is not medical advice. Please talk to a doctor about your health."))
    PAGES[page][2]()

# 5. Global Footer
ai_note = "AI mode: " + ("ON" if llm.available() else "OFF")
d_title = tr("Medical Disclaimer")
d_body = tr(f"{config.APP_TITLE} provides educational translations... Always consult with a healthcare provider.")
ui.footer(d_title, d_body, ai_note)