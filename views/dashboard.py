import streamlit as st

import config
from modules import ui
from modules.languages import LANGS
from modules.translate import tr_list

# (page, icon, title, description, tile gradient, card gradient)
ACTIONS = [
    ("Translator", "file", "Translate a Report", "Upload a medical report and get a plain-language explanation instantly.",
     "#B56BE0,#8A5CD0", "#F5EEFB,#FCEFF6"),
    ("Checklist", "checks", "Doctor Visit Checklist", "Generate questions to ask your doctor based on your report.",
     "#7A8FE6,#5AA9DC", "#EEF1FC,#F1F8FD"),
    ("Conditions", "book", "Health Library", "Browse plain-language guides for common women's health conditions.",
     "#F59B6B,#F2B24C", "#FDEFEA,#FFF8E9"),
    ("Relaxer", "wind", "Mindful Relaxer", "Guided breathing and meditation to ease medical anxiety.",
     "#45C4B0,#4AA3E0", "#E9F8F5,#EEF4FD"),
    ("Glossary", "glossary", "Medical Glossary", "Look up clinical terms and acronyms in plain language.",
     "#F2A65A,#F08A7A", "#FEF2EA,#FDEFF1"),
    ("Reminders", "bell", "Care Reminders", "Schedule medication, cycle, and appointment reminders.",
     "#8E86E8,#5F9BE0", "#EFEEFC,#EEF3FC"),
    ("Community", "users", "Community", "Connect with peers who share similar health journeys.",
     "#E56FA8,#F0708F", "#FCEEF5,#FDF0F1"),
]

TEXT = ["AI-Powered Women's Health Platform", "Understand Your Health. In Your Words.",
        "translates complex medical reports into clear, compassionate language, and gives you the tools to advocate for your care.",
        "Start Translating", "Explore Knowledge Base", "Quick Actions",
        "Private by design", "Reports are read in memory, never stored",
        "Native language support", "Research-linked", "Papers and guidelines for every condition",
        "How it works", "Upload or paste your report", "Read the plain-language summary in your language",
        "Take your questions to your doctor", "This session", "Report analyzed", "Yes", "Not yet", "Reminders set", "Language"]
TEXT += [a[2] for a in ACTIONS] + [a[3] for a in ACTIONS]


def render():
    T = tr_list(TEXT)
    (badge, h1, sub, cta1, cta2, qa_h, f1t, f1s, f2s, f3t, f3s, how, s1, s2, s3, sess, rep, yes, notyet, rems, lang) = T[:21]
    titles, descs = T[21:21 + len(ACTIONS)], T[21 + len(ACTIONS):]

    with st.container(key="hero"):
        st.markdown(f'<span class="ah-badge">{ui.icon("sparkles", 14, ui.PRIMARY_DARK)}{badge}</span>'
                    f'<div class="ah-hero-h">{h1}</div>'
                    f'<p class="ah-hero-p"><b style="color:#2b2840">{config.APP_TITLE}</b> {sub}</p>', unsafe_allow_html=True)
        b1, b2, _ = st.columns([1.5, 1.9, 4])
        b1.button(cta1, type="primary", icon=":material/description:", key="hero_go", width="stretch", on_click=ui.go, args=("Translator",))
        b2.button(cta2, icon=":material/menu_book:", key="hero_kb", width="stretch", on_click=ui.go, args=("Conditions",))

    n_lang = len(LANGS)
    feats = [("shield", "#EFEAF8", ui.PRIMARY_DARK, f1t, f1s),
             ("languages", "#E4F6F1", "#2F9E86", f"{n_lang} Languages", f2s),
             ("search", "#FBEAF0", "#B04663", f3t, f3s)]
    for col, (ic, bg, fg, t, s) in zip(st.columns(3), feats):
        col.markdown(f'<div class="ah-feat"><div class="t" style="background:{bg}">{ui.icon(ic, 22, fg)}</div>'
                     f'<div><b>{t}</b><span>{s}</span></div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="ah-h2">{qa_h}</div>', unsafe_allow_html=True)
    for row in range(0, len(ACTIONS), 3):
        cols = st.columns(3)
        for col, i in zip(cols, range(row, min(row + 3, len(ACTIONS)))):
            page, ic, _, _, tile, card = ACTIONS[i]
            with col:
                with st.container(key=f"qa_{page.lower()}"):
                    st.markdown(f'<style>.st-key-qa_{page.lower()}{{background:linear-gradient(135deg,{card});}}</style>'
                                f'<div class="ah-qa"><div class="t" style="background:linear-gradient(135deg,{tile})">{ui.icon(ic, 24, "#fff")}</div>'
                                f'<div><b>{titles[i]}</b><span>{descs[i]}</span></div></div>', unsafe_allow_html=True)
                    st.button(titles[i], key=f"go_{page.lower()}", on_click=ui.go, args=(page,))

    left, right = st.columns(2, gap="medium")
    left.markdown(f'<div class="ah-card"><h3>{how}</h3>'
                  f'<div class="ah-step"><i>1</i><div>{s1}</div></div>'
                  f'<div class="ah-step"><i>2</i><div>{s2}</div></div>'
                  f'<div class="ah-step"><i>3</i><div>{s3}</div></div></div>', unsafe_allow_html=True)
    done = "analysis" in st.session_state
    right.markdown(f'<div class="ah-card"><h3>{sess}</h3>'
                   f'<div class="ah-step"><i>✓</i><div>{rep}: <b>{yes if done else notyet}</b></div></div>'
                   f'<div class="ah-step"><i>⏰</i><div>{rems}: <b>{len(st.session_state.get("reminders", []))}</b></div></div>'
                   f'<div class="ah-step"><i>文</i><div>{lang}: <b>{st.session_state.get("lang_name", "English")}</b></div></div></div>',
                   unsafe_allow_html=True)
