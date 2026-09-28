import streamlit as st

from modules import ui
from modules.content import load_json
from modules.translate import current_code, tr_list

LABELS = ["Questions to ask your doctor", "Bring with you", "Download checklist",
          "Tick each question as you ask it. Add your own below."]


def render():
    ui.page_header(*tr_list(["Doctor Visit Checklist", "Questions to take to your appointment, based on your report and symptoms."]))
    cl = load_json("checklist")
    a = st.session_state.get("analysis")
    if a:
        st.success("Questions from your analyzed report are included below.")
    else:
        st.info("Tip: analyze a report first to get report-specific questions, or pick topics and symptoms here.")

    c1, c2 = st.columns(2)
    topics = c1.multiselect("Health topics", list(cl["by_topic"]), key="cl_topics")
    symptoms = c2.multiselect("Symptoms you have", list(cl["by_symptom"]), key="cl_symptoms")
    extra = st.text_area("Add your own questions (one per line)", key="cl_extra", height=80)

    qs = list(a["questions"]) if a else []
    for t in topics:
        qs += cl["by_topic"][t]["questions"]
    qs += [cl["by_symptom"][s] for s in symptoms]
    qs += cl["general"]
    qs += [x.strip() for x in extra.splitlines() if x.strip()]
    qs = list(dict.fromkeys(qs))

    code = current_code()
    tq = tr_list(qs, private=True)
    tb = tr_list(cl["bring"])
    L = dict(zip(LABELS, tr_list(LABELS)))

    st.subheader(L["Questions to ask your doctor"])
    st.caption(L["Tick each question as you ask it. Add your own below."])
    for i, q in enumerate(tq):
        st.checkbox(q, key=f"cq_{abs(hash(qs[i])) % 10**9}")
    st.subheader(L["Bring with you"])
    for b in tb:
        st.markdown(f"- {b}")

    def block(qq, bb):
        return "\n".join(["DOCTOR VISIT CHECKLIST", "", "QUESTIONS TO ASK"] + [f"[ ] {q}" for q in qq] + ["", "BRING WITH YOU"] + [f"- {b}" for b in bb])
    english = block(qs, cl["bring"])
    doc = english if code == "en" else english + "\n\n===== TRANSLATION =====\n\n" + block(tq, tb)
    st.download_button(f"⬇️ {L['Download checklist']}", doc, file_name="doctor_visit_checklist.txt", key="dl_checklist")
