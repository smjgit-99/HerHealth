import html
import time

import streamlit as st

from modules import auth, db, ui
from modules.content import load_json
from modules.translate import tr, tr_list

# Community Rules definition
RULES = [
    "Be respectful and supportive to fellow community members.",
    "Do not share explicit personal health identifying details.",
    "Moderators review posts to maintain a safe and welcoming space."
]

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
          "Share your experience or ask a question...", "Posting as", "Post", "All", "You", "just now",
          "Request to connect", "Report misinformation", "Filter by tag",
          "Sample stories below were written for this demo. Posts from verified members appear above them after a moderator approves them.",
          "Connect request (demo match): real requests go to verified members from their posts.",
          "Report received. A moderator will review it.",
          "No posts with this tag yet.",
          "How we keep it free of misinformation",
          "Moderators check every proof document and every post before it is shown.",
          "Feeling anxious or overwhelmed? Take a one-minute breathing break."]
N = ["Sign in", "Create account", "Email", "Password", "Alias (not your real name)", "Sign out", "Sign in to post, connect or report.",
     "Password must be at least 8 characters. Your email is never shown to others.",
     "Get verified to post", "Condition tag", "Upload a lab report or doctor letter (PDF, PNG or JPG)",
     "Submit for verification", "Sent. A moderator will check it. The document is deleted right after the decision.",
     "Your verification is waiting for a moderator.", "Your verification was not accepted. You can upload a different document.",
     "You are a verified member.", "Your post was sent to a moderator and will appear once approved.", "Waiting for approval",
     "Approved", "Connection requests", "Accept", "Decline", "Your connections", "Request sent.",
     "Already requested or connected.", "Only verified members can post or connect.", "Already reported. Thank you.",
     "Moderation", "Verification requests", "Approve", "Reject", "Posts waiting for approval", "Reported posts",
     "Remove post", "Keep post", "Nothing waiting.", "Download document", "Verified member", "Sample story"]


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


def _account(L, T, user):
    """Signed-in member panel. Renders nothing if the user is logged out."""
    if user is None:
        return

    with st.container(key="card_account"):
        a, b = st.columns([6, 1.3], vertical_alignment="center")
        a.markdown(f'**{html.escape(user["alias"])}**' + (f' · ✓ {T["You are a verified member."]}' if user["status"] == "verified" else ""))
        if b.button(T["Sign out"], key="so", width="stretch"):
            st.session_state.pop("user_id", None)
            st.rerun()

        if user["status"] in ("unverified", "rejected"):
            if user["status"] == "rejected":
                st.warning(T["Your verification was not accepted. You can upload a different document."])
            st.markdown(f'**{T["Get verified to post"]}**')
            tag = st.selectbox(T["Condition tag"], FILTERS, key="v_tag")
            up = st.file_uploader(T["Upload a lab report or doctor letter (PDF, PNG or JPG)"], type=["pdf", "png", "jpg", "jpeg"], key="v_file")
            if st.button(T["Submit for verification"], key="v_go", disabled=up is None):
                err = auth.submit_verification(user["id"], tag, up.name, up.getvalue())
                if err:
                    st.error(tr(err))
                else:
                    st.success(T["Sent. A moderator will check it. The document is deleted right after the decision."])
                    st.rerun()
        elif user["status"] == "pending":
            st.info(T["Your verification is waiting for a moderator."])

        reqs = db.incoming_requests(user["id"])
        if reqs:
            st.markdown(f'**{T["Connection requests"]}**')
            for r in reqs:
                c1, c2, c3 = st.columns([4, 1.2, 1.2], vertical_alignment="center")
                c1.write(r["alias"])
                if c2.button(T["Accept"], key=f"acc_{r['id']}"):
                    db.answer_request(r["id"], user["id"], True)
                    st.rerun()
                if c3.button(T["Decline"], key=f"dec_{r['id']}"):
                    db.answer_request(r["id"], user["id"], False)
                    st.rerun()
        friends = db.connections_of(user["id"])
        if friends:
            st.caption(f'{T["Your connections"]}: ' + ", ".join(f["alias"] for f in friends))


def _moderation(T):
    with st.expander(T["Moderation"], icon=":material/shield:"):
        st.markdown(f'**{T["Verification requests"]}**')
        v = auth.pending_verifications()
        for r in v:
            c1, c2, c3, c4 = st.columns([3, 2.5, 1.2, 1.2], vertical_alignment="center")
            c1.write(f'{r["alias"]} · {r["tag"]}')
            c2.download_button(T["Download document"], r["doc_blob"], file_name=r["doc_name"], key=f"dl_{r['id']}")
            if c3.button(T["Approve"], key=f"va_{r['id']}"):
                auth.decide_verification(r["id"], True)
                st.rerun()
            if c4.button(T["Reject"], key=f"vr_{r['id']}"):
                auth.decide_verification(r["id"], False)
                st.rerun()
        if not v:
            st.caption(T["Nothing waiting."])

        st.markdown(f'**{T["Posts waiting for approval"]}**')
        pp = db.pending_posts()
        for p in pp:
            st.write(f'{p["alias"]} · {p["tag"]}')
            st.info(p["story"])
            c1, c2, _ = st.columns([1.2, 1.2, 5])
            if c1.button(T["Approve"], key=f"pa_{p['id']}"):
                db.set_post_status(p["id"], "approved")
                st.rerun()
            if c2.button(T["Reject"], key=f"pr_{p['id']}"):
                db.set_post_status(p["id"], "removed")
                st.rerun()
        if not pp:
            st.caption(T["Nothing waiting."])

        st.markdown(f'**{T["Reported posts"]}**')
        rp = db.open_reports()
        for p in rp:
            st.write(f'{p["alias"]} · {p["tag"]}')
            st.warning(p["story"])
            c1, c2, _ = st.columns([1.5, 1.5, 4])
            if c1.button(T["Remove post"], key=f"rm_{p['rid']}"):
                db.set_post_status(p["pid"], "removed")
                db.close_reports(p["pid"])
                st.rerun()
            if c2.button(T["Keep post"], key=f"kp_{p['rid']}"):
                db.close_reports(p["pid"])
                st.rerun()
        if not rp:
            st.caption(T["Nothing waiting."])


def _ago(ts: float) -> str:
    s = max(0, time.time() - ts)
    return "just now" if s < 3600 else f"{int(s // 3600)}h" if s < 86400 else f"{int(s // 86400)}d"


def render():
    db.init()
    L = dict(zip(LABELS, tr_list(LABELS)))
    T = dict(zip(N, tr_list(N)))
    user = auth.get_user(st.session_state.get("user_id"))
    if user is None:
        st.session_state.pop("user_id", None)
        
    ui.page_header(L["Verified Peer Community"], L["Connect with others on similar health journeys."])
    
    # Aesthetic & Calm Relaxer Card linked to the new standalone Relax page
    with st.container(border=True):
        col1, col2 = st.columns([5, 1.5], vertical_alignment="center")
        col1.markdown(
            "🌿 **Take a Moment for Yourself**\n\n"
            "*Feeling anxious or overwhelmed? Take a one-minute breathing break to center your mind.*"
        )
        if col2.button("✨ Breathe", key="goto_relax_page", type="primary", use_container_width=True):
            st.session_state["nav_page"] = "Relax"
            st.rerun()

    _account(L, T, user)
    
    if user is not None and user["role"] == "admin":
        _moderation(T)
    _twins(L)

    sample = load_json("community")
    real = db.approved_posts()
    tags = FILTERS + sorted(({p["tag"] for p in sample} | {p["tag"] for p in real}) - set(FILTERS))
    s, p = st.columns([0.35, 12], vertical_alignment="center")
    s.markdown(ui.icon("search", 18, "#6B6880"), unsafe_allow_html=True)
    with p:
        pick = st.pills(L["Filter by tag"], [L["All"]] + tags, default=L["All"], key="cm_tag", label_visibility="collapsed")
    active = None if pick in (None, L["All"]) else pick

    if user is not None and user["status"] == "verified":
        with st.container(key="card_compose"):
            text = st.text_area("post", placeholder=L[LABELS[9]], height=80, key="cm_text", label_visibility="collapsed", max_chars=2000)
            c1, c2 = st.columns([6, 1.1], vertical_alignment="center")
            c1.markdown(f'<div class="ah-fine">{L[LABELS[10]]} {html.escape(user["alias"])} · {active or user["tag"] or "#General"}</div>', unsafe_allow_html=True)
            if c2.button(L["Post"], key="cm_post", type="primary", icon=":material/send:", width="stretch", disabled=not (text or "").strip()):
                db.add_post(user["id"], active or user["tag"] or "#General", text)
                st.session_state["cm_sent"] = True
                st.session_state["cm_text"] = ""
                st.rerun()
        if st.session_state.pop("cm_sent", False):
            st.success(T["Your post was sent to a moderator and will appear once approved."])
        waiting = [m for m in db.my_posts(user["id"]) if m["status"] == "pending"]
        for m in waiting:
            st.caption(f'⏳ {T["Waiting for approval"]}: {m["story"][:80]}')

    shown_real = [c for c in real if not active or c["tag"] == active]
    shown = [c for c in sample if not active or c["tag"] == active]
    flat = tr_list([x for c in shown for x in (c["title"], c["story"], c["tip"], c["verified_by"])])
    real_tr = tr_list([c["story"] for c in shown_real])
    if not (shown_real or shown):
        st.info(L[LABELS[21]])

    for i, c in enumerate(shown_real):
        with st.container(key=f"card_post_db_{c['id']}"):
            st.markdown(
                f'<div class="ah-post">{_avatar(AVATARS[c["user_id"] % len(AVATARS)], 46)}<div>'
                f'<span class="who">{html.escape(c["alias"])}</span><span class="ago">{_ago(c["created"])}</span>'
                f'<span class="ah-ver">✓ {T["Verified member"]}</span><div class="ah-tags">{_tags([c["tag"]])}</div>'
                f'<p>{html.escape(real_tr[i])}</p></div></div>', unsafe_allow_html=True)
            b1, b2, _ = st.columns([1.6, 2.1, 5])
            if b1.button(L["Request to connect"], key=f"conn_db_{c['id']}", type="tertiary", icon=":material/person_add:"):
                if user is None or user["status"] != "verified":
                    st.toast(T["Only verified members can post or connect."])
                elif db.request_connection(user["id"], c["user_id"]):
                    st.toast(T["Request sent."])
                else:
                    st.toast(T["Already requested or connected."])
            if b2.button(L["Report misinformation"], key=f"rep_db_{c['id']}", type="tertiary", icon=":material/flag:"):
                if user is None:
                    st.toast(T["Sign in to post, connect or report."])
                else:
                    st.toast(L[LABELS[20]] if db.add_report(c["id"], user["id"]) else T["Already reported. Thank you."])

    for i, c in enumerate(shown):
        title, story, tip, ver = flat[i * 4:(i + 1) * 4]
        head = f"<b>{html.escape(title)}</b><br>" if title else ""
        tip_html = f'<div class="tip">💡 {html.escape(tip)}</div>' if tip else ""
        with st.container(key=f"card_post_{c['id']}"):
            st.markdown(
                f'<div class="ah-post">{_avatar(AVATARS[(i + 1) % len(AVATARS)], 46)}<div>'
                f'<span class="who">{html.escape(c["alias"])}</span><span class="ago">{c["ago"]} ago</span>'
                f'<span class="ah-ver">✓ {html.escape(ver)}</span><span class="ah-tag">{T["Sample story"]}</span>'
                f'<div class="ah-tags">{_tags([c["tag"]])}</div>'
                f'<p>{head}{html.escape(story)}</p>{tip_html}'
                f'<div class="meta"><span>{ui.icon("heart", 16)}{c["likes"]}</span><span>{ui.icon("message", 16)}{c["comments"]}</span></div>'
                f'</div></div>', unsafe_allow_html=True)

    with st.expander(L[LABELS[22]]):
        for r in tr_list(RULES):
            st.markdown(f"- {r}")
        st.caption(L[LABELS[23]])