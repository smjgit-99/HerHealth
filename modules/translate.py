"""Translation with per-text caching and safe fallback to English.

Static content (glossary, disease pages) is cached for all users.
Anything derived from a user's report is cached only in that user's session.
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import streamlit as st
from deep_translator import GoogleTranslator

_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "translation_cache.json"


def _load_cache() -> dict:
    try:
        return {tuple(k.split("\u241f", 1)): v for k, v in json.loads(_CACHE_FILE.read_text("utf-8")).items()}
    except Exception:
        return {}


def _save_cache(cache: dict):
    try:
        _CACHE_FILE.write_text(json.dumps({"\u241f".join(k): v for k, v in cache.items()}, ensure_ascii=False), "utf-8")
    except Exception:
        pass


# Static (non-report) translations persist on disk, so each text is fetched only once, ever.
_PUBLIC: dict = _load_cache()


def _load_bundled() -> dict:
    try:
        return json.loads((_CACHE_FILE.parent / "translations.json").read_text("utf-8"))
    except Exception:
        return {}


# Hindi and Marathi text shipped with the app: works offline and instantly.
_BUNDLED: dict = _load_bundled()

_RANGE_WORDS = {"hi": (" से ", "से कम "), "mr": (" ते ", "पेक्षा कमी ")}
_SENTENCES = {
    "hi": {"is": "{t} {w} है ({v}; सामान्य सीमा {r})। {m}", "low": "कम", "high": "ज़्यादा",
           "chk": "रिपोर्ट में इकाई '{u}' दिखती है, जो सामान्य {n} से अलग है। अपनी रिपोर्ट में छपी सीमा से तुलना करें।",
           "mention": "रिपोर्ट में '{t}' का उल्लेख है। सरल शब्दों में: {p}"},
    "mr": {"is": "{t} {w} आहे ({v}; सामान्य मर्यादा {r}). {m}", "low": "कमी", "high": "जास्त",
           "chk": "अहवालात '{u}' हे एकक दिसते, जे नेहमीच्या {n} पेक्षा वेगळे आहे. तुमच्या अहवालात छापलेल्या मर्यादेशी तुलना करा.",
           "mention": "अहवालात '{t}' चा उल्लेख आहे. सोप्या शब्दांत: {p}"},
}


def _local_range(r: str, code: str) -> str:
    to, below = _RANGE_WORDS[code]
    return (below + r[len("below "):]) if r.startswith("below ") else r.replace(" to ", to, 1)


def _bundled(text: str, code: str):
    """Translate from the bundled dictionary, including the generated report sentences. None if unknown."""
    table = _BUNDLED.get(code)
    if not table:
        return None
    if text in table:
        return table[text]
    names, tmpl = _BUNDLED.get("_names", {}).get(code, {}), _SENTENCES[code]
    m = re.match(r"^(.+?) is (low|high) \((.+?); usual range (.+?)\)\. (.*)$", text, re.S)
    if m and m.group(5) in table:
        t, w, v, r, mean = m.groups()
        return tmpl["is"].format(t=names.get(t, t), w=tmpl[w], v=v, r=_local_range(r, code), m=table[mean])
    m = re.match(r"^The report mentions '(.+?)'\. In simple words: (.*)$", text, re.S)
    if m and m.group(2) in table:
        return tmpl["mention"].format(t=m.group(1), p=table[m.group(2)])
    m = re.match(r"^The report shows the unit '(.+?)', which differs from the usual (.+?)\. Compare with", text, re.S)
    if m:
        return tmpl["chk"].format(u=m.group(1), n=m.group(2))
    return None


def current_code() -> str:
    return st.session_state.get("lang_code", "en")


def _chunks(text: str, limit: int = 4500):
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit and cur:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur:
        out.append(cur)
    return out


def _one(text: str, code: str):
    """Returns translated text, or None if the service failed. Must not call st.*"""
    for _ in range(1):
        try:
            tr = GoogleTranslator(source="auto", target=code)
            parts = [tr.translate(c.rstrip("\n")) for c in _chunks(text)]
            if any(p is None for p in parts):
                continue
            return "\n".join(parts)
        except Exception:
            continue
    return None


def tr_list(texts, private: bool = False):
    """Translate a list of strings into the selected language.

    Bundled Hindi/Marathi text is used first (instant, offline). Only text that is not bundled
    (for example words typed by the user) goes to Google Translate, and if that is unreachable the
    English text is shown right away instead of keeping the page waiting.
    """
    texts = list(texts)
    code = current_code()
    if code == "en":
        return texts
    cache = st.session_state.setdefault("_tr_cache", {}) if private else _PUBLIC
    out, todo = {}, []
    for t in dict.fromkeys(texts):
        if not t or not t.strip():
            continue
        hit = _bundled(t, code)
        if hit is not None:
            out[t] = hit
        elif (code, t) in cache:
            out[t] = cache[(code, t)]
        else:
            todo.append(t)
    if todo and time.time() - st.session_state.get("_tr_offline", 0) > 60:
        with st.spinner("Translating..."):
            first = _one(todo[0], code)
            if first is None:  # service unreachable: don't wait on every remaining text
                st.session_state["_tr_offline"] = time.time()  # retry after a minute
                st.toast("Translation service not reachable for some text. Showing English.", icon="⚠️")
            else:
                cache[(code, todo[0])] = out[todo[0]] = first
                rest = todo[1:]
                with ThreadPoolExecutor(max_workers=4) as ex:
                    results = list(ex.map(lambda t: _one(t, code), rest))
                for t, r in zip(rest, results):
                    if r is not None:
                        cache[(code, t)] = out[t] = r
                if not private:
                    _save_cache(cache)
    return [out.get(t, t) for t in texts]


def tr(text: str, private: bool = False) -> str:
    return tr_list([text], private)[0]


def bilingual(label: str) -> str:
    """'Translated label (English label)' for headings, so demo viewers can map them."""
    if current_code() == "en":
        return label
    return f"{tr(label)} ({label})"
