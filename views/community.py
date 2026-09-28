import html

import streamlit as st

from modules import ui
from modules.content import load_json
from modules.translate import tr_list

# Sample "Report Twin" matches for the demo (tag based only, no health data is shared).
TWINS = [
    ("Sunflower_22", 92, ["#PCOS", "#Hormones", "#Insulin Resistance"], "#B56BE0,#8A5CD0"),
    ("Mountain_Mom", 85, ["#PCOS", "#Fertility", "#Hashimotos"], "#4AB3D6,#5A8FE0"),
    ("Quiet_Storm", 78, ["#PCOS", "#Hormones"], "#F2A65A,#F0708F"),
]
FILTERS = ["#PCOS", "#Endometriosis", "#Fertility", "#Perimenopause", "#Hashimotos", "#Fibroids"]
AVATARS = ["#B56BE0,#8A5CD0", "#4AB3D6,#5A8FE0", "#F2A65A,#F0708F", "#7A8FE6,#5AA9DC", "#E56FA8,#F0708F", "#45C4B0,#4AA3E0"]

LABELS = ["Verified Peer Community", "Connect with others on similar health journeys.",
          "Find My Report Twin", "Match with users who share similar diagnostic tags", "Hide", "Show matches", "Connect",
          "match", "Matches based on non-sensitive diagnostic tags only. No personal health data is shared.",
          "Share your experience or ask a question...", "Posting as anonymous", "Post", "All", "You", "just now",
          "Request to connect", "Report misinformation", "Filter by tag",
          "Demo preview: these are sample stories written for this demo. Posts you write stay in this session only and are not saved or shared.",
          "Connect request (demo): in the full version, a moderated, consent-based request is sent and no contact details are shared.",
          "Report received (demo): in the full version, a moderator reviews it and removes wrong claims.",
          "No posts with this tag yet. Write the first one above.",
          "How we keep it free of misinformation",
          "In this demo these steps are described, not implemented. The stories below were written and reviewed by the team."]
RULES = [
    "Only people whose diagnosis is confirmed by a lab report or doctor letter can join. A moderator checks the document.",
    "Posts share experiences only. No medicine names, doses or treatment advice.",
    "Every post is reviewed by a moderator before it appears.",
    "Health facts in posts are checked against trusted sources, and wrong claims are removed.",
    "Anyone can report a post. Reports are reviewed quickly.",
    "Identity stays private: alias only, no phone number, address or reports are shown.",
    "A connection needs consent from both people.",
]


def _avatar(grad: str, size: int = 52) -> str:
    return (f'<div class="ah-av" style="width:{size}px;height:{size}px;background:linear-gradient(135deg,{grad})">'
            f'{ui.icon("user", int(size * .55), "#fff")}</div>')


def _tags(tags) -> str:
    return "".join(f'<span class="ah-tag">{html.escape(t)}</span>' for t in tags)


def _twins(L):
    if st.session_state.get("cm_hide_twin"):
        st.button(L["Show matches"], key="cm_show_twin", icon=":material/auto_awesome:",
                  on_click=lambda: st.session_state.update(cm_hide_twin=False))
        return
    with st.container(key="card_twin"):
        h, b = st.columns([6, 1], vertical_alignment="center")
        h.markdown(f'<div class="ah-twin-head"><div class="t">{ui.icon("sparkles", 20, "#fff")}</div>'
                   f'<div><b>{L["Find My Report Twin"]}</b><span>{L["Match with users who share similar diagnostic tags"]}</span></div></div>',
                   unsafe_allow_html=True)
        b.button(L["Hide"], key="cm_hide", width="stretch", on_click=lambda: st.session_state.update(cm_hide_twin=True))
        st.divider()
        for i, (name, pct, tags, grad) in enumerate(TWINS):
            with st.container(key=f"card_match_{i}"):
                m, c = st.columns([6, 1.1], vertical_alignment="center")
                m.markdown(f'<div class="ah-match">{_avatar(grad)}<div><span class="ah-name">{name}</span>'
                           f'<span class="ah-pct">{pct}% {L["match"]}</span><div class="ah-tags">{_tags(tags)}</div></div></div>',
                           unsafe_allow_html=True)
                if c.button(L["Connect"], key=f"cm_twin_{i}", width="stretch"):
                    st.toast(L[LABELS[19]])
        st.markdown(f'<div class="ah-fine">{L[LABELS[8]]}</div>', unsafe_allow_html=True)



def render():
    L = dict(zip(LABELS, tr_list(LABELS)))
    ui.page_header(L["Verified Peer Community"], L["Connect with others on similar health journeys."])
    ui.notice(L[LABELS[18]])
    _twins(L)

    posts = load_json("community")
    tags = FILTERS + sorted({p["tag"] for p in posts} - set(FILTERS))
    s, p = st.columns([0.35, 12], vertical_alignment="center")
    s.markdown(ui.icon("search", 18, "#6B6880"), unsafe_allow_html=True)
    with p:
        pick = st.pills(L["Filter by tag"], [L["All"]] + tags, default=L["All"], key="cm_tag", label_visibility="collapsed")
    active = None if pick in (None, L["All"]) else pick

    with st.container(key="card_compose"):
        text = st.text_area("post", placeholder=L[LABELS[9]], height=80, key="cm_text", label_visibility="collapsed")
        c1, c2 = st.columns([6, 1.1], vertical_alignment="center")
        c1.markdown(f'<div class="ah-fine">{L[LABELS[10]]} · {active or "#General"}</div>', unsafe_allow_html=True)
        if c2.button(L["Post"], key="cm_post", type="primary", icon=":material/send:", width="stretch", disabled=not (text or "").strip()):
            st.session_state.setdefault("cm_mine", []).insert(0, {"alias": L["You"], "tag": active or "#General", "story": text.strip(), "mine": True})
            st.session_state["cm_text"] = ""
            st.rerun()

    mine = [m for m in st.session_state.get("cm_mine", []) if not active or m["tag"] == active]
    shown = [c for c in posts if not active or c["tag"] == active]
    flat = tr_list([x for c in shown for x in (c["title"], c["story"], c["tip"], c["verified_by"])])
    if not (mine or shown):
        st.info(L[LABELS[21]])

    for m in mine:
        with st.container(key=f"card_post_me_{abs(hash(m['story'])) % 10**6}"):
            st.markdown(f'<div class="ah-post">{_avatar(AVATARS[0], 46)}<div><span class="who">{html.escape(m["alias"])}</span>'
                        f'<span class="ago">{L["just now"]}</span><div class="ah-tags">{_tags([m["tag"]])}</div>'
                        f'<p>{html.escape(m["story"])}</p></div></div>', unsafe_allow_html=True)

    for i, c in enumerate(shown):
        title, story, tip, ver = flat[i * 4:(i + 1) * 4]
        head = f"<b>{html.escape(title)}</b><br>" if title else ""
        tip_html = f'<div class="tip">💡 {html.escape(tip)}</div>' if tip else ""
        with st.container(key=f"card_post_{c['id']}"):
            st.markdown(
                f'<div class="ah-post">{_avatar(AVATARS[(i + 1) % len(AVATARS)], 46)}<div>'
                f'<span class="who">{html.escape(c["alias"])}</span><span class="ago">{c["ago"]} ago</span>'
                f'<span class="ah-ver">✓ {html.escape(ver)}</span><div class="ah-tags">{_tags([c["tag"]])}</div>'
                f'<p>{head}{html.escape(story)}</p>{tip_html}'
                f'<div class="meta"><span>{ui.icon("heart", 16)}{c["likes"]}</span><span>{ui.icon("message", 16)}{c["comments"]}</span></div>'
                f'</div></div>', unsafe_allow_html=True)
            b1, b2, _ = st.columns([1.6, 2.1, 5])
            if b1.button(L["Request to connect"], key=f"conn_{c['id']}", type="tertiary", icon=":material/person_add:"):
                st.toast(L[LABELS[19]])
            if b2.button(L["Report misinformation"], key=f"rep_{c['id']}", type="tertiary", icon=":material/flag:"):
                st.toast(L[LABELS[20]])

    with st.expander(L[LABELS[22]]):
        for r in tr_list(RULES):
            st.markdown(f"- {r}")
        st.caption(L[LABELS[23]])
