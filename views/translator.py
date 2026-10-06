import streamlit as st

from modules import ui
from views import checklist
from modules.analyzer import analyze
from modules.content import load_text
from modules.highlight import highlight_html
from modules.ingest import ALLOWED, read_upload
from modules.languages import can_speak
from modules.translate import current_code, tr_list
from modules.tts import speak

CSS = """<style>
.report-box{white-space:pre-wrap;max-height:520px;overflow:auto;padding:12px 14px;line-height:1.55;
 font-size:.92rem;border:1px solid rgba(128,128,128,.35);border-radius:8px}
.report-box mark{background:#ffe08a;color:#3a2a00;padding:0 3px;border-radius:3px;cursor:help}
</style>"""

LABELS = ["What This Means", "What Is Normal", "Things to Watch", "Jargon found in your report",
          "Test", "Your value", "Usual range", "Status", "What it may mean", "Read aloud",
          "Download summary", "Original report", "Plain-language explanation",
          "No known lab values were found in this text.",
          "Ranges are general adult values. If your report prints a different range, follow the one on your report.",
          "This is a simple explanation, not a diagnosis. Please discuss your report with a doctor."]
STATUS = ["Low", "Normal", "High", "Check unit"]


def _run(text, how):
    with st.spinner("Reading and analyzing..."):
        st.session_state.report_text = text
        st.session_state.read_how = how
        st.session_state.analysis = analyze(text)


def _summary(a, means, watch, qs, title):
    out = [title, "Educational only, not medical advice.", "", "WHAT THIS MEANS"]
    out += [f"- {m}" for m in means]
    out += ["", "WHAT IS NORMAL"]
    out += [f"- {r['test']}: {r['value']:g} {r['unit']} (usual {r['range']}) - {r['status']}" for r in a["rows"]] or ["- (no lab values found)"]
    out += ["", "THINGS TO WATCH"] + [f"- {w}" for w in watch]
    out += ["", "QUESTIONS FOR MY DOCTOR"] + [f"- {q}" for q in qs]
    return "\n".join(out)


def _show():
    a, text, code = st.session_state.analysis, st.session_state.report_text, current_code()
    rows, terms = a["rows"], a["terms"]

    pub = tr_list(LABELS + STATUS + [r["meaning"] for r in rows] + [t["plain"] for t in terms])
    L = dict(zip(LABELS, pub[:len(LABELS)]))
    S = dict(zip(STATUS, pub[len(LABELS):len(LABELS) + len(STATUS)]))
    rest = pub[len(LABELS) + len(STATUS):]
    meanings, plains = rest[:len(rows)], rest[len(rows):]
    prv = tr_list(a["means"] + a["watch"] + a["questions"], private=True)
    means = prv[:len(a["means"])]
    watch = prv[len(a["means"]):len(a["means"]) + len(a["watch"])]
    qs = prv[len(a["means"]) + len(a["watch"]):]

    def lab(k):
        return k if code == "en" else f"{L[k]} ({k})"

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader(L["Original report"])
        st.caption(f"{st.session_state.read_how}. Highlighted words are medical jargon. Hover to see the meaning.")
        st.markdown(f'<div class="report-box">{highlight_html(text)}</div>', unsafe_allow_html=True)
        with st.expander(f"{L['Jargon found in your report']} ({len(terms)})"):
            for t, p in zip(terms, plains):
                st.markdown(f"**{t['found_as']}**: {p}")

    with right:
        st.subheader(L["Plain-language explanation"])
        st.caption(f"Mode: {a['mode']}")
        t1, t2, t3 = st.tabs([lab("What This Means"), lab("What Is Normal"), lab("Things to Watch")])
        with t1:
            for m in means:
                st.markdown(f"- {m}")
            if can_speak(code):
                if st.button(f"🔊 {L['Read aloud']}", key="btn_listen"):
                    audio = speak(" ".join(means), code)
                    if audio:
                        st.audio(audio, format="audio/mp3")
                    else:
                        st.warning("Audio service not reachable right now.")
            else:
                st.caption("Audio is not available for this language.")
        with t2:
            if rows:
                st.dataframe(
                    [{L["Test"]: r["test"], L["Your value"]: f"{r['value']:g} {r['unit']}", L["Usual range"]: r["range"],
                      L["Status"]: S[r["status"]], L["What it may mean"]: mm} for r, mm in zip(rows, meanings)],
                    hide_index=True, width="stretch")
                st.caption(L["Ranges are general adult values. If your report prints a different range, follow the one on your report."])
            else:
                st.info(L["No known lab values were found in this text."])
        with t3:
            for w in watch:
                st.markdown(f"- {w}")
        st.caption(L["This is a simple explanation, not a diagnosis. Please discuss your report with a doctor."])

    english = _summary(a, a["means"], a["watch"], a["questions"], "WOMEN'S HEALTH REPORT SUMMARY")
    doc = english if code == "en" else english + "\n\n===== TRANSLATION =====\n\n" + _summary(a, means, watch, qs, "SUMMARY")
    st.download_button(f"⬇️ {L['Download summary']}", doc, file_name="report_summary.txt", key="dl_summary")


def render():
    st.markdown(CSS, unsafe_allow_html=True)
    ui.page_header(*tr_list(["Report Translator", "Upload or paste a report. Left: your report with jargon highlighted. Right: a plain-language explanation in your language."]))
    c1, c2 = st.columns([3, 1])
    with c1:
        up = st.file_uploader("Upload a report (PDF, image, Word or text)", type=ALLOWED, key="report_upload")
        pasted = st.text_area("...or paste the report text", height=130, key="report_paste")
    with c2:
        st.write("")
        go = st.button("Analyze report", type="primary", width="stretch", key="btn_analyze")
        sample = st.button("Try sample report", width="stretch", key="btn_sample")
        st.caption("Files are read in memory and are not saved.")

    if sample:
        _run(load_text("sample_report.txt"), "Sample report (fictional)")
    elif go:
        try:
            text, how = (read_upload(up) if up else (pasted, "Pasted text"))
            if len(text.strip()) < 20:
                st.error("Not enough text found. Try pasting the text, or upload a clearer file.")
            else:
                _run(text, how)
        except Exception as e:
            st.error(f"Could not read this input: {e}")

    if "analysis" in st.session_state:
        _show()

    checklist.render()

# --- Translator -> Community CTA Cards ---
    st.write("")
    st.markdown("---")
    cta_h, c1t, c1b, c1btn, c2t, c2b, c2btn = tr_list([
        "Take the Next Step in Your Health Journey",
        "Join the HerHealth Community",
        "Have questions about your lab results or looking for peer support? Connect with other women using an alias or anonymously.",
        "Join Community Now",
        "Learn More About Your Results",
        "Browse plain-language guides to common women's health conditions, plus a glossary of medical terms.",
        "Explore the Health Library",
    ])
    st.markdown(f"### 🌸 {cta_h}")

    col_cta1, col_cta2 = st.columns(2, gap="medium")

    with col_cta1:
        with st.container(key="card_cta_community"):
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #F5EEFB, #FCEFF6); padding: 20px; border-radius: 12px; border: 1px solid #EFEAF8;">
                    <h4 style="color: #1D1B2A; margin-top: 0;">{c1t}</h4>
                    <p style="color: #6B6880; font-size: 0.9rem;">{c1b}</p>
                </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button(c1btn, type="primary", use_container_width=True, key="btn_cta_join_comm"):
                st.session_state.nav_page = "Community"
                st.rerun()

    with col_cta2:
        with st.container(key="card_cta_signin"):
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #EEF4FD, #F1F8FD); padding: 20px; border-radius: 12px; border: 1px solid #D1E3F8;">
                    <h4 style="color: #1D1B2A; margin-top: 0;">{c2t}</h4>
                    <p style="color: #6B6880; font-size: 0.9rem;">{c2b}</p>
                </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button(c2btn, use_container_width=True, key="btn_cta_learn"):
                st.session_state.nav_page = "Learn"
                st.rerun()