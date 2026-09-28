import streamlit as st

import config
from modules import llm, ui
from modules.languages import LANGS
from modules.translate import tr, tr_list
from views import checklist, community, dashboard, glossary, info, relaxer, reminders, translator

st.set_page_config(page_title=config.APP_TITLE, page_icon="🌸", layout="wide", initial_sidebar_state="collapsed")
ui.inject_css()

# page key -> (nav label, material icon, render function)
PAGES = {
    "Dashboard": ("Dashboard", "grid_view", dashboard.render),
    "Translator": ("Translator", "description", translator.render),
    "Checklist": ("Checklist", "checklist", checklist.render),
    "Conditions": ("Conditions", "menu_book", info.render),
    "Glossary": ("Glossary", "book_2", glossary.render),
    "Reminders": ("Reminders", "notifications", reminders.render),
    "Community": ("Community", "group", community.render),
    "Relaxer": ("Relaxer", "air", relaxer.render),
}
st.session_state.setdefault("nav_page", "Dashboard")
if st.session_state["nav_page"] not in PAGES:  # stale value from an older session
    st.session_state["nav_page"] = "Dashboard"

# Resolve the language before anything is translated (the selector renders later in the top bar).
st.session_state["lang_code"] = LANGS.get(st.session_state.get("lang_name", "English"), "en")

labels = dict(zip(PAGES, tr_list([v[0] for v in PAGES.values()])))

with st.container(key="topbar"):
    c_brand, c_nav, c_lang = st.columns([1.9, 8.9, 1.75], vertical_alignment="center")
    c_brand.markdown(ui.brand(), unsafe_allow_html=True)
    with c_nav:
        page = st.radio("Go to", list(PAGES), key="nav_page", horizontal=True, label_visibility="collapsed",
                        format_func=lambda k: f":material/{PAGES[k][1]}: {labels[k]}")
    with c_lang:
        ic, sel = st.columns([1, 5], vertical_alignment="center", gap="small")
        ic.markdown(ui.icon("languages", 18, "#5b5870"), unsafe_allow_html=True)
        lang_name = sel.selectbox("Language", list(LANGS), key="lang_name", label_visibility="collapsed")
st.session_state["lang_code"] = LANGS[lang_name]

if page in ("Translator", "Checklist"):  # pages that show report-based results keep the visible reminder
    ui.notice(tr("Educational information only. This is not medical advice. Please talk to a doctor about your health."))
PAGES[page][2]()

ai_note = "AI mode: " + ("ON (plain-language by Claude)" if llm.available() else "OFF (offline rules, still works)")
d_title, d_body = tr_list(["Medical Disclaimer",
                           f"{config.APP_TITLE} provides educational translations, stress management tools, and patient advocacy "
                           "support only. It does not provide medical diagnoses or replace professional healthcare advice.\n\n"
                           "Always consult with a qualified healthcare provider before making medical decisions. "
                           f"{config.APP_TITLE} is designed to support, not replace, the relationship between you and your doctor. "
                           "In case of a medical emergency, contact your local emergency services immediately."])
d_body = d_body.replace("\n\n", "<br><br>")
ui.footer(d_title, d_body, ai_note)
