# app.py
# FarmGuard AI — Main Streamlit Application
# Merged: teammate UI (farm scene, hero card, animations) +
#         Vanshika functionality (chicken branching, glossary, photo suggestion, report card)
# Run with: streamlit run app.py

import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import io

from dialogue import (
    ANIMALS,
    get_questions_for_animal,
    format_answers_for_prompt,
    maybe_insert_hoof_question,
    CHICKEN_FLOCK_QUESTIONS,
    CHICKEN_SINGLE_BASE_QUESTIONS,
    CHICKEN_RESP_DETAIL,
    CHICKEN_DIGEST_DETAIL,
    CHICKEN_NEURO_DETAIL,
)
from alert import build_mailto_link, simulate_alert

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Farmer's Friend",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Nunito:wght@400;600;700;800&display=swap');

  #MainMenu, footer, header { visibility: hidden; }

  /* ── BASE APP ── */
  .stApp, .stApp p, .stApp div, .stApp span, .stApp label,
  .stMarkdown, .stRadio label, .stMultiSelect label,
  .stRadio div, .stMultiSelect div,
  [data-testid="stMarkdownContainer"],
  [data-testid="stWidgetLabel"] {
    color: #1a1a1a !important;
    font-size: 16px;
  }
  .stRadio > div > label,
  .stRadio > div > label > div,
  .stMultiSelect > div > div,
  div[role="radiogroup"] label,
  div[role="radiogroup"] p {
    color: #1a1a1a !important;
    font-size: 16px !important;
  }
  .stButton > button {
    color: #1a1a1a !important;
    background-color: #ffffff !important;
    border: 1.5px solid #ccc !important;
    border-radius: 10px !important;
    font-size: 16px !important;
    padding: 10px 16px !important;
  }
  .stButton > button:hover {
    border-color: #5a8a3c !important;
    color: #2d4a1e !important;
  }
  .stButton > button[kind="primary"] {
    background-color: #5a8a3c !important;
    color: #ffffff !important;
    border: none !important;
  }
  .stButton > button[kind="secondary"] {
    padding: 4px 14px !important;
    min-height: unset !important;
    font-size: 13px !important;
  }
  .stProgress > div > div { background-color: #5a8a3c !important; }
  .stTextInput input, .stTextArea textarea {
    color: #1a1a1a !important;
    background: white !important;
  }
  .stMultiSelect span { color: #1a1a1a !important; }
  .stSidebar, .stSidebar p, .stSidebar div, .stSidebar label {
    color: #1a1a1a !important;
  }

  /* ── SHARED COMPONENTS ── */
  .question-box {
    background: white;
    border-left: 4px solid #5a8a3c;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 16px;
    color: #1a1a1a !important;
  }
  .type-card {
    background: white;
    border: 2px solid #e0d5c5;
    border-radius: 16px;
    padding: 28px 20px;
    text-align: center;
    transition: all 0.2s;
  }
  .source-tag {
    display: inline-block;
    background: #eef2f7;
    color: #4a5568 !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    margin: 2px;
  }
  .triage-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #e0d5c5;
    margin-top: 16px;
  }

  /* ── HOME: FARM SCENE (teammate's UI) ── */
  .stApp {
    background: linear-gradient(180deg, #87CEEB 0%, #b8e4f7 35%, #c8efc0 60%, #8bc34a 100%) !important;
  }
  .farm-scene {
    position: fixed; top:0; left:0; right:0; bottom:0;
    pointer-events: none; z-index:0; overflow:hidden;
  }
  .sun { position:absolute; top:40px; right:80px; width:70px; height:70px;
    background:radial-gradient(circle,#FFE44D 60%,#FFD700 100%); border-radius:50%;
    box-shadow:0 0 30px 10px rgba(255,228,77,0.4); animation:sunPulse 4s ease-in-out infinite; }
  @keyframes sunPulse {
    0%,100%{box-shadow:0 0 30px 10px rgba(255,228,77,0.4);}
    50%{box-shadow:0 0 50px 20px rgba(255,228,77,0.6);}
  }
  .cloud{position:absolute;background:white;border-radius:50px;opacity:0.88;}
  .cloud::before,.cloud::after{content:'';position:absolute;background:white;border-radius:50%;}
  .cloud-1{width:120px;height:38px;top:60px;left:-140px;animation:cf1 28s linear infinite;}
  .cloud-1::before{width:60px;height:60px;top:-30px;left:15px;}
  .cloud-1::after{width:40px;height:40px;top:-20px;left:55px;}
  .cloud-2{width:90px;height:28px;top:100px;left:-110px;animation:cf2 36s linear infinite 8s;opacity:0.75;}
  .cloud-2::before{width:45px;height:45px;top:-22px;left:10px;}
  .cloud-2::after{width:30px;height:30px;top:-15px;left:40px;}
  .cloud-3{width:150px;height:44px;top:30px;left:-180px;animation:cf3 40s linear infinite 4s;}
  .cloud-3::before{width:70px;height:70px;top:-35px;left:20px;}
  .cloud-3::after{width:50px;height:50px;top:-25px;left:70px;}
  .cloud-4{width:80px;height:24px;top:140px;left:-100px;animation:cf1 32s linear infinite 15s;opacity:0.65;}
  .cloud-4::before{width:38px;height:38px;top:-18px;left:8px;}
  .cloud-4::after{width:28px;height:28px;top:-14px;left:35px;}
  @keyframes cf1{from{left:-140px;}to{left:110%;}}
  @keyframes cf2{from{left:-110px;}to{left:110%;}}
  @keyframes cf3{from{left:-180px;}to{left:110%;}}
  .bird{position:absolute;animation:birdFly linear infinite;opacity:0.85;}
  .bird-1{top:80px;font-size:14px;left:-40px;animation-duration:22s;animation-delay:2s;}
  .bird-2{top:110px;font-size:10px;left:-40px;animation-duration:26s;animation-delay:9s;}
  .bird-3{top:55px;font-size:16px;left:-40px;animation-duration:30s;animation-delay:16s;}
  @keyframes birdFly{
    0%{left:-60px;transform:scaleX(1);}49%{transform:scaleX(1);}
    50%{left:110%;transform:scaleX(-1);}100%{left:-60px;transform:scaleX(-1);}
  }
  .hills{position:absolute;bottom:0;left:0;right:0;height:200px;}
  .hill-back{position:absolute;bottom:80px;left:-5%;right:-5%;height:160px;
    background:#6baa3a;border-radius:50% 50% 0 0/100% 100% 0 0;}
  .hill-front{position:absolute;bottom:0;left:-10%;right:-10%;height:120px;
    background:#7bc142;border-radius:60% 40% 0 0/100% 100% 0 0;}
  .fence-full{position:absolute;bottom:83px;left:0;right:0;height:40px;
    background:repeating-linear-gradient(90deg,#8B6914 0px,#8B6914 10px,transparent 10px,transparent 38px);}
  .fence-full::before{content:'';position:absolute;top:6px;left:0;right:0;height:6px;background:#A0782A;border-radius:3px;}
  .fence-full::after{content:'';position:absolute;top:18px;left:0;right:0;height:6px;background:#A0782A;border-radius:3px;}
  .flower{position:absolute;bottom:100px;font-size:20px;animation:flowerSway 3s ease-in-out infinite;}
  @keyframes flowerSway{0%,100%{transform:rotate(-5deg);}50%{transform:rotate(5deg);}}
  .scarecrow{position:absolute;bottom:108px;right:60px;font-size:52px;
    animation:scarecrowWave 4s ease-in-out infinite;transform-origin:bottom center;
    filter:drop-shadow(2px 2px 4px rgba(0,0,0,0.2));}
  @keyframes scarecrowWave{0%,100%{transform:rotate(-3deg);}25%{transform:rotate(4deg);}75%{transform:rotate(-5deg);}}
  .barn{position:absolute;bottom:103px;left:30px;font-size:72px;
    filter:drop-shadow(3px 3px 6px rgba(0,0,0,0.25));opacity:0.9;}
  .tree{position:absolute;bottom:98px;font-size:52px;filter:drop-shadow(2px 2px 3px rgba(0,0,0,0.15));}
  .walk-animal{position:absolute;bottom:92px;animation:walkAcross linear infinite;
    filter:drop-shadow(1px 1px 2px rgba(0,0,0,0.15));}
  .walk-cow-1{font-size:30px;bottom:90px;animation-duration:18s;animation-delay:0s;}
  .walk-cow-2{font-size:24px;bottom:88px;animation-duration:24s;animation-delay:6s;}
  .walk-chick-1{font-size:20px;bottom:90px;animation-duration:12s;animation-delay:3s;}
  .walk-chick-2{font-size:18px;bottom:89px;animation-duration:15s;animation-delay:9s;}
  .walk-pig{font-size:26px;bottom:90px;animation-duration:20s;animation-delay:11s;}
  .walk-sheep{font-size:24px;bottom:89px;animation-duration:22s;animation-delay:1s;}
  @keyframes walkAcross{
    0%{left:-60px;transform:scaleX(1);}49%{left:110%;transform:scaleX(1);}
    50%{left:110%;transform:scaleX(-1);}99%{left:-60px;transform:scaleX(-1);}
    100%{left:-60px;transform:scaleX(1);}
  }
  .hero-card{
    position:relative;z-index:10;
    background:rgba(255,255,255,0.82);backdrop-filter:blur(12px);
    border-radius:28px;border:2px solid rgba(255,255,255,0.9);
    box-shadow:0 8px 32px rgba(80,120,40,0.18),0 2px 8px rgba(0,0,0,0.08);
    padding:32px 28px 24px;text-align:center;margin-bottom:24px;
    animation:heroEntrance 0.8s cubic-bezier(0.34,1.56,0.64,1) both;
  }
  @keyframes heroEntrance{
    from{opacity:0;transform:translateY(30px) scale(0.95);}
    to{opacity:1;transform:translateY(0) scale(1);}
  }
  .welcome-text{font-family:'Nunito',sans-serif;font-size:15px;font-weight:700;
    color:#5a8a3c;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:4px;}
  .farm-name{font-family:'Fredoka One',cursive;font-size:100px;color:#2d4a1e;
    line-height:1.1;margin:0 0 4px;text-shadow:2px 2px 0 rgba(90,138,60,0.15);}
  .stat-farm-label{font-family:'Nunito',sans-serif;font-size:20px;color:#7a9a6a;
    font-weight:800;margin-bottom:6px;letter-spacing:0.05em;}
  .tagline{font-family:'Nunito',sans-serif;font-size:18px;color:#5a7a45;font-weight:600;margin:0 0 8px;}
  .subtagline{font-family:'Nunito',sans-serif;font-size:13px;color:#7a9a6a;margin:0;}
  div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
    position:relative !important; z-index:10 !important;
    background:rgba(255,255,255,0.88) !important;
    border:2.5px solid rgba(90,138,60,0.2) !important;
    border-radius:20px !important; padding:18px 12px !important;
    width:100% !important; min-height:64px !important;
    transition:all 0.22s cubic-bezier(0.34,1.56,0.64,1) !important;
    box-shadow:0 4px 16px rgba(80,120,40,0.1) !important;
    color:#2d4a1e !important;
    font-family:'Fredoka One',cursive !important;
    font-size:24px !important; font-weight:900 !important;
  }
  div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button p {
    font-family:'Fredoka One',cursive !important;
    font-size:24px !important; font-weight:900 !important; color:#2d4a1e !important;
  }
  div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:first-child > button:hover {
    border-color:#5a8a3c !important;
    background:rgba(240,247,236,0.97) !important;
    transform:translateY(-4px) scale(1.03) !important;
    box-shadow:0 12px 28px rgba(80,120,40,0.22) !important;
  }
  div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:last-child > button:hover {
    border-color:#DAA520 !important;
    background:rgba(255,251,230,0.97) !important;
    transform:translateY(-4px) scale(1.03) !important;
    box-shadow:0 12px 28px rgba(218,165,32,0.22) !important;
  }
  .info-pill{
    position:relative;z-index:10;
    background:rgba(255,255,255,0.75);backdrop-filter:blur(8px);
    border:1.5px solid rgba(90,138,60,0.25);border-radius:16px;padding:12px 18px;
    font-family:'Nunito',sans-serif;font-size:13px;color:#4a6a35;
    text-align:center;margin-top:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "screen": "home",
        "selected_animal": None,
        "chicken_type": None,       # "single" or "flock"
        "current_question": 0,
        "answers": {},
        "questions": [],
        "uploaded_image": None,
        "triage_result": None,
        "vet_email": "vet@example.com",
        "judge_mode": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Helpers ───────────────────────────────────────────────────────────────────

def go_home():
    st.session_state.screen = "home"
    st.session_state.selected_animal = None
    st.session_state.chicken_type = None
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.questions = []
    st.session_state.uploaded_image = None
    st.session_state.triage_result = None
    st.rerun()


SEVERITY_COLORS = {
    "LOW":      ("#155724", "#d4edda"),
    "MEDIUM":   ("#6b4c00", "#fff3cd"),
    "HIGH":     ("#842029", "#f8d7da"),
    "CRITICAL": ("#f8d7da", "#842029"),
}

# ── Chicken question builders ─────────────────────────────────────────────────

def build_chicken_questions(chicken_type: str) -> list:
    if chicken_type == "flock":
        return list(CHICKEN_FLOCK_QUESTIONS)
    else:
        return list(CHICKEN_SINGLE_BASE_QUESTIONS)


def insert_chicken_detail_if_needed(questions: list, answers: dict) -> list:
    existing_ids = {q["id"] for q in questions}
    if (
        "single_resp_detail" not in existing_ids
        and answers.get("single_respiratory") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_respiratory":
                questions.insert(i + 1, CHICKEN_RESP_DETAIL)
                break
    if (
        "single_digest_detail" not in existing_ids
        and answers.get("single_digestive") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_digestive":
                questions.insert(i + 1, CHICKEN_DIGEST_DETAIL)
                break
    if (
        "single_neuro_detail" not in existing_ids
        and answers.get("single_neurological") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_neurological":
                questions.insert(i + 1, CHICKEN_NEURO_DETAIL)
                break
    return questions


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE: TERM GLOSSARY
# ══════════════════════════════════════════════════════════════════════════════

GLOSSARY = {
    "nasal discharge":      "Fluid or mucus coming out of the nose — can be clear, cloudy, or thick/yellow depending on infection severity.",
    "respiratory distress": "Difficulty breathing — signs include fast breathing, open-mouth breathing, gasping, or noisy breath sounds.",
    "respiratory":          "Relating to breathing and the lungs — includes the nose, throat, windpipe, and lungs.",
    "comb":                 "The red fleshy crest on top of a chicken's head. Color changes (pale, purple, dark) often signal illness.",
    "wattle":               "The red fleshy flaps that hang under a chicken's beak. Like the comb, discoloration can indicate disease.",
    "coccidiosis":          "A common intestinal disease in chickens caused by a parasite — symptoms include bloody droppings, weight loss, and lethargy.",
    "neurological":         "Relating to the nervous system (brain and nerves) — neurological signs include tremors, paralysis, circling, and loss of balance.",
    "sinuses":              "Air-filled spaces in the skull around the nose and eyes — swollen sinuses look like puffy areas under the eyes or beside the beak.",
    "paralysis":            "Loss of ability to move a body part — e.g., a chicken unable to move its legs or wings.",
    "tremors":              "Involuntary shaking or quivering of muscles — often a sign of neurological disease.",
    "bloat":                "Buildup of gas in the stomach or rumen, causing visible swelling — most often seen on the left side of cattle.",
    "mastitis":             "Infection of the udder (milk-producing gland) — signs include swelling, heat, pain, and abnormal milk.",
    "ketosis":              "A metabolic condition in dairy cows after calving where the body burns fat too fast — causes sweet-smelling breath, weight loss, and low milk.",
    "lesions":              "Abnormal patches of skin, tissue, or organ — can look like sores, scabs, warts, or discolored areas.",
    "discoloration":        "An unusual change in color — e.g., a comb turning purple/black, or skin becoming pale or yellowish.",
    "gait":                 "The way an animal walks — an abnormal gait means limping, stumbling, or an uneven stride.",
    "udder":                "The milk-producing organ of a cow, hanging between the hind legs — divided into four quarters.",
    "rumen":                "The first and largest stomach chamber in cattle — where fermentation and gas production happens.",
    "foamy eyes":           "Foam or bubbles collecting in or around the eye — a sign of eye infection or respiratory disease in chickens.",
    "dehydration":          "Lack of enough water in the body — signs include sunken eyes, dry mouth, lethargy, and skin that stays 'tented' when pinched.",
}

def render_glossary_expander(question_text: str):
    found = {t: d for t, d in GLOSSARY.items() if t.lower() in question_text.lower()}
    if not found:
        return
    with st.expander("📖 What do these terms mean?"):
        for term, definition in found.items():
            st.markdown(f"""
            <div style="padding:8px 0; border-bottom:1px solid #f0ebe0;">
              <span style="font-weight:700; color:#2d4a1e; font-size:14px;">{term.title()}</span>
              <span style="color:#6b7c61; font-size:14px;"> — {definition}</span>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE: PHOTO SUGGESTION
# ══════════════════════════════════════════════════════════════════════════════

PHOTO_RELEVANT_QUESTION_IDS = {
    "abdomen", "hoof_signs", "digestive_eyes",
    "flock_head_swelling", "flock_comb_color", "flock_neurological",
    "single_resp_detail", "single_digest_detail", "single_neuro_detail",
}

def photo_was_suggested_by_answers(answers: dict) -> tuple:
    triggered_ids = set(answers.keys()) & PHOTO_RELEVANT_QUESTION_IDS
    physical_keywords = [
        "swelling", "swollen", "discolor", "lesion", "wound",
        "bloody", "discharge", "twisted", "paralysis", "tremor",
        "limping", "hoof", "foamy", "bloat"
    ]
    content_triggered = any(
        kw in (v if isinstance(v, str) else " ".join(v)).lower()
        for v in answers.values()
        for kw in physical_keywords
    )
    if triggered_ids or content_triggered:
        reasons = []
        if "abdomen" in triggered_ids or "bloat" in str(answers).lower():
            reasons.append("abdominal swelling")
        if "hoof_signs" in triggered_ids or "limping" in str(answers).lower():
            reasons.append("hoof or leg issues")
        if any(k in triggered_ids for k in ("flock_head_swelling", "flock_comb_color", "single_neuro_detail")):
            reasons.append("visible physical signs on the bird")
        if any(k in triggered_ids for k in ("single_digest_detail", "single_resp_detail")):
            reasons.append("discharge or visible symptoms")
        if "digestive_eyes" in triggered_ids:
            reasons.append("eye or digestive symptoms")
        reason_str = ", ".join(reasons) if reasons else "physical symptoms in your answers"
        return True, reason_str
    return False, ""


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 1: HOME — Farm scene (teammate's UI)
# ═════════════════════════════════════════════════════════════════════════════

def screen_home():
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.session_state.judge_mode = st.toggle("Judge mode (no live API)", value=st.session_state.judge_mode)
        st.session_state.vet_email = st.text_input("Vet email address", value=st.session_state.vet_email)
        st.markdown("---")
        st.markdown("**About Farmer's Friend**")
        st.markdown("RAG-powered livestock triage. Backed by Illinois Extension & USDA docs.")
        if st.session_state.judge_mode:
            st.info("🧪 Judge mode: Uses cached responses, no API key needed.")

    # Farm background scene
    st.markdown("""
    <div class="farm-scene">
      <div class="sun"></div>
      <div class="cloud cloud-1"></div><div class="cloud cloud-2"></div>
      <div class="cloud cloud-3"></div><div class="cloud cloud-4"></div>
      <div class="bird bird-1">🐦</div><div class="bird bird-2">🐦</div><div class="bird bird-3">🐦</div>
      <div class="barn">🏚️</div>
      <div class="tree" style="right:140px;font-size:60px;">🌳</div>
      <div class="tree" style="right:200px;font-size:44px;bottom:91px;">🌲</div>
      <div class="tree" style="left:145px;font-size:38px;">🌳</div>
      <div class="scarecrow">🧑‍🌾</div>
      <div class="flower" style="left:45%;animation-delay:0.3s;">🌻</div>
      <div class="flower" style="left:30%;animation-delay:0.8s;font-size:16px;">🌸</div>
      <div class="flower" style="left:55%;animation-delay:1.4s;font-size:16px;">🌼</div>
      <div class="flower" style="left:22%;animation-delay:0.5s;font-size:14px;">🌺</div>
      <div class="walk-animal walk-cow-1">🐄</div>
      <div class="walk-animal walk-cow-2">🐄</div>
      <div class="walk-animal walk-chick-1">🐔</div>
      <div class="walk-animal walk-chick-2">🐓</div>
      <div class="walk-animal walk-pig">🐖</div>
      <div class="walk-animal walk-sheep">🐑</div>
      <div class="hills"><div class="hill-back"></div><div class="hill-front"></div></div>
      <div class="fence-full"></div>
    </div>
    """, unsafe_allow_html=True)

    # Hero card
    st.markdown("""
    <div class="hero-card">
      <div class="welcome-text">Welcome to</div>
      <div class="farm-name" style="font-size: 50px;">Farmer's Friend</div>
      <div class="stat-farm-label" style="font-size: 20px;">StatFarm</div>
      <div class="tagline">How can we help you today?</div>
      <div class="subtagline">Select an animal below to begin your livestock health check.</div>
    </div>
    """, unsafe_allow_html=True)

    # Animal buttons — teammate's style, Vanshika's routing logic
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🐮  Cattle", key="btn_cow", use_container_width=True):
            st.session_state.selected_animal = "Cow"
            st.session_state.answers = {}
            st.session_state.current_question = 0
            st.session_state.triage_result = None
            st.session_state.uploaded_image = None
            st.session_state.questions = get_questions_for_animal("Cow")
            st.session_state.screen = "dialogue"
            st.rerun()

    with col2:
        if st.button("🐣  Chicken", key="btn_chicken", use_container_width=True):
            st.session_state.selected_animal = "Chicken"
            st.session_state.answers = {}
            st.session_state.current_question = 0
            st.session_state.triage_result = None
            st.session_state.uploaded_image = None
            st.session_state.screen = "chicken_type"
            st.rerun()

    st.markdown("""
    <div class="info-pill">
      Answer a few quick questions, optionally snap a photo, and Farmer's Friend will recommend
      what to do next — backed by agricultural extension knowledge.
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 1b: CHICKEN TYPE SELECTION
# ═════════════════════════════════════════════════════════════════════════════

def screen_chicken_type():
    st.markdown("""
    <div style="text-align:center; padding:16px 0 24px 0;">
      <h2 style="font-weight:800; color:#2d4a1e;">Chicken Health Check</h2>
      <p style="color:#6b7c61; font-size:16px;">Is this about one chicken or a group?</p>
    </div>
    """, unsafe_allow_html=True)

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Back"):
            go_home()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="type-card">
          <div style="font-size:48px; margin-bottom:12px;">🐔</div>
          <div style="font-size:20px; font-weight:700; color:#2d4a1e;">One Chicken</div>
          <div style="color:#6b7c61; font-size:14px; margin-top:8px;">
            Checking a single bird for respiratory, digestive, or neurological issues
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Single chicken", use_container_width=True, key="btn_single"):
            st.session_state.chicken_type = "single"
            st.session_state.answers = {"chicken_count": "Just one chicken"}
            st.session_state.questions = build_chicken_questions("single")
            st.session_state.current_question = 0
            st.session_state.screen = "dialogue"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="type-card">
          <div style="font-size:48px; margin-bottom:12px;">🐔🐔🐔</div>
          <div style="font-size:20px; font-weight:700; color:#2d4a1e;">Multiple Chickens</div>
          <div style="color:#6b7c61; font-size:14px; margin-top:8px;">
            Several or many birds showing symptoms — possible outbreak
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Multiple chickens", use_container_width=True, key="btn_flock"):
            st.session_state.chicken_type = "flock"
            st.session_state.answers = {"chicken_count": "Multiple chickens"}
            st.session_state.questions = build_chicken_questions("flock")
            st.session_state.current_question = 0
            st.session_state.screen = "dialogue"
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 2: DIALOGUE — Guided Symptom Questions
# ═════════════════════════════════════════════════════════════════════════════

def screen_dialogue():
    animal = ANIMALS[st.session_state.selected_animal]
    questions = st.session_state.questions
    q_idx = st.session_state.current_question

    total = len(questions) + 1
    progress = min(q_idx / max(total, 1), 1.0)

    chicken_type_label = ""
    if st.session_state.selected_animal == "Chicken":
        chicken_type_label = " · " + (
            "Single Bird" if st.session_state.chicken_type == "single" else "Flock"
        )

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
      <div>
        <div style="font-weight:700; font-size:20px; color:#2d4a1e;">
          {animal['label']} Health Check{chicken_type_label}
        </div>
        <div style="color:#6b7c61; font-size:14px;">
          Question {min(q_idx+1, total)} of {total}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(progress)

    col_back, _ = st.columns([0.15, 0.5])
    with col_back:
        if st.button("← Back", key="back_btn"):
            if q_idx > 0:
                st.session_state.current_question -= 1
                st.rerun()
            elif st.session_state.selected_animal == "Chicken":
                st.session_state.screen = "chicken_type"
                st.rerun()
            else:
                go_home()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Photo upload step ─────────────────────────────────────────────────────
    if q_idx >= len(questions):
        # Feature: contextual photo suggestion
        should_suggest, reason = photo_was_suggested_by_answers(st.session_state.answers)

        if should_suggest:
            st.markdown(f"""
            <div style="background:#e8f5e0; border:1.5px solid #5a8a3c; border-radius:12px;
                        padding:14px 18px; margin-bottom:16px; display:flex; gap:12px; align-items:flex-start;">
              <span style="font-size:22px; flex-shrink:0;">📸</span>
              <div>
                <div style="font-weight:700; color:#2d4a1e; font-size:15px; margin-bottom:4px;">
                  We recommend adding a photo
                </div>
                <div style="color:#4a6741; font-size:14px;">
                  Based on your answers ({reason}), a photo will help give a much more accurate assessment.
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="question-box">
              <div style="font-size:13px; color:#6b7c61; margin-bottom:4px;">OPTIONAL — but very helpful</div>
              <div style="font-size:18px; font-weight:700; color:#2d4a1e;">📸 Add a photo of the animal</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("A photo helps give a more accurate assessment. Upload if you have one — or skip.")

        uploaded = st.file_uploader(
            "Upload a photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed",
        )
        if uploaded:
            st.session_state.uploaded_image = uploaded.read()
            img = Image.open(io.BytesIO(st.session_state.uploaded_image))
            st.image(img, caption="Photo uploaded ✓", width=300)

        col_skip, col_analyze = st.columns([1, 2])
        with col_skip:
            if st.button("Skip photo →", use_container_width=True):
                st.session_state.uploaded_image = None
                st.session_state.screen = "result"
                st.rerun()
        with col_analyze:
            if st.button("🔍 Analyze now", type="primary", use_container_width=True):
                st.session_state.screen = "result"
                st.rerun()
        return

    # ── Question step ─────────────────────────────────────────────────────────
    q = questions[q_idx]
    photo_hint = q.get("photo_hint", False)

    st.markdown(f"""
    <div class="question-box">
      <div style="font-size:13px; color:#6b7c61; margin-bottom:4px;">QUESTION {q_idx + 1}</div>
      <div style="font-size:18px; font-weight:700; color:#2d4a1e;">{q['question']}</div>
      {"<div style='font-size:13px; color:#5a8a3c; margin-top:6px;'>📸 A photo can help here if you have one</div>" if photo_hint else ""}
    </div>
    """, unsafe_allow_html=True)

    # Feature: glossary
    render_glossary_expander(q["question"])

    # ── Single select ─────────────────────────────────────────────────────────
    if q["type"] == "single":
        answer = st.radio(
            "Select one:", options=q["options"],
            key=f"q_{q_idx}", label_visibility="collapsed",
        )
        if st.button("Next →", type="primary", use_container_width=True, key=f"next_{q_idx}"):
            st.session_state.answers[q["id"]] = answer
            st.session_state.current_question += 1

            if q["id"] == "mobility" and st.session_state.selected_animal == "Cow":
                st.session_state.questions = maybe_insert_hoof_question(
                    st.session_state.questions,
                    st.session_state.answers,
                    st.session_state.current_question - 1,
                )
            if st.session_state.selected_animal == "Chicken" and st.session_state.chicken_type == "single":
                st.session_state.questions = insert_chicken_detail_if_needed(
                    st.session_state.questions,
                    st.session_state.answers,
                )
            st.rerun()

    # ── Multi select ──────────────────────────────────────────────────────────
    elif q["type"] == "multi":
        selected = st.multiselect(
            "Select all that apply:", options=q["options"],
            key=f"q_{q_idx}", label_visibility="collapsed",
        )
        col_none, col_next = st.columns([1, 2])
        with col_none:
            if st.button("None of these", use_container_width=True, key=f"none_{q_idx}"):
                st.session_state.answers[q["id"]] = ["None"]
                st.session_state.current_question += 1
                st.rerun()
        with col_next:
            if st.button("Next →", type="primary", use_container_width=True,
                         disabled=len(selected) == 0, key=f"next_multi_{q_idx}"):
                st.session_state.answers[q["id"]] = selected
                st.session_state.current_question += 1
                st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 3: RESULT — Triage Card
# ═════════════════════════════════════════════════════════════════════════════

JUDGE_MODE_CACHE = {
    "likely_conditions": [
        {"name": "Bovine Respiratory Disease (BRD)", "confidence": "HIGH",
         "explanation": "Labored breathing, nasal discharge, and reduced appetite are classic BRD signs."},
        {"name": "Pneumonia", "confidence": "MEDIUM",
         "explanation": "Could be secondary to BRD or caused by other pathogens."},
        {"name": "Hardware Disease", "confidence": "LOW",
         "explanation": "Less likely but worth noting if bloating is present."},
    ],
    "immediate_actions": [
        "Separate the animal from the herd immediately to prevent spread.",
        "Take the animal's temperature — fever above 104°F (40°C) confirms infection.",
        "Ensure access to fresh water and palatable feed.",
        "Contact your vet if temperature is high or symptoms worsen within 12 hours.",
    ],
    "severity": "HIGH",
    "escalate_to_vet": True,
    "vet_summary": "Farmer reports a cow with labored breathing, nasal discharge, and reduced appetite for 2 days. FarmGuard AI assessment suggests Bovine Respiratory Disease (BRD). Animal has been isolated. Requesting guidance on antibiotic protocol.",
    "cited_sources": ["illinois_extension_cattle_respiratory.pdf", "usda_brd_factsheet.txt"],
    "uncertainty_note": "Cannot confirm causative pathogen without lab testing.",
    "image_observations": "Image shows visible nasal discharge and a slightly hunched posture, consistent with respiratory distress.",
}


def screen_result():
    animal = ANIMALS[st.session_state.selected_animal]

    if st.session_state.triage_result is None:
        if st.session_state.judge_mode:
            import time
            with st.spinner("🔍 Analyzing symptoms..."):
                time.sleep(2)
            st.session_state.triage_result = JUDGE_MODE_CACHE
        else:
            symptom_summary = format_answers_for_prompt(
                st.session_state.selected_animal,
                st.session_state.answers,
            )
            with st.spinner("🔍 Retrieving knowledge and analyzing symptoms..."):
                try:
                    from rag_chain import run_triage
                    result = run_triage(
                        symptom_summary=symptom_summary,
                        image_bytes=st.session_state.uploaded_image,
                    )
                    st.session_state.triage_result = result
                except FileNotFoundError:
                    st.error("⚠️ ChromaDB not found. Run `python ingest.py` first.")
                    if st.button("← Go back"):
                        go_home()
                    return
                except Exception as e:
                    st.error(f"⚠️ Error during analysis: {e}")
                    if st.button("← Try again"):
                        st.session_state.triage_result = None
                        st.rerun()
                    return

    r = st.session_state.triage_result
    severity = r.get("severity", "MEDIUM").upper()
    escalate = r.get("escalate_to_vet", False)
    sev_color, sev_bg = SEVERITY_COLORS.get(severity, ("#333", "#eee"))

    chicken_label = ""
    if st.session_state.selected_animal == "Chicken" and st.session_state.chicken_type:
        chicken_label = f" · {'Single Bird' if st.session_state.chicken_type == 'single' else 'Flock'}"

    # Header
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <div>
        <div style="font-weight:800; font-size:22px; color:#2d4a1e;">Triage Assessment</div>
        <div style="color:#6b7c61; font-size:13px;">{animal['label']}{chicken_label} · AI-assisted recommendation</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Severity banner
    icon = "🚨" if severity in ["HIGH", "CRITICAL"] else "⚠️" if severity == "MEDIUM" else "✅"
    st.markdown(f"""
    <div style="background:{sev_bg}; border:1px solid {sev_color}40; border-radius:12px;
                padding:14px 20px; margin:12px 0; display:flex; align-items:center; gap:12px;">
      <span style="font-size:24px;">{icon}</span>
      <div>
        <div style="font-size:12px; color:{sev_color}; font-weight:600; letter-spacing:0.05em;">SEVERITY LEVEL</div>
        <div style="font-size:20px; font-weight:800; color:{sev_color};">{severity}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Possible conditions
    st.markdown("#### 🩺 Possible Conditions")
    for condition in r.get("likely_conditions", []):
        conf = condition.get("confidence", "?")
        conf_bg   = {"HIGH": "#d4edda", "MEDIUM": "#fff3cd", "LOW": "#f8d7da"}.get(conf, "#eee")
        conf_text = {"HIGH": "#155724", "MEDIUM": "#856404", "LOW": "#842029"}.get(conf, "#333")
        st.markdown(f"""
        <div style="background:white; border:1px solid #e0d5c5; border-radius:10px;
                    padding:12px 16px; margin-bottom:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; color:#2d4a1e; font-size:15px;">{condition['name']}</span>
            <span style="background:{conf_bg}; color:{conf_text}; padding:2px 10px;
                         border-radius:20px; font-size:12px; font-weight:600;">{conf} confidence</span>
          </div>
          <div style="color:#6b7c61; font-size:13px; margin-top:4px;">{condition.get('explanation','')}</div>
        </div>
        """, unsafe_allow_html=True)

    # Immediate actions
    st.markdown("#### ✅ What to do right now")
    for i, action in enumerate(r.get("immediate_actions", []), 1):
        st.markdown(f"""
        <div style="display:flex; gap:12px; align-items:flex-start; padding:8px 0;
                    border-bottom:1px solid #f0ebe0;">
          <span style="background:#5a8a3c; color:white; border-radius:50%; width:24px; height:24px;
                       display:flex; align-items:center; justify-content:center; font-size:12px;
                       font-weight:700; flex-shrink:0; margin-top:2px;">{i}</span>
          <span style="color:#2d4a1e; font-size:14px;">{action}</span>
        </div>
        """, unsafe_allow_html=True)

    # Photo observations
    img_obs = r.get("image_observations", "")
    if img_obs and img_obs != "No image provided" and st.session_state.uploaded_image:
        st.markdown("#### 📸 Photo Analysis")
        col_img, col_obs = st.columns([1, 2])
        with col_img:
            img = Image.open(io.BytesIO(st.session_state.uploaded_image))
            st.image(img, use_column_width=True)
        with col_obs:
            st.markdown(f"""
            <div style="background:#f8f6f0; border-radius:10px; padding:14px; font-size:13px; color:#2d4a1e;">
              {img_obs}
            </div>
            """, unsafe_allow_html=True)

    # Uncertainty
    if r.get("uncertainty_note"):
        st.markdown(f"""
        <div style="background:#f8f6f0; border-left:3px solid #aaa; border-radius:0 8px 8px 0;
                    padding:10px 14px; margin:12px 0; font-size:13px; color:#6b7c61;">
          💭 <strong>Uncertainty:</strong> {r['uncertainty_note']}
        </div>
        """, unsafe_allow_html=True)

    # Sources
    sources = r.get("cited_sources", [])
    if sources:
        st.markdown("#### 📚 Sources used")
        sources_html = " ".join(f'<span class="source-tag">{s}</span>' for s in sources)
        st.markdown(f'<div>{sources_html}</div>', unsafe_allow_html=True)

    # Vet alert
    if escalate or severity in ["HIGH", "CRITICAL"]:
        st.markdown("""
        <div style="background:#fff0f0; border:2px solid #dc3545; border-radius:14px; padding:20px; margin-top:16px;">
          <div style="font-size:18px; font-weight:800; color:#842029; margin-bottom:8px;">
            🚨 Vet Consultation Recommended
          </div>
          <div style="color:#6b2737; font-size:13px;">
            Based on the severity of these symptoms, please contact your veterinarian.
            Click below to send them a pre-filled report.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.judge_mode:
            if st.button("🚨 Alert Vet (Judge Mode — Simulated)", type="primary", use_container_width=True):
                sim = simulate_alert(animal["label"], severity, r.get("vet_summary", ""))
                st.success(f"✅ {sim['message']}")
                st.code(sim["preview"])
        else:
            mailto_link = build_mailto_link(
                vet_email=st.session_state.vet_email,
                animal_type=animal["label"],
                severity=severity,
                vet_summary=r.get("vet_summary", ""),
                conditions=r.get("likely_conditions", []),
                answers=st.session_state.answers,
                chicken_type=st.session_state.get("chicken_type"),
            )
            st.markdown(f"""
            <a href="{mailto_link}" style="display:block; background:#dc3545; color:white;
               text-align:center; padding:14px; border-radius:10px; font-weight:700;
               font-size:16px; text-decoration:none; margin-bottom:12px;">
              🚨 Alert Your Vet (Opens Email)
            </a>
            """, unsafe_allow_html=True)
            with st.expander("👁️ Preview vet message"):
                st.text_area("Message preview:", value=r.get("vet_summary", ""), height=150, disabled=True)

        # ── Feature: Farm Incident Report ────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)

        animal_label = animal["label"]
        chicken_report_label = ""
        if st.session_state.selected_animal == "Chicken" and st.session_state.chicken_type:
            chicken_report_label = f" ({'Single Bird' if st.session_state.chicken_type == 'single' else 'Flock'})"

        answers = st.session_state.answers
        symptom_lines = []
        for key, val in answers.items():
            if key == "chicken_count":
                continue
            label = key.replace("_", " ").replace("flock ", "").replace("single ", "").title()
            display = ", ".join(val) if isinstance(val, list) else val
            if display and display not in ("None", "None of these"):
                symptom_lines.append(f"<li><strong>{label}:</strong> {display}</li>")

        conditions_html = "".join(
            f"<li>{c['name']} <span style='color:#6b7c61;font-size:13px;'>({c.get('confidence','?')} confidence)</span></li>"
            for c in r.get("likely_conditions", [])
        )
        symptoms_html = "".join(symptom_lines) if symptom_lines else "<li>No specific symptoms recorded</li>"

        import datetime
        report_date = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")

        st.markdown(f"""
        <div style="background:white; border:1.5px solid #e0d5c5; border-radius:14px;
                    padding:22px 24px; margin-top:8px;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
            <div>
              <div style="font-size:17px; font-weight:800; color:#2d4a1e;">Farm Incident Report</div>
              <div style="color:#6b7c61; font-size:13px; margin-top:2px;">
                Generated by FarmGuard AI · {report_date}
              </div>
            </div>
            <div style="background:{sev_bg}; color:{sev_color}; padding:4px 14px;
                        border-radius:20px; font-size:13px; font-weight:700;">{severity}</div>
          </div>
          <div style="border-top:1px solid #f0ebe0; padding-top:14px; margin-bottom:14px;">
            <div style="font-size:13px; font-weight:700; color:#6b7c61; letter-spacing:0.05em; margin-bottom:8px;">ANIMAL</div>
            <div style="color:#2d4a1e; font-size:15px;">{animal_label}{chicken_report_label}</div>
          </div>
          <div style="border-top:1px solid #f0ebe0; padding-top:14px; margin-bottom:14px;">
            <div style="font-size:13px; font-weight:700; color:#6b7c61; letter-spacing:0.05em; margin-bottom:8px;">SYMPTOMS REPORTED</div>
            <ul style="margin:0; padding-left:18px; color:#2d4a1e; font-size:14px; line-height:1.8;">{symptoms_html}</ul>
          </div>
          <div style="border-top:1px solid #f0ebe0; padding-top:14px; margin-bottom:14px;">
            <div style="font-size:13px; font-weight:700; color:#6b7c61; letter-spacing:0.05em; margin-bottom:8px;">POSSIBLE CONDITIONS</div>
            <ul style="margin:0; padding-left:18px; color:#2d4a1e; font-size:14px; line-height:1.8;">{conditions_html}</ul>
          </div>
          <div style="border-top:1px solid #f0ebe0; padding-top:14px;">
            <div style="font-size:13px; font-weight:700; color:#6b7c61; letter-spacing:0.05em; margin-bottom:8px;">VET SUMMARY</div>
            <div style="color:#2d4a1e; font-size:14px; line-height:1.7; background:#f8f6f0; border-radius:8px; padding:12px 14px;">
              {r.get("vet_summary", "No summary available.")}
            </div>
          </div>
          <div style="margin-top:16px; color:#9aaa91; font-size:12px; text-align:center;">
            This report was auto-generated and is not a substitute for professional veterinary diagnosis.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Check another animal", use_container_width=True):
            go_home()
    with col2:
        if st.button("📋 New check (same animal)", use_container_width=True):
            if st.session_state.selected_animal == "Chicken":
                st.session_state.screen = "chicken_type"
            else:
                st.session_state.questions = get_questions_for_animal(st.session_state.selected_animal)
                st.session_state.screen = "dialogue"
            st.session_state.answers = {}
            st.session_state.current_question = 0
            st.session_state.triage_result = None
            st.session_state.uploaded_image = None
            st.rerun()

    if st.session_state.judge_mode:
        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#999; font-size:12px;">
          🧪 Judge mode active — responses use cached demo data
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════

screen = st.session_state.get("screen", "home")

if screen == "home":
    screen_home()
elif screen == "chicken_type":
    screen_chicken_type()
elif screen == "dialogue":
    screen_dialogue()
elif screen == "result":
    screen_result()