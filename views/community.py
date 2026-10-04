"""Community: first-visit onboarding, For You / condition pages, posts, reactions, comments, reports.

All data lives in modules/db.py, logic helpers in modules/community.py, static text in data/conditions.json.
Every UI string goes through _() so Hindi/Marathi work like the rest of the app.
"""
import html
import re
import sqlite3
import zlib
from pathlib import Path

import streamlit as st

from modules import community as cm
from modules import db, ui
from modules.translate import tr, tr_list

PAGE_SIZE = 10
VIEWS = ["foryou", "mine", "add"]
AVATARS = ["#B56BE0,#8A5CD0", "#4AB3D6,#5A8FE0", "#F2A65A,#F0708F", "#7A8FE6,#5AA9DC", "#E56FA8,#F0708F", "#45C4B0,#4AA3E0"]


def _(text: str) -> str:
    return tr(text)


# Warm the translation cache with one batched call per render: every _("...") literal in this file,
# plus the shared texts from modules/community.py and data/conditions.json.
_SOURCE = Path(__file__).read_text(encoding="utf-8")
_STATIC = sorted(set(re.findall(r'\b_\("([^"\n]+)"\)', _SOURCE)) | set(cm.RULES) | set(cm.POST_TYPES)
                 | set(cm.REPORT_REASONS) | {r[1] for r in cm.REACTIONS} | {cm.DISCLAIMER, cm.MED_WARNING}
                 | {x for c in cm.CONDITIONS for x in (c["name"], c["description"], c["fact"])})

_CSS = """<style>
.ah-ph{display:flex;gap:12px;align-items:center;}
.ah-ph .who{font-weight:700;font-size:1.02rem;}
.ah-ph .ago{color:var(--mute);font-size:.82rem;margin-left:8px;}
.ah-body{margin:10px 0 8px;color:#2e2b3d;line-height:1.55;word-break:break-word;}
.ah-cmt{margin:2px 0 0;color:#2e2b3d;line-height:1.5;word-break:break-word;}
.ah-cmt .ago{color:var(--mute);font-size:.8rem;margin-left:6px;}
.ah-cmt p{margin:2px 0 0;}
[class*="st-key-cmt_r_"]{margin-left:14px;padding-left:12px;border-left:2px solid var(--line);}
[class*="st-key-cmt_t_"]{padding:6px 0;border-bottom:1px solid var(--line);}
[class*="st-key-card_post"] .stButton > button,[class*="st-key-cmt_"] .stButton > button{font-size:.85rem;padding:.3rem .7rem;}
.ah-dyk{display:flex;gap:10px;align-items:flex-start;font-size:.92rem;color:#4a4560;}
.ah-dyk b{color:var(--pd);}
</style>"""


# ---- small UI helpers ---------------------------------------------------------
def _avatar(seed: str, size: int = 44, anon: bool = False) -> str:
    grad = "#B9B5C8,#9A96AE" if anon else AVATARS[zlib.crc32(seed.encode()) % len(AVATARS)]
    return (f'<div class="ah-av" style="width:{size}px;height:{size}px;background:linear-gradient(135deg,{grad})">'
            f'{ui.icon("user", int(size * .55), "#fff")}</div>')


def _tags(tags) -> str:
    return "".join(f'<span class="ah-tag">{html.escape(t)}</span>' for t in tags)


def _cond_label(cid: str) -> str:
    c = cm.BY_ID[cid]
    return f'{c["icon"]} {_(c["name"])}'


def _text_html(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def _flash(msg: str):
    st.session_state["cm_flash"] = msg


def _members_text(n: int) -> str:
    return f"{n} {_('member') if n == 1 else _('members')}"


def _db_error(retry_key: str):
    st.error(_("We could not load this right now. Please try again."), icon=":material/error:")
    st.button(_("Try again"), key=retry_key, icon=":material/refresh:")


# ---- callbacks (run before the next rerun, so the page shows fresh data) -------
def _toggle_reaction(post_id, uid, kind):
    try:
        db.toggle_reaction(post_id, uid, kind)
    except sqlite3.Error:
        _flash(_("Could not save your reaction. Please try again."))


def _toggle_helpful(comment_id, uid):
    try:
        db.toggle_comment_helpful(comment_id, uid)
    except sqlite3.Error:
        _flash(_("Could not save. Please try again."))


def _toggle_comments(post_id):
    st.session_state["cm_open"] = None if st.session_state.get("cm_open") == post_id else post_id
    st.session_state.pop("cm_reply", None)


def _start_reply(comment_id):
    st.session_state["cm_reply"] = comment_id


def _cancel_reply():
    st.session_state.pop("cm_reply", None)


def _delete_comment(comment_id, uid):
    try:
        if db.delete_comment(comment_id, uid):
            _flash(_("Comment deleted."))
    except sqlite3.Error:
        _flash(_("Could not delete. Please try again."))


def _open_condition(cid):
    st.session_state["cm_cond"] = cid


def _close_condition():
    st.session_state["cm_cond"] = None


def _join(uid, cid):
    try:
        db.join_condition(uid, cid)
        _flash(_("You joined this community."))
    except sqlite3.Error:
        _flash(_("Could not join. Please try again."))


def _leave(uid, cid):
    try:
        if db.leave_condition(uid, cid):
            _flash(_("You left this community."))
        else:
            _flash(_("Keep at least one condition. Add another first."))
    except sqlite3.Error:
        _flash(_("Could not leave. Please try again."))


def _more(key, step):
    st.session_state[key] = st.session_state.get(key, PAGE_SIZE) + step


# ---- condition picker (onboarding and the "+" tab) --------------------------------
def _picker(prefix: str, current: dict) -> dict:
    """Pick one or more conditions and, for each, Community or Personal. Returns {id: visibility}."""
    ids = [c["id"] for c in cm.CONDITIONS]
    chosen = st.pills(_("Conditions"), ids, selection_mode="multi", default=[c for c in current if c in cm.BY_ID],
                      format_func=_cond_label, key=f"{prefix}_sel", label_visibility="collapsed") or []
    result = {}
    if chosen:
        st.caption(_("Community: shown in Community. Personal: visible only to you."))
    for cid in chosen:
        was = current.get(cid, "community")
        result[cid] = st.radio(_cond_label(cid), ["community", "personal"], index=0 if was == "community" else 1,
                               format_func=lambda v: _("Community") if v == "community" else _("Personal"),
                               horizontal=True, key=f"{prefix}_vis_{cid}")
    fact = cm.BY_ID[chosen[0]]["fact"] if chosen else \
        "Writing down your symptoms and dates before a visit helps your doctor understand what you are going through."
    with st.container(key=f"card_dyk_{prefix}"):
        st.markdown(f'<div class="ah-dyk">{ui.icon("sparkles", 20, ui.PRIMARY_DARK)}<div><b>{_("Did you know?")}</b><br>{html.escape(_(fact))}</div></div>',
                    unsafe_allow_html=True)
    ui.notice(_("Privacy: only your alias is ever shown, never your email. Personal conditions stay private to you. You can change this any time."))
    return result


def _onboarding(uid: int):
    @st.dialog(_("What conditions are you interested in?"), width="large", dismissible=False)
    def dlg():
        st.caption(_("Select at least one. You control what others can see."))
        choices = _picker("ob", {})
        if not choices:
            st.caption(_("Choose at least one condition to continue."))
        if st.button(_("Continue"), type="primary", disabled=not choices, key="ob_go", width="stretch"):
            try:
                err = db.save_conditions(uid, choices)
            except sqlite3.Error:
                err = "Could not save your choices. Please try again."
            if err:
                st.error(_(err))
            else:
                _flash(_("Welcome! Your choices are saved."))
                st.rerun()
    dlg()


# ---- dialogs: compose / edit / delete / report ------------------------------------------
def _composer(uid: int, conds: dict, default_cond):
    @st.dialog(_("Share something..."), width="large")
    def dlg():
        accepted = db.rules_accepted(uid)
        order = list(conds) + [c["id"] for c in cm.CONDITIONS if c["id"] not in conds]
        idx = order.index(default_cond) if default_cond in order else None
        with st.form("cm_compose", border=False):
            cond = st.selectbox(_("Condition"), order, index=idx, placeholder=_("Choose a condition"),
                                format_func=_cond_label, key="cm_c_cond")
            text = st.text_area(_("What would you like to share?"), max_chars=cm.MAX_POST, height=150, key="cm_c_text",
                                placeholder=_("Share your experience or ask a question..."))
            ptype = st.pills(_("Tag (optional)"), cm.POST_TYPES, format_func=_, key="cm_c_type")
            photo = st.file_uploader(_("Add a photo (optional)"), type=["png", "jpg", "jpeg"], key="cm_c_img")
            anon = st.toggle(_("Post anonymously"), key="cm_c_anon", help=_("Your alias is hidden on this post."))
            agree = True
            if not accepted:
                with st.expander(_("Community Rules")):
                    for r in cm.RULES:
                        st.markdown(f"- {_(r)}")
                agree = st.checkbox(_("I have read and accept the Community Rules"), key="cm_c_rules")
            st.caption(_(cm.DISCLAIMER))
            go = st.form_submit_button(_("Post"), type="primary", icon=":material/send:", width="stretch")
        if not go:
            return
        body = (text or "").strip()
        image, img_err = (cm.process_image(photo) if photo is not None else (None, None))
        if cond is None:
            st.error(_("Please choose a condition."))
        elif not body:
            st.error(_("Write something to share."))
        elif not agree:
            st.error(_("Please accept the Community Rules to post."))
        elif img_err:
            st.error(_(img_err))
        else:
            try:
                with st.spinner(_("Posting...")):
                    db.create_post(uid, cond, body, ptype, bool(anon), image)
                    if not accepted:
                        db.accept_rules(uid)
            except sqlite3.Error:
                st.error(_("Could not save your post. Please try again."))
                return
            _flash(_("Posted.") + (" " + _(cm.MED_WARNING) if cm.looks_like_medicine(body) else ""))
            st.rerun()
    dlg()


def _edit_dialog(p, uid: int):
    @st.dialog(_("Edit post"), width="large")
    def dlg():
        with st.form(f"cm_edit_{p['id']}", border=False):
            text = st.text_area(_("Your post"), value=p["story"], max_chars=cm.MAX_POST, height=150, key=f"cm_e_text_{p['id']}")
            ptype = st.pills(_("Tag (optional)"), cm.POST_TYPES, format_func=_, key=f"cm_e_type_{p['id']}",
                             default=p["post_type"] if p["post_type"] in cm.POST_TYPES else None)
            anon = st.toggle(_("Post anonymously"), value=bool(p["anonymous"]), key=f"cm_e_anon_{p['id']}")
            go = st.form_submit_button(_("Save changes"), type="primary", width="stretch")
        if go:
            if not (text or "").strip():
                st.error(_("A post cannot be empty."))
                return
            try:
                ok = db.update_post(p["id"], uid, text, ptype, bool(anon))
            except sqlite3.Error:
                ok = False
            if ok:
                _flash(_("Post updated."))
                st.rerun()
            st.error(_("Could not update this post."))
    dlg()


def _delete_dialog(post_id: int, uid: int):
    @st.dialog(_("Delete this post?"))
    def dlg():
        st.write(_("This removes your post for everyone. It cannot be undone."))
        a, b = st.columns(2)
        if a.button(_("Delete"), type="primary", key=f"cm_del_go_{post_id}", width="stretch"):
            try:
                ok = db.delete_post(post_id, uid)
            except sqlite3.Error:
                ok = False
            _flash(_("Post deleted.") if ok else _("Could not delete this post."))
            st.rerun()
        if b.button(_("Cancel"), key=f"cm_del_no_{post_id}", width="stretch"):
            st.rerun()
    dlg()


def _report_dialog(kind: str, target_id: int, uid: int):
    @st.dialog(_("Report post") if kind == "post" else _("Report comment"))
    def dlg():
        reason = st.radio(_("What is the problem?"), cm.REPORT_REASONS, format_func=_, key=f"cm_rep_r_{kind}_{target_id}")
        if st.button(_("Send report"), type="primary", key=f"cm_rep_go_{kind}_{target_id}", width="stretch"):
            try:
                new = db.add_content_report(kind, target_id, uid, reason)
            except sqlite3.Error:
                st.error(_("Could not send your report. Please try again."))
                return
            _flash(_("Report received. Thank you for helping keep this space safe.") if new else _("You already reported this."))
            st.rerun()
    dlg()


# ---- comments ------------------------------------------------------------------
def _comment_form(uid: int, post_id: int, parent_id, key: str):
    with st.form(key, clear_on_submit=True, border=False):
        txt = st.text_area(_("Write a reply...") if parent_id else _("Write a comment..."), max_chars=cm.MAX_COMMENT,
                           height=80, key=f"{key}_t", label_visibility="collapsed",
                           placeholder=_("Write a reply...") if parent_id else _("Write a comment..."))
        go = st.form_submit_button(_("Reply") if parent_id else _("Comment"), type="primary", icon=":material/send:")
    if parent_id:
        st.button(_("Cancel"), key=f"{key}_cancel", type="tertiary", on_click=_cancel_reply)
    if go:
        if not (txt or "").strip():
            st.warning(_("Write something first."))
            return
        try:
            ok = db.add_comment(post_id, uid, txt, parent_id)
        except sqlite3.Error:
            ok = None
        if ok:
            st.session_state.pop("cm_reply", None)
            st.rerun()
        st.error(_("Could not add your comment. Please try again."))


def _comment(uid: int, post_id: int, c, reply: bool):
    with st.container(key=f"cmt_{'r' if reply else 't'}_{c['id']}"):
        if c["status"] != "visible":
            st.caption(_("This comment was deleted."))
        else:
            who = html.escape(c["alias"]) if c["alias"] else _("Anonymous")
            if c["mine"]:
                who += f' ({_("you")})'
            st.markdown(f'<div class="ah-cmt"><b>{who}</b><span class="ago">{cm.ago(c["created"])}</span>'
                        f'<p>{_text_html(c["body"])}</p></div>', unsafe_allow_html=True)
            if cm.looks_like_medicine(c["body"]):
                st.caption(f":material/medication: {_(cm.MED_WARNING)}")
            with st.container(horizontal=True, key=f"cmt_act_{c['id']}"):
                n = c["helpful"]
                st.button(f"{_('Helpful')} · {n}" if n else _("Helpful"), key=f"cm_h_{c['id']}", icon=":material/thumb_up:",
                          type="primary" if c["i_voted"] else "secondary", on_click=_toggle_helpful, args=(c["id"], uid))
                if not reply:
                    st.button(_("Reply"), key=f"cm_rp_{c['id']}", icon=":material/reply:", type="tertiary",
                              on_click=_start_reply, args=(c["id"],))
                if c["mine"]:
                    st.button(_("Delete"), key=f"cm_dc_{c['id']}", icon=":material/delete:", type="tertiary",
                              on_click=_delete_comment, args=(c["id"], uid))
                elif st.button(_("Report"), key=f"cm_rc_{c['id']}", icon=":material/flag:", type="tertiary"):
                    _report_dialog("comment", c["id"], uid)


def _comments(uid: int, post_id: int):
    sort = st.pills(_("Sort comments"), ["newest", "helpful"], default="newest", required=True, key=f"cm_cs_{post_id}",
                    format_func=lambda v: _("Newest") if v == "newest" else _("Helpful"), label_visibility="collapsed")
    try:
        tops = db.comments_for(post_id, uid, sort)
    except sqlite3.Error:
        _db_error(f"cm_cretry_{post_id}")
        return
    if not tops:
        st.caption(_("No comments yet. Be the first to reply."))
    for c in tops:
        _comment(uid, post_id, c, reply=False)
        for r in c["replies"]:
            _comment(uid, post_id, r, reply=True)
        if st.session_state.get("cm_reply") == c["id"] and c["status"] == "visible":
            _comment_form(uid, post_id, c["id"], f"cm_rf_{c['id']}")
    _comment_form(uid, post_id, None, f"cm_cf_{post_id}")


# ---- posts and feed --------------------------------------------------------------
def _post_card(uid: int, p, counts: dict, mine: set, scope: str):
    pid = p["id"]
    who = html.escape(p["alias"]) if p["alias"] else _("Anonymous")
    if p["mine"]:
        who += f' ({_("you")})'
    edited = f' · {_("edited")}' if p["edited"] else ""
    chips = [_cond_label(p["condition"])] if p["condition"] in cm.BY_ID else []
    if p["post_type"] in cm.POST_TYPES:
        chips.append(_(p["post_type"]))
    with st.container(key=f"card_post_{scope}_{pid}"):
        st.markdown(f'<div class="ah-ph">{_avatar(p["alias"] or f"anon{pid}", 44, anon=not p["alias"])}<div>'
                    f'<span class="who">{who}</span><span class="ago">{cm.ago(p["created"])}{edited}</span>'
                    f'<div class="ah-tags">{_tags(chips)}</div></div></div>'
                    f'<div class="ah-body">{_text_html(p["story"])}</div>', unsafe_allow_html=True)
        if p["has_image"]:
            img = db.post_image(pid)
            if img:
                st.image(img, width="stretch")
        if cm.looks_like_medicine(p["story"]):
            st.warning(_(cm.MED_WARNING), icon=":material/medication:")

        with st.container(horizontal=True, key=f"rx_{scope}_{pid}"):
            for kind, label, icon in cm.REACTIONS:
                n = counts.get(kind, 0)
                st.button(f"{_(label)} · {n}" if n else _(label), key=f"rx_{scope}_{pid}_{kind}", icon=icon,
                          type="primary" if kind in mine else "secondary", on_click=_toggle_reaction, args=(pid, uid, kind))
            opened = st.session_state.get("cm_open") == pid
            st.button(f"{_('Comments')} · {p['cc']}" if p["cc"] else _("Comments"), key=f"cmt_btn_{scope}_{pid}",
                      icon=":material/chat_bubble:", type="primary" if opened else "secondary",
                      on_click=_toggle_comments, args=(pid,))
        with st.container(horizontal=True, key=f"act_{scope}_{pid}"):
            if p["mine"]:
                if st.button(_("Edit"), key=f"edit_{scope}_{pid}", icon=":material/edit:", type="tertiary"):
                    _edit_dialog(p, uid)
                if st.button(_("Delete"), key=f"del_{scope}_{pid}", icon=":material/delete:", type="tertiary"):
                    _delete_dialog(pid, uid)
            elif st.button(_("Report"), key=f"rep_{scope}_{pid}", icon=":material/flag:", type="tertiary"):
                _report_dialog("post", pid, uid)
        if opened:
            _comments(uid, pid)


def _feed(uid: int, cond_ids: list, scope: str, conds: dict, default_cond=None):
    """Share button, keyword search, sort and the post list for the given conditions."""
    with st.container(key=f"card_compose_{scope}"):
        if st.button(_("Share something..."), key=f"cm_share_{scope}", type="primary", icon=":material/edit:", width="stretch"):
            _composer(uid, conds, default_cond)
    search = st.text_input(_("Search posts"), key=f"cm_q_{scope}", icon=":material/search:", label_visibility="collapsed",
                           placeholder=_("Search posts by keyword...")).strip()
    sort = st.pills(_("Sort posts"), ["latest", "popular"], default="latest", required=True, key=f"cm_sort_{scope}",
                    format_func=lambda v: _("Latest") if v == "latest" else _("Popular"), label_visibility="collapsed")
    limit_key = f"cm_lim_{scope}"
    limit = st.session_state.get(limit_key, PAGE_SIZE)
    try:
        with st.spinner(_("Loading posts...")):
            rows = db.feed(uid, cond_ids, search, sort, limit + 1)
            more = len(rows) > limit
            rows = rows[:limit]
            counts, mine = db.reaction_summary([r["id"] for r in rows], uid)
    except sqlite3.Error:
        _db_error(f"cm_retry_{scope}")
        return
    if not rows:
        if search:
            st.info(_("No posts match your search. Try a different word."), icon=":material/search_off:")
        else:
            st.info(_("No posts here yet. Be the first to share something."), icon=":material/forum:")
        return
    for p in rows:
        _post_card(uid, p, counts.get(p["id"], {}), mine.get(p["id"], set()), scope)
    if more:
        st.button(_("Load more"), key=f"cm_more_{scope}", on_click=_more, args=(limit_key, PAGE_SIZE), width="stretch")


# ---- tabs --------------------------------------------------------------------
def _for_you(uid: int, conds: dict):
    joined = [c for c, v in conds.items() if v == "community"]
    if not joined:
        st.info(_("You have not joined any community yet. Open Selected Conditions and tap Join, or use + to change your choices."),
                icon=":material/group_add:")
        return
    _feed(uid, joined, "foryou", conds)


def _cond_card(cid: str, vis, counts: dict):
    c = cm.BY_ID[cid]
    badge = {"community": _("Community"), "personal": _("Personal")}.get(vis, _("Not joined"))
    with st.container(key=f"card_cond_{cid}"):
        a, b = st.columns([4, 1.3], vertical_alignment="center")
        a.markdown(f'<b>{c["icon"]} {html.escape(_(c["name"]))}</b> <span class="ah-tag">{badge}</span><br>'
                   f'<span class="ah-fine">{_members_text(counts.get(cid, 0))}</span>', unsafe_allow_html=True)
        b.button(_("Open"), key=f"open_{cid}", on_click=_open_condition, args=(cid,), width="stretch")


def _selected(uid: int, conds: dict):
    cid = st.session_state.get("cm_cond")
    try:
        counts = db.member_counts()
    except sqlite3.Error:
        _db_error("cm_sel_retry")
        return
    if cid in cm.BY_ID:
        _condition_page(uid, cid, conds, counts)
        return
    st.markdown(f"**{_('Your conditions')}**")
    for k, v in conds.items():
        _cond_card(k, v, counts)
    others = [c["id"] for c in cm.CONDITIONS if c["id"] not in conds]
    if others:
        st.markdown(f"**{_('Explore more conditions')}**")
        for k in others:
            _cond_card(k, None, counts)


def _condition_page(uid: int, cid: str, conds: dict, counts: dict):
    c = cm.BY_ID[cid]
    st.button(_("Back"), key="cm_back", icon=":material/arrow_back:", type="tertiary", on_click=_close_condition)
    vis = conds.get(cid)
    with st.container(key="card_cond_head"):
        a, b = st.columns([3, 1.3], vertical_alignment="center")
        a.markdown(f'### {c["icon"]} {_(c["name"])}')
        if vis == "community":
            b.button(_("Joined"), key="cm_joined", icon=":material/check:", on_click=_leave, args=(uid, cid), width="stretch",
                     help=_("Tap to leave this community"))
        else:
            b.button(_("Join"), key="cm_join", type="primary", icon=":material/add:", on_click=_join, args=(uid, cid), width="stretch")
        st.write(_(c["description"]))
        st.markdown(f'<span class="ah-tag">{_members_text(counts.get(cid, 0))}</span>', unsafe_allow_html=True)
        if vis == "personal":
            st.caption(_("This is private to you. Join to be counted as a member and see its posts in For You."))
        st.markdown(f"**{_('Community rules')}**")
        for r in cm.RULES[:4]:
            st.markdown(f"- {_(r)}")
    _feed(uid, [cid], f"cond_{cid}", conds, default_cond=cid)


def _add_tab(uid: int, conds: dict):
    st.markdown(f"**{_('Add or change your conditions')}**")
    choices = _picker("add", conds)
    if not choices:
        st.caption(_("Choose at least one condition."))
    if st.button(_("Save changes"), type="primary", disabled=not choices, key="add_go", width="stretch"):
        try:
            err = db.save_conditions(uid, choices)
        except sqlite3.Error:
            err = "Could not save your choices. Please try again."
        if err:
            st.error(_(err))
        else:
            _flash(_("Your conditions are updated."))
            st.rerun()


# ---- page ---------------------------------------------------------------------
def _relax_card():
    with st.container(border=True):
        col1, col2 = st.columns([5, 1.5], vertical_alignment="center")
        col1.markdown(
            "🌿 **Take a Moment for Yourself**\n\n"
            "*Feeling anxious or overwhelmed? Take a one-minute breathing break to center your mind.*"
        )
        if col2.button("✨ Breathe", key="goto_relax_page", type="primary", use_container_width=True):
            st.session_state["nav_page"] = "Relax"
            st.rerun()


def render():
    st.markdown(_CSS, unsafe_allow_html=True)
    tr_list(_STATIC)
    ui.page_header(_("Community"), _("Connect with others on similar health journeys."))
    ui.notice(_(cm.DISCLAIMER))
    _relax_card()

    try:
        uid = cm.resolve_user_id(st.session_state.get("user_data"))
        if uid is None:
            st.info(_("Please sign in to join the Community."))
            return
        if msg := st.session_state.pop("cm_flash", None):
            st.toast(msg)
        conds = db.user_conditions(uid)
        profile = db.community_profile(uid)
    except sqlite3.Error:
        _db_error("cm_boot_retry")
        return

    if not (profile and profile["onboarded"]) or not conds:
        _onboarding(uid)          # first visit: required, cannot be dismissed without saving
        return

    names = {"foryou": _("For You"), "mine": _("Selected Conditions"), "add": "+"}
    view = st.pills(_("Community sections"), VIEWS, default="foryou", required=True, key="cm_view",
                    format_func=names.get, label_visibility="collapsed")
    try:
        if view == "foryou":
            _for_you(uid, conds)
        elif view == "mine":
            _selected(uid, conds)
        else:
            _add_tab(uid, conds)
    except sqlite3.Error:
        _db_error("cm_view_retry")

    with st.expander(_("Community Rules & Disclaimer"), icon=":material/shield:"):
        for r in cm.RULES:
            st.markdown(f"- {_(r)}")
        st.caption(_(cm.DISCLAIMER))
        st.caption(_(cm.MED_WARNING))
