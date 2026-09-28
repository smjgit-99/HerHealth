from urllib.parse import quote_plus

import streamlit as st

from modules import ui
from modules.content import load_json
from modules.translate import current_code, tr_list

LABELS = ["What it is", "Common signs", "Why it happens", "What usually helps", "See a doctor if",
          "Research papers and guidelines", "Browse more papers on PubMed",
          "Papers are written in English for doctors and researchers. Ask a doctor if something is unclear."]


def render():
    ui.page_header(*tr_list(["Health Library", "Plain-language guides for common women's health conditions."]))
    data = load_json("diseases")
    st.caption(f"{len(data)} topics in this demo, written in simple language.")
    name = st.selectbox("Choose a topic", [d["name"] for d in data], key="info_topic")
    d = next(x for x in data if x["name"] == name)

    texts = LABELS + [name, d["overview"], d["causes"], d["care"], d["see_doctor"]] + d["signs"]
    out = tr_list(texts)
    L = dict(zip(LABELS, out[:len(LABELS)]))
    n, overview, causes, care, see, *signs = out[len(LABELS):]

    st.subheader(n if current_code() == "en" else f"{n} ({name})")
    st.markdown(f"**{L['What it is']}**\n\n{overview}")
    st.markdown(f"**{L['Common signs']}**")
    for s in signs:
        st.markdown(f"- {s}")
    st.markdown(f"**{L['Why it happens']}**\n\n{causes}")
    st.markdown(f"**{L['What usually helps']}**\n\n{care}")
    st.warning(f"**{L['See a doctor if']}:** {see}")

    st.divider()
    st.subheader(f"📄 {L['Research papers and guidelines']}")
    for p in d["papers"]:
        st.markdown(f"- [{p['title']}]({p['url']})  \n  {p['cite']}")
    st.markdown(f"- [{L['Browse more papers on PubMed']}](https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(d['pubmed'])})")
    st.caption(L["Papers are written in English for doctors and researchers. Ask a doctor if something is unclear."])
