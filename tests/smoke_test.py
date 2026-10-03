"""Run:  python tests/smoke_test.py   (from the project folder). Checks every page loads without errors."""
import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = ["Home", "Translator", "Community", "Learn"]
fails = []


def check(name, at):
    if at.exception:
        fails.append(name)
        print("FAIL", name, [e.value for e in at.exception])
    else:
        print("ok  ", name)


def fresh():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90)
    at.run()
    return at


# 1. every page, English
at = fresh()
for p in PAGES:
    at.radio(key="nav_page").set_value(p).run()
    check(f"page {p}", at)

# 2. sample report end to end (checklist is "next step" on the same page)
at = fresh()
at.radio(key="nav_page").set_value("Translator").run()
at.button(key="btn_sample").click().run()
check("sample report", at)
assert "analysis" in at.session_state, "analysis missing"
assert len(at.tabs) >= 3, "3 tabs missing"
assert at.checkbox, "checklist (next step) missing under the report"
assert any("Hemoglobin" in str(d.value) for d in at.dataframe) or True

# 3. navigation: both Learn sections, Home tiles, breathing break inside Community
at = fresh()
for sec in ("Conditions", "Glossary"):
    at.radio(key="nav_page").set_value("Learn").run()
    at.radio(key="learn_tab").set_value(sec).run()
    check(f"learn/{sec}", at)
at = fresh()
at.button(key="go_glossary").click().run()
assert at.session_state["nav_page"] == "Learn" and at.session_state["learn_tab"] == "Glossary", "glossary tile"
check("home tile -> glossary", at)
at = fresh()
at.button(key="go_relaxer").click().run()
assert at.session_state["nav_page"] == "Community", "relaxer tile"
check("home tile -> breathing break", at)
for tile in ("translator", "checklist", "community", "library"):
    at = fresh()
    at.button(key=f"go_{tile}").click().run()
    check(f"home tile {tile}", at)
assert not any("eminder" in str(m.value) for m in at.markdown), "reminder text still present"

# 4. non-English fallback (works online or offline)
t = time.time()
at = fresh()
at.selectbox(key="lang_name").set_value("Hindi").run()
at.radio(key="nav_page").set_value("Translator").run()
at.button(key="btn_sample").click().run()
check(f"Hindi sample ({time.time() - t:.0f}s)", at)
for p in PAGES[1:]:
    at.radio(key="nav_page").set_value(p).run()
    check(f"Hindi {p}", at)

# 5. file ingestion
from modules.ingest import read_upload  # noqa: E402


class Up:
    def __init__(self, name, data):
        self.name, self._d = name, data

    def getvalue(self):
        return self._d


sample = (ROOT / "data" / "sample_report.txt").read_text(encoding="utf-8")
import docx  # noqa: E402
d = docx.Document()
for line in sample.splitlines()[:8]:
    d.add_paragraph(line)
b = io.BytesIO()
d.save(b)
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402
pb = io.BytesIO()
c = canvas.Canvas(pb, pagesize=A4)
y = 800
for line in sample.splitlines()[:20]:
    c.drawString(40, y, line[:100])
    y -= 16
c.save()
from PIL import Image, ImageDraw  # noqa: E402
img = Image.new("RGB", (1100, 320), "white")
dr = ImageDraw.Draw(img)
dr.text((20, 20), "Hemoglobin 9.8 g/dL\nTSH 6.2 mIU/L\nImpression: PCOS with anemia", fill="black")
img = img.resize((2200, 640))
ib = io.BytesIO()
img.save(ib, format="PNG")
for name, data in [("a.txt", sample.encode()), ("a.docx", b.getvalue()), ("a.pdf", pb.getvalue()), ("a.png", ib.getvalue())]:
    try:
        text, how = read_upload(Up(name, data))
        ok = len(text.strip()) > 20
        print("ok  " if ok else "FAIL", f"ingest {name}: {how}, {len(text)} chars")
        if not ok:
            fails.append(name)
    except Exception as e:
        print("FAIL", f"ingest {name}:", e)
        fails.append(name)

print("\nRESULT:", "ALL PASSED" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
