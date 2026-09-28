"""Turn a report into: What This Means / What Is Normal / Things to Watch / Questions.

Works fully offline with rules. If an API key is present, Claude writes the plain-language
parts, while the "normal" numbers ALWAYS come from data/reference_ranges.json (never from the AI).
"""
import re

from modules import llm
from modules.content import load_json
from modules.highlight import find_terms
from modules.ranges import extract_values

SYSTEM = (
    "You explain medical reports to women in simple language (class 8 reading level). "
    "Never diagnose. Use phrases like 'may mean'. Do not invent numbers or reference ranges. "
    "Use only facts present in the report. Reply with JSON only, no other text: "
    '{"means": [3 to 6 short sentences], "watch": [3 to 6 short items], "questions": [5 to 8 questions to ask the doctor]}'
)


def _has_kw(text: str, kw: str) -> bool:
    pat = rf"\b{re.escape(kw)}\b" if len(kw) <= 4 else rf"\b{re.escape(kw)}"
    return re.search(pat, text, flags=re.I) is not None


def _rule_based(text, rows, terms):
    means = []
    for r in rows:
        if r["status"] in ("Low", "High"):
            means.append(f"{r['test']} is {r['status'].lower()} ({r['value']:g} {r['unit']}; usual range {r['range']}). {r['meaning']}")
    if rows and not means:
        means.append("The lab values we could read are within the usual ranges. Your doctor will still look at them together with your symptoms.")
    for t in [t for t in terms if t["category"] not in ("Lab tests", "Tests and scans")][:4]:
        means.append(f"The report mentions '{t['found_as']}'. In simple words: {t['plain']}")
    if not means:
        means.append("We could not find familiar terms or lab values in this text. Try pasting the findings or impression section, and check the file was read correctly.")

    watch = []
    for s in load_json("watch_signals"):
        if any(_has_kw(text, k) for k in s["keywords"]):
            watch.append(s["text"])
    if any(r["status"] in ("Low", "High") for r in rows):
        watch.append("Values outside the usual range usually need a repeat test or a check for the cause. Ask when to repeat them.")
    watch.append("Go to a doctor or emergency room quickly for very heavy bleeding, severe pain, fainting, fever with pain, or any bleeding in pregnancy.")

    cl = load_json("checklist")
    qs = list(cl["general"][:2])
    for topic in cl["by_topic"].values():
        if any(_has_kw(text, k) for k in topic["keywords"]):
            qs += topic["questions"][:2]
    for r in rows:
        if r["status"] in ("Low", "High"):
            qs += cl["by_test"].get(r["key"], [])[:2]
    qs += cl["general"][2:]
    return {"means": means, "watch": watch, "questions": list(dict.fromkeys(qs))[:16]}


def _valid(out):
    return (isinstance(out, dict)
            and all(isinstance(out.get(k), list) and out[k] and all(isinstance(x, str) for x in out[k])
                    for k in ("means", "watch", "questions")))


def analyze(text: str) -> dict:
    text = text.strip()
    rows = extract_values(text)
    terms = find_terms(text)
    rules = _rule_based(text, rows, terms)
    mode = "Offline rules"
    result = dict(rules)
    if llm.available():
        facts = "\n".join(f"- {r['test']}: {r['value']:g} {r['unit']} ({r['status']}; usual {r['range']})" for r in rows)
        out = llm.ask_json(SYSTEM, f"Report text:\n{text[:6000]}\n\nChecked lab values:\n{facts or 'none found'}")
        if _valid(out):
            result = {"means": out["means"][:6], "watch": out["watch"][:6] + rules["watch"][-1:],
                      "questions": list(dict.fromkeys(out["questions"][:8] + rules["questions"]))[:16]}
            mode = "AI plain-language + verified ranges"
    result.update(rows=rows, terms=terms, mode=mode)
    return result
