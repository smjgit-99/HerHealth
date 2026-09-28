import html
import re

from modules.content import load_json


def _index():
    idx = {}
    for i, e in enumerate(load_json("glossary")):
        for t in e["terms"]:
            idx[t.lower()] = i
    return idx


def _pattern(idx):
    return re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(idx, key=len, reverse=True)) + r")\b", re.I)


def find_terms(text: str):
    """Glossary entries present in the text, first-seen order: [{term, found_as, plain, category}]"""
    g, idx = load_json("glossary"), _index()
    seen, out = set(), []
    for m in _pattern(idx).finditer(text):
        i = idx[m.group(0).lower()]
        if i in seen:
            continue
        seen.add(i)
        out.append({"term": g[i]["terms"][0], "found_as": m.group(0), "plain": g[i]["plain"], "category": g[i]["category"]})
    return out


def highlight_html(text: str) -> str:
    """Escape the report and wrap jargon in <mark> with the plain meaning as a tooltip."""
    g, idx = load_json("glossary"), _index()
    pat, out, last = _pattern(idx), [], 0
    for m in pat.finditer(text):
        out.append(html.escape(text[last:m.start()]))
        tip = html.escape(g[idx[m.group(0).lower()]]["plain"], quote=True)
        out.append(f'<mark title="{tip}">{html.escape(m.group(0))}</mark>')
        last = m.end()
    out.append(html.escape(text[last:]))
    return "".join(out).replace("\r", "").replace("\n", "<br>")
