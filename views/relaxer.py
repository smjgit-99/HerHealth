import streamlit as st

from modules import ui
from modules.languages import can_speak
from modules.mascot import say
from modules.translate import current_code, tr_list
from modules.tts import speak

# name -> list of (phase label, seconds, orb goes: "grow" | "hold-big" | "shrink" | "hold-small")
PATTERNS = {
    "Calm breathing (4 in, 6 out)": [("Breathe in", 4, "grow"), ("Breathe out", 6, "shrink")],
    "Box breathing (4-4-4-4)": [("Breathe in", 4, "grow"), ("Hold", 4, "hold-big"), ("Breathe out", 4, "shrink"), ("Hold", 4, "hold-small")],
    "4-7-8 relaxing breath": [("Breathe in", 4, "grow"), ("Hold", 7, "hold-big"), ("Breathe out", 8, "shrink")],
}
SCALE_LO, SCALE_HI = 0.62, 1.0
SCRIPT = ["Sit comfortably and let your shoulders drop.",
          "Notice your feet on the floor and your breath moving in and out.",
          "Waiting for a report or a visit can feel heavy. It is okay to feel worried.",
          "With each slow breath out, let your jaw and hands soften.",
          "You are not alone. You can write down your questions and take them to your doctor."]
LABELS = ["Guided breathing", "Pick a rhythm", "Follow the circle. Breathe slowly through your nose. Stop if you feel dizzy.",
          "A short calming script", "Read aloud", "Audio service not reachable right now.", "Audio is not available for this language.",
          "Guided breathing and meditation to ease medical anxiety.", "Mindful Relaxer",
          "If your worry feels too big or does not go away, please talk to a doctor or someone you trust."]


def _css(uid: str, phases) -> str:
    total = sum(p[1] for p in phases)
    t, kf, scale = 0.0, [], SCALE_LO
    kf.append(f"0%{{transform:scale({scale})}}")
    label_css = []
    for i, (_, secs, mode) in enumerate(phases):
        start, end = t / total * 100, (t + secs) / total * 100
        if mode == "grow":
            scale = SCALE_HI
        elif mode == "shrink":
            scale = SCALE_LO
        kf.append(f"{end:.2f}%{{transform:scale({scale})}}")
        label_css.append(f"@keyframes {uid}p{i}{{0%,{max(start - .01, 0):.2f}%{{opacity:0}}{start:.2f}%,{end:.2f}%{{opacity:1}}{min(end + .01, 100):.2f}%,100%{{opacity:0}}}}"
                         f".{uid}-p{i}{{animation:{uid}p{i} {total}s linear infinite}}")
        t += secs
    return (f"<style>@keyframes {uid}o{{{','.join(kf)}}}.{uid}-orb{{animation:{uid}o {total}s ease-in-out infinite}}"
            + "".join(label_css) + "</style>")


def render():
    T = tr_list(LABELS + list(PATTERNS) + SCRIPT + [p[0] for v in PATTERNS.values() for p in v])
    L = dict(zip(LABELS, T[:len(LABELS)]))
    names = T[len(LABELS):len(LABELS) + len(PATTERNS)]
    script = T[len(LABELS) + len(PATTERNS):len(LABELS) + len(PATTERNS) + len(SCRIPT)]
    phase_tr = dict(zip([p[0] for v in PATTERNS.values() for p in v], T[len(LABELS) + len(PATTERNS) + len(SCRIPT):]))

    ui.page_header(L["Mindful Relaxer"], L["Guided breathing and meditation to ease medical anxiety."])
    choice = st.selectbox(L["Pick a rhythm"], list(range(len(PATTERNS))), format_func=lambda i: names[i], key="relax_pattern")  # noqa
    key = list(PATTERNS)[choice]
    phases = PATTERNS[key]

    uid = f"br{choice}"
    labels = "".join(f'<span class="ah-phase {uid}-p{i}">{phase_tr[p[0]]}</span>' for i, p in enumerate(phases))
    with st.container(border=True, key="card_orb"):
        st.markdown(_css(uid, phases) +
                    f'<div class="ah-breath"><div class="ah-orb-wrap"><div class="ah-orb-ring"></div>'
                    f'<div class="ah-orb {uid}-orb"></div>{labels}</div></div>', unsafe_allow_html=True)
        st.caption(L["Follow the circle. Breathe slowly through your nose. Stop if you feel dizzy."])

    st.subheader(L["A short calming script"])
    say("\n\n".join(script))
    code = current_code()
    if can_speak(code):
        if st.button(f"🔊 {L['Read aloud']}", key="relax_listen"):
            audio = speak(" ".join(script), code)
            if audio:
                st.audio(audio, format="audio/mp3")
            else:
                st.warning(L["Audio service not reachable right now."])
    else:
        st.caption(L["Audio is not available for this language."])
    st.info(L["If your worry feels too big or does not go away, please talk to a doctor or someone you trust."])
