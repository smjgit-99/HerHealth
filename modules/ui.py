"""Shared look and feel (HerHealth design system): CSS, icons, header/footer helpers."""
from datetime import datetime

import streamlit as st

import config

# Design tokens ---------------------------------------------------------------
PRIMARY = "#9B72CB"
PRIMARY_DARK = "#7E57B5"
TINT = "#EFE9F7"

# Lucide-style icon paths (24x24, stroke based)
_ICONS = {
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "file": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "checks": '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    "book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "wind": '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
    "glossary": '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/><path d="M10 2v8l3-2.5L16 10V2"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "languages": '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "sparkles": '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/>',
    "message": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "user": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="10" r="3"/><path d="M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662"/>',
    "translate": '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>',
}


def icon(name: str, size: int = 20, color: str = "currentColor", fill: str = "none", sw: float = 2) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" '
            f'style="flex:none">{_ICONS[name]}</svg>')


def logo_tile(size: int = 38) -> str:
    return (f'<span class="ah-logo" style="width:{size}px;height:{size}px">'
            f'{icon("heart", int(size * .55), "#fff", "#fff")}</span>')


def go(page: str):
    """Button callback: jump to another page."""
    st.session_state["nav_page"] = page


def page_header(title: str, subtitle: str = ""):
    sub = f'<p class="ah-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<div class="ah-pagehead"><h1>{title}</h1>{sub}</div>', unsafe_allow_html=True)


def brand() -> str:
    name = config.APP_TITLE
    head, tail = (name[:3], name[3:]) if name.startswith("Her") else (name, "")
    return f'<div class="ah-brand">{logo_tile()}<span>{head}<b>{tail}</b></span></div>'


def notice(text: str):
    st.markdown(f'<div class="ah-notice">{icon("shield", 15, PRIMARY_DARK)}<span>{text}</span></div>', unsafe_allow_html=True)


def footer(disclaimer_title: str, disclaimer_body: str, extra_caption: str = ""):
    st.markdown('<div class="ah-footer-gap"></div>', unsafe_allow_html=True)
    with st.container(key="footer"):
        st.markdown(
            f'<div class="ah-disc">{icon("shield", 20, "#E8A33D")}<div><b>{disclaimer_title}</b>'
            f'<p>{disclaimer_body}</p></div></div>'
            f'<div class="ah-foot-copy">© {datetime.now().year} {config.APP_TITLE}. All rights reserved.</div>',
            unsafe_allow_html=True)
        if extra_caption:
            st.caption(extra_caption)


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{{--p:{PRIMARY};--pd:{PRIMARY_DARK};--tint:{TINT};--bg:#F8F7FA;--card:#fff;--line:#ECE8F2;--ink:#1D1B2A;--mute:#6B6880;
 --shadow:0 1px 2px rgba(60,40,90,.04),0 4px 14px rgba(60,40,90,.04);}}
body,.stApp,.stApp :where(p,h1,h2,h3,h4,label,button,input,textarea,li,a,td,th,summary,b,i){{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;}}
.stApp [data-testid="stIconMaterial"],.stApp [translate="no"]{{font-family:"Material Symbols Rounded"!important;}}
.stApp{{background:var(--bg);color:var(--ink);}}
/* chrome we replace */
header[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"],#MainMenu,footer{{display:none!important;}}
.block-container,[data-testid="stMainBlockContainer"]{{max-width:1290px;padding:0 24px 24px!important;}}
[data-testid="stAppViewContainer"] > .main,[data-testid="stMain"]{{padding-top:0!important;}}
.stApp a{{color:var(--pd);}}
[data-testid="stMarkdownContainer"] ul li{{margin-bottom:.15rem;}}
h1,h2,h3{{letter-spacing:-.02em;color:var(--ink);}}

/* ---- top bar ---- */
.st-key-topbar{{background:#fff;border-bottom:1px solid var(--line);padding:10px 0;margin-bottom:22px;
 box-shadow:0 0 0 100vmax #fff;clip-path:inset(0 -100vmax);position:relative;z-index:5;}}
.ah-brand{{display:flex;align-items:center;gap:10px;font-size:1.25rem;font-weight:700;color:var(--ink);white-space:nowrap;}}
.ah-brand b{{color:var(--p);font-weight:700;}}
.ah-logo{{display:inline-flex;align-items:center;justify-content:center;border-radius:12px;
 background:linear-gradient(135deg,#B48CE0,#8B5FBF);box-shadow:0 4px 10px rgba(139,95,191,.35);}}
.st-key-topbar [data-testid="stRadioGroup"]{{gap:2px;flex-wrap:nowrap;justify-content:center;}}
.st-key-topbar [data-testid="stRadioOption"]{{padding:8px 9px;border-radius:10px;margin:0;cursor:pointer;transition:background .15s;}}
.st-key-topbar [data-testid="stRadioOption"] > div > div:first-child{{display:none;}}
.st-key-topbar [data-testid="stRadioOption"] p{{font-size:.9rem;font-weight:500;color:#5b5870;white-space:nowrap;margin:0;}}
.st-key-topbar [data-testid="stRadioOption"]:hover{{background:#F5F2FA;}}
.st-key-topbar [data-testid="stRadioOption"][data-selected="true"]{{background:var(--tint);}}
.st-key-topbar [data-testid="stRadioOption"][data-selected="true"] p{{color:var(--pd);font-weight:600;}}
.st-key-topbar [data-baseweb="select"] > div{{background:transparent;border:0;box-shadow:none;font-weight:500;}}

/* ---- page header + notice ---- */
.ah-pagehead h1{{font-size:2rem;font-weight:700;margin:6px 0 2px;padding:0;}}
.ah-sub{{color:var(--mute);font-size:1.02rem;margin:0 0 14px;}}
.ah-notice{{display:flex;align-items:center;gap:8px;background:#F4EFFA;border:1px solid #E7DDF4;color:#5a4a78;
 border-radius:10px;padding:7px 12px;font-size:.82rem;margin-bottom:14px;}}

/* ---- generic components ---- */
[class*="st-key-card"]{{background:#fff;border:1px solid var(--line)!important;border-radius:18px;box-shadow:var(--shadow);padding:18px 20px!important;}}
[class*="st-key-card_match"]{{border-radius:14px;box-shadow:none;padding:12px 16px!important;background:#fff;}}
[class*="st-key-card_post"] .stButton{{margin-top:2px;}}
.stButton > button[kind="tertiary"]{{border:0;background:transparent;box-shadow:none;color:var(--mute);font-weight:500;font-size:.85rem;padding:.2rem .4rem;}}
.stButton > button[kind="tertiary"]:hover{{color:#B04663;background:#FDF0F3;}}
[data-testid="stExpander"] details{{border:1px solid var(--line);border-radius:14px;background:#fff;box-shadow:var(--shadow);}}
[data-testid="stExpander"] summary{{font-weight:600;}}
.stButton > button,.stDownloadButton > button,[data-testid="stFormSubmitButton"] > button,[data-testid="stPopover"] > button{{
 border-radius:11px;border:1px solid var(--line);background:#fff;color:var(--ink);font-weight:600;padding:.5rem 1rem;box-shadow:var(--shadow);transition:all .15s;}}
.stButton > button:hover,.stDownloadButton > button:hover,[data-testid="stPopover"] > button:hover{{border-color:var(--p);color:var(--pd);background:#FBF9FE;}}
.stButton > button[kind="primary"],[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]{{
 background:var(--p);border-color:var(--p);color:#fff;box-shadow:0 4px 12px rgba(155,114,203,.35);}}
.stButton > button[kind="primary"]:hover{{background:var(--pd);border-color:var(--pd);color:#fff;}}
.stButton > button[kind="primary"]:disabled{{opacity:.5;box-shadow:none;}}
[data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input,[data-baseweb="select"] > div,[data-testid="stDateInput"] input,[data-testid="stTimeInput"] input{{
 border-radius:12px;background:#fff;}}
[data-testid="stTextArea"] textarea:focus,[data-testid="stTextInput"] input:focus{{border-color:var(--p);box-shadow:0 0 0 1px var(--p);}}
[data-testid="stFileUploader"] section{{border-radius:14px;background:#fff;border:1.5px dashed #D9CCEB;}}
[data-testid="stTabs"] [role="tablist"]{{gap:6px;border-bottom:1px solid var(--line);}}
[data-testid="stTabs"] button[role="tab"]{{border-radius:10px 10px 0 0;font-weight:600;padding:.6rem 1.1rem;}}
[data-testid="stTabs"] button[aria-selected="true"]{{color:var(--pd);}}
[data-testid="stAlert"]{{border-radius:14px;}}
[data-testid="stDataFrame"]{{border-radius:14px;overflow:hidden;border:1px solid var(--line);}}
[data-testid="stChatMessage"]{{background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);}}
/* pills (filter chips) */
[data-testid="stButtonGroup"]{{flex-wrap:wrap;}}
.st-key-card_twin hr{{margin:.6rem 0 .9rem;border-color:var(--line);}}
[data-testid="stButtonGroup"] button[data-variant="pills"]{{border-radius:999px;background:#fff;border:1px solid var(--line);color:#4b4860;padding:.32rem 1.05rem;box-shadow:none;}}
[data-testid="stButtonGroup"] button[data-variant="pills"]:hover{{border-color:var(--p);}}
[data-testid="stButtonGroup"] button[data-variant="pills"][aria-checked="true"]{{background:var(--p);border-color:var(--p);}}
[data-testid="stButtonGroup"] button[data-variant="pills"][aria-checked="true"] *{{color:#fff!important;font-weight:600;}}

/* ---- dashboard ---- */
.st-key-hero{{position:relative;overflow:hidden;border-radius:26px;padding:54px 66px 44px;margin-bottom:22px;
 background:radial-gradient(900px 400px at 100% 0%,#EEEAF5 0%,transparent 60%),linear-gradient(135deg,#F4EEF8 0%,#F1EFF6 55%,#EEF0F7 100%);
 border:1px solid #EFEAF5;}}
.ah-badge{{display:inline-flex;align-items:center;gap:7px;padding:5px 13px;border-radius:999px;background:#fff;border:1px solid #E5DAF3;
 color:var(--pd);font-size:.8rem;font-weight:600;}}
.ah-hero-h{{font-size:clamp(2.4rem,5vw,4.1rem);line-height:1.02;font-weight:800;letter-spacing:-.035em;margin:22px 0 18px;color:#14121F;max-width:720px;}}
.ah-hero-p{{font-size:1.2rem;line-height:1.6;color:var(--mute);max-width:660px;margin:0 0 26px;}}
.st-key-hero .stButton > button{{padding:.85rem 1.4rem;font-size:1rem;border-radius:12px;}}
.ah-feat{{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:var(--shadow);height:100%;}}
.ah-feat .t{{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex:none;}}
.ah-feat b{{display:block;font-size:.98rem;color:var(--ink);}}
.ah-feat span{{font-size:.86rem;color:var(--mute);}}
.ah-h2{{font-size:1.45rem;font-weight:700;margin:30px 0 14px;letter-spacing:-.02em;}}
[class*="st-key-qa_"]{{position:relative;border-radius:18px;border:1px solid var(--line);padding:22px 22px 20px;min-height:122px;
 box-shadow:var(--shadow);transition:transform .15s,box-shadow .15s;}}
[class*="st-key-qa_"]:hover{{transform:translateY(-2px);box-shadow:0 10px 26px rgba(90,60,140,.12);}}
[class*="st-key-qa_"] [data-testid="stButton"]{{position:absolute;inset:0;z-index:2;}}
[class*="st-key-qa_"] [data-testid="stButton"] button{{width:100%;height:100%;opacity:0;cursor:pointer;}}
.ah-qa{{display:flex;gap:16px;align-items:flex-start;}}
.ah-qa .t{{width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center;flex:none;box-shadow:0 6px 14px rgba(0,0,0,.12);}}
.ah-qa b{{display:block;font-size:1.06rem;margin-bottom:4px;color:var(--ink);}}
.ah-qa span{{font-size:.93rem;line-height:1.45;color:var(--mute);}}
.ah-card{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px 24px;box-shadow:var(--shadow);height:100%;}}
.ah-card h3{{font-size:1.15rem;margin:0 0 12px;}}
.ah-step{{display:flex;gap:12px;align-items:flex-start;margin:10px 0;color:#3f3c52;font-size:.95rem;}}
.ah-step i{{font-style:normal;width:26px;height:26px;border-radius:50%;background:var(--tint);color:var(--pd);font-weight:700;font-size:.82rem;
 display:flex;align-items:center;justify-content:center;flex:none;}}

/* ---- community ---- */
.ah-twin-head{{display:flex;gap:14px;align-items:center;}}
.ah-twin-head .t{{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#8F86D8,#6FB0C8);}}
.ah-twin-head b{{font-size:1.08rem;display:block;}}
.ah-twin-head span{{font-size:.86rem;color:var(--mute);}}
.ah-match{{display:flex;gap:14px;align-items:center;padding:4px 2px;}}
.ah-av{{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex:none;}}
.ah-name{{font-weight:700;font-size:1.04rem;margin-right:8px;}}
.ah-pct{{background:#F9DCE3;color:#B04663;border-radius:999px;padding:2px 10px;font-size:.78rem;font-weight:600;}}
.ah-tags{{margin-top:7px;display:flex;gap:7px;flex-wrap:wrap;}}
.ah-tag{{background:#F1EAF9;color:var(--pd);border-radius:7px;padding:2px 9px;font-size:.78rem;font-weight:500;}}
.ah-post{{display:flex;gap:14px;}}
.ah-post .who{{font-weight:700;font-size:1.04rem;}}
.ah-post .ago{{color:var(--mute);font-size:.82rem;margin-left:8px;}}
.ah-post p{{margin:10px 0 6px;color:#2e2b3d;line-height:1.55;}}
.ah-post .tip{{background:#F8F5FC;border-radius:10px;padding:8px 12px;font-size:.9rem;color:#4a4560;margin:6px 0;}}
.ah-post .meta{{display:flex;gap:18px;color:var(--mute);font-size:.88rem;margin-top:8px;align-items:center;}}
.ah-post .meta span{{display:inline-flex;gap:6px;align-items:center;}}
.ah-ver{{color:#3b8f6a;font-size:.78rem;font-weight:600;margin-left:8px;}}
.ah-fine{{color:var(--mute);font-size:.82rem;margin-top:4px;}}

/* ---- relaxer ---- */
.ah-breath{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:26px 0 10px;}}
.ah-orb-wrap{{position:relative;width:260px;height:260px;display:flex;align-items:center;justify-content:center;}}
.ah-orb-ring{{position:absolute;inset:0;border-radius:50%;border:2px dashed #DCCDF0;}}
.ah-orb{{width:170px;height:170px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#D9C4F2,#9B72CB 70%);
 box-shadow:0 0 60px rgba(155,114,203,.45);}}
.ah-phase{{position:absolute;color:#fff;font-weight:700;font-size:1.15rem;opacity:0;text-shadow:0 1px 6px rgba(60,30,100,.35);}}

/* ---- footer ---- */
.ah-footer-gap{{height:34px;}}
.st-key-footer{{border-top:1px solid var(--line);padding-top:18px;}}
.ah-foot-l{{color:var(--ink);font-size:.95rem;}}
.ah-foot-l span{{color:var(--mute);}}
.ah-foot-copy{{color:#9a97a8;font-size:.82rem;margin-top:6px;}}
.ah-disc{{display:flex;gap:12px;align-items:flex-start;max-width:900px;}}
.ah-disc b{{display:block;font-size:1rem;color:var(--ink);margin-bottom:4px;}}
.ah-disc p{{margin:0;color:var(--mute);font-size:.88rem;line-height:1.55;}}

/* ---- translator report box (kept from original) ---- */
.report-box{{white-space:pre-wrap;max-height:520px;overflow:auto;padding:14px 16px;line-height:1.6;font-size:.92rem;background:#fff;
 border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);}}
.report-box mark{{background:#EADCFB;color:#3a1f66;padding:0 3px;border-radius:4px;cursor:help;}}

@media(max-width:900px){{.st-key-hero{{padding:32px 24px;}}.st-key-topbar [data-testid="stRadioGroup"]{{flex-wrap:wrap;}}}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
