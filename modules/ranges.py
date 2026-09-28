"""Find known lab values in report text and compare them with reference ranges."""
import re

from modules.content import load_json


def _fmt_range(t):
    u = t["unit"]
    if t["low"] is None:
        return f"below {t['high'] + (0.1 if t['unit'] == '%' else 1):g} {u}"
    return f"{t['low']:g} to {t['high']:g} {u}"


def extract_values(text: str):
    """Return rows: {key, test, value, unit, range, status, meaning}. Status: Low / Normal / High / Check unit."""
    clean = re.sub(r"gly(?:cated|cosylated)\s+ha?emoglobin", "hba1c", text, flags=re.I)
    rows = []
    for t in load_json("reference_ranges"):
        found = None
        for alias in t["aliases"]:
            pat = (rf"\b{re.escape(alias)}\b(?:\s*\([^)\n]{{0,20}}\))?[^\d\n]{{0,30}}"
                   rf"(\d+(?:\.\d+)?)(?:\s*([%a-zA-Zµμ/]{{1,10}}))?")
            m = re.search(pat, clean, flags=re.I)
            if m:
                found = m
                break
        if not found:
            continue
        value = float(found.group(1))
        unit_seen = (found.group(2) or "").lower()
        unit_seen = unit_seen if ("/" in unit_seen or "%" in unit_seen) else ""
        status, meaning = "Normal", ""
        if unit_seen and unit_seen not in t["units_ok"]:
            status = "Check unit"
            meaning = f"The report shows the unit '{found.group(2)}', which differs from the usual {t['unit']}. Compare with the range printed on your report."
        elif t["low"] is not None and value < t["low"]:
            status, meaning = "Low", t["low_meaning"]
        elif t["high"] is not None and value > t["high"]:
            status, meaning = "High", t["high_meaning"]
        rows.append({"key": t["key"], "test": t["name"], "value": value, "unit": t["unit"],
                     "range": _fmt_range(t), "status": status, "meaning": meaning})
    return rows
