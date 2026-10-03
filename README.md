# HerHealth: Women's Health Information Translator

Turns medical reports into simple language (English, Hindi, Marathi), with a doctor-visit checklist,
a health library and glossary, a breathing break for medical anxiety, and a community preview.

## Run (VS Code terminal)
    1. python -m venv .venv
    2. .venv\Scripts\activate           (Windows)   |   source .venv/bin/activate   (Mac/Linux)
    3. pip install -r requirements.txt
    4. streamlit run app.py

Optional AI mode: copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY`. Without it, everything still works with offline rules.
Image OCR needs Tesseract installed locally (Windows: https://github.com/UB-Mannheim/tesseract/wiki). Without it, paste text instead.

## Deploy (Streamlit Community Cloud)
1. Push to GitHub. 2. share.streamlit.io > Create app > pick repo, branch `main`, file `app.py`.
3. Advanced settings > Secrets: paste `ANTHROPIC_API_KEY = "..."` (optional). 4. Deploy.
`packages.txt` installs Tesseract on the cloud automatically.

## Where things live
| Path | What |
|---|---|
| app.py | top navigation bar (Home, Translator, Community, Learn), language picker, page routing |
| config.py | **mascot name / image**, timezone, model |
| views/ | dashboard (Home), translator (+ checklist as "next step"), community (+ breathing break), learn (info + glossary) |
| modules/ | logic: ingest (files+OCR), analyzer, ranges, highlight, translate, tts, llm |
| data/ | all static content as JSON. **Edit here, no code needed** |
| assets/mascot/mascot.png | put your character image here |

## Before the demo (10 min)
- Open every paper link in `data/diseases.json` once.
- Have the team doctor/mentor check `data/reference_ranges.json` and `data/diseases.json`.
- Run "Try sample report" in each demo language once, to warm the translation cache.
- Keep the sample report and one PDF and one image ready. Have a phone hotspot as backup for Wi-Fi.
- Say clearly: community is a preview with sample stories.

## Roadmap (hackathon)
- [x] Remove reminders; merge checklist into Translator, library + glossary into Learn, relaxer into Community
- [ ] Login / register (DigiLocker sandbox flow)
- [ ] Report-verified community badge, moderated posting, consent-based connect
