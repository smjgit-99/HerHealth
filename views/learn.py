"""One 'Learn' page: Health Library (conditions) and Medical Glossary as two sections."""
import streamlit as st

from modules import ui
from modules.translate import tr_list
from views import glossary, info

SECTIONS = {"Conditions": info.render, "Glossary": glossary.render}


def render():
    head, sub, *names = tr_list(["Learn", "Plain-language health guides and a glossary of medical terms.", *SECTIONS])
    ui.page_header(head, sub)
    label = dict(zip(SECTIONS, names))
    st.session_state.setdefault("learn_tab", "Conditions")  # Home tiles can preselect a section via ui.go
    pick = st.radio("Section", list(SECTIONS), key="learn_tab", horizontal=True, label_visibility="collapsed",
                    format_func=lambda k: label[k])
    SECTIONS[pick]()
