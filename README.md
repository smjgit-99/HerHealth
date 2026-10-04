# HerHealth: Women's Health Report Translator + Community

Turns medical reports into plain language (English, Hindi, Marathi), builds a doctor-visit
checklist, and connects women with peers in condition-based communities.

**Rules decide, AI only does the wording.** Reference ranges come from `data/reference_ranges.json`
(doctor-reviewable), never from the AI. AI is optional.

## Run locally
1. `python -m venv .venv`
2. `.venv\Scripts\activate` (Windows) | `source .venv/bin/activate` (Mac/Linux)
3. `pip install -r requirements.txt`
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your Supabase
   `url` and `key` (**required**: login and community use Supabase Auth).
5. `streamlit run app.py`

Optional: add `ANTHROPIC_API_KEY` to secrets for AI wording. Without it the translator
still works with offline rules.
Image OCR needs Tesseract (Windows: https://github.com/UB-Mannheim/tesseract/wiki). Without it,
paste text instead. Developed on Python 3.13.

Tests: `pip install -r requirements-dev.txt`, then `python tests/smoke_test.py`.

## Deploy (Streamlit Community Cloud)
1. Push to GitHub. 2. share.streamlit.io > Create app > repo, branch `main`, file `app.py`.
3. Advanced settings > Secrets: paste the contents of your `secrets.toml` (Supabase required).
4. Deploy. `packages.txt` installs Tesseract with English, Hindi and Marathi packs.

## How it works
Upload/paste > `ingest.py` (PDF, DOCX, OCR) > `ranges.py` + `highlight.py` (extract values and jargon)
> `analyzer.py` (rules, optional Claude wording) > `translate.py` (bundled Hindi/Marathi dictionary
first, Google Translate as fallback) > Translator page with read-aloud and download.

## Where things live
| Path | What |
|---|---|
| app.py | navigation, language picker, auth gate, page routing |
| config.py | mascot name/image, timezone, model |
| views/ | Home, Translator (+ doctor checklist), Community, Learn, Relax |
| modules/ | ingest, ranges, highlight, analyzer, translate, tts, llm, auth, db, community |
| data/ | all static content as JSON. **Edit here, no code needed** |

## Privacy
Uploaded reports are read in memory and not saved. Report text is sent to Anthropic only if an
API key is set. Read-aloud audio and any text outside the bundled dictionary go to Google.
Community members appear under aliases; uploaded photos are re-encoded to strip location data.

## Known limitations
- Ranges are general adult values, not adjusted for age, sex or pregnancy. Pending doctor review.
- Extracts 9 common lab tests; value formats vary between labs.
- Community posts are not pre-moderated (report button and medicine-mention warning only).
- Community data is stored in SQLite, which Streamlit Cloud resets on restart.

## Roadmap
- [x] Translator, doctor checklist, Learn library and glossary, breathing break
- [x] Login (Supabase Auth) and 12-condition community
- [ ] Doctor review of reference ranges
- [ ] Pilot with a clinic or NGO
- [ ] Moderated posting, report-verified badges, DigiLocker sign-in, more languages