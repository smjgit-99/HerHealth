import streamlit as st

from modules.content import load_json
from modules.translate import current_code, tr_list


def render():
    g = load_json("glossary")
    code = current_code()
    q = st.text_input("Search a term or meaning", key="gl_q")
    cat = st.selectbox("Category", ["All"] + sorted({e["category"] for e in g}), key="gl_cat")

    local = tr_list([e["plain"] for e in g])  # whole list once, then filter locally
    rows = []
    for e, loc in zip(g, local):
        if cat != "All" and e["category"] != cat:
            continue
        hay = " ".join(e["terms"] + [e["plain"], loc]).lower()
        if q.strip() and q.strip().lower() not in hay:
            continue
        row = {"Term": "HbA1c" if e["terms"][0] == "hba1c" else (e["terms"][0].title() if len(e["terms"][0]) > 5 else e["terms"][0].upper()),
               "Also written as": ", ".join(e["terms"][1:]), "Simple meaning": e["plain"], "Category": e["category"]}
        if code != "en":
            row["In your language"] = loc
        rows.append(row)
    st.caption(f"{len(rows)} of {len(g)} terms")
    st.dataframe(rows, hide_index=True, width="stretch")
