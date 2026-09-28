import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from config import MASCOT_NAME, TIMEZONE
from modules import ui
from modules.mascot import say
from modules.translate import tr, tr_list

MESSAGES = {
    "Medicine": "Time for your medicine. Take it exactly as your doctor advised.",
    "Period": "Your period may start soon. Keep supplies ready and drink enough water.",
    "Iron / vitamin tablet": "Don't forget your iron or vitamin tablet today.",
    "Water": "Have a glass of water. Your body will thank you!",
    "Doctor visit": "You have a doctor visit today. Carry your reports and your question list.",
}
KINDS = list(MESSAGES)


def _now():
    return datetime.now(ZoneInfo(TIMEZONE))


def _ics(rems):
    stamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Womens Health Translator//EN"]
    for r in rems:
        start = datetime.combine(r["date"] if r["repeat"] == "Once" else _now().date(), r["time"])
        lines += ["BEGIN:VEVENT", f"UID:{r['id']}@whtranslator", f"DTSTAMP:{stamp}",
                  f"DTSTART:{start:%Y%m%dT%H%M%S}", f"SUMMARY:{r['kind']} {r['note']}".strip()]
        if r["repeat"] == "Every day":
            lines.append("RRULE:FREQ=DAILY")
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Reminder", "TRIGGER:PT0M", "END:VALARM", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


@st.fragment(run_every=10)
def _watcher():
    now = _now()
    st.caption(f"🕒 Clock ({TIMEZONE}): {now:%d %b %Y, %I:%M:%S %p}. {MASCOT_NAME} checks your reminders every few seconds while this page is open.")
    for r in st.session_state.reminders:
        today = now.date()
        due = r["repeat"] == "Every day" or r["date"] == today
        if due and now.time() >= r["time"] and r.get("fired") != today.isoformat():
            r["fired"] = today.isoformat()
            st.session_state.alerts.append({"id": uuid.uuid4().hex[:8], "kind": r["kind"], "note": r["note"]})
            st.toast(f"{MASCOT_NAME}: {r['kind']} reminder", icon="⏰")
    for a in list(st.session_state.alerts):
        say(f"{tr(MESSAGES[a['kind']])} {a['note']}".strip())
        if st.button("Done ✅", key=f"done_{a['id']}"):
            st.session_state.alerts.remove(a)
            st.rerun(scope="fragment")


def render():
    st.session_state.setdefault("reminders", [])
    st.session_state.setdefault("alerts", [])
    ui.page_header(*tr_list([f"Care Reminders from {MASCOT_NAME}", "Set a time for medicines, periods and more. Reminders live in this session while the page is open. Download the calendar file to get real phone alerts."]))

    _watcher()

    with st.form("rem_form"):
        c1, c2, c3, c4 = st.columns([2, 1.3, 1.5, 2.2])
        kind = c1.selectbox("Remind me about", KINDS, key="rem_kind")
        when = c2.time_input("Time", value=(_now() + timedelta(minutes=1)).time().replace(second=0, microsecond=0), key="rem_time")
        repeat = c3.selectbox("Repeat", ["Every day", "Once"], key="rem_repeat")
        note = c4.text_input("Note (optional)", key="rem_note", placeholder="e.g. after lunch")
        if st.form_submit_button("Add reminder", type="primary"):
            now = _now()
            item = {"id": uuid.uuid4().hex[:8], "kind": kind, "time": when, "repeat": repeat, "note": note.strip(), "date": now.date()}
            if now.time() >= when:
                item["fired"] = now.date().isoformat()  # already past for today; do not fire instantly
            st.session_state.reminders.append(item)
            st.rerun()

    b1, b2 = st.columns([1, 3])
    if b1.button("Test my character now", key="rem_test"):
        st.session_state.alerts.append({"id": uuid.uuid4().hex[:8], "kind": kind, "note": ""})
        st.rerun()

    if st.session_state.reminders:
        st.subheader("Your reminders")
        for r in sorted(st.session_state.reminders, key=lambda x: x["time"]):
            c1, c2 = st.columns([6, 1])
            when_txt = "every day" if r["repeat"] == "Every day" else f"on {r['date']:%d %b}"
            c1.markdown(f"**{r['kind']}** at {r['time']:%I:%M %p}, {when_txt}  {('· ' + r['note']) if r['note'] else ''}")
            if c2.button("Remove", key=f"rm_{r['id']}"):
                st.session_state.reminders.remove(r)
                st.rerun()
        st.download_button("⬇️ Download calendar file (.ics) for phone alerts", _ics(st.session_state.reminders),
                           file_name="reminders.ics", mime="text/calendar", key="dl_ics")

    st.divider()
    st.subheader("Next period estimator")
    today = _now().date()
    c1, c2 = st.columns(2)
    last = c1.date_input("First day of your last period", value=today - timedelta(days=14), max_value=today, key="pe_last")
    cycle = c2.slider("Usual cycle length (days)", 21, 45, 28, key="pe_cycle")
    nxt = last + timedelta(days=cycle)
    say(f"{tr('Your next period is expected around')} {nxt:%d %b %Y}. {tr('This is only an estimate. Cycles can vary.')}")
    if st.button("Add a period reminder for the day before", key="pe_add"):
        d = nxt - timedelta(days=1)
        if d < today:
            st.warning("That date has already passed. Update the date of your last period.")
        else:
            st.session_state.reminders.append({"id": uuid.uuid4().hex[:8], "kind": "Period", "time": datetime.strptime("09:00", "%H:%M").time(),
                                               "repeat": "Once", "note": "", "date": d})
            st.rerun()
