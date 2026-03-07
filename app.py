# app.py
# FarmGuard AI — Main Streamlit Application
# Run with: streamlit run app.py

import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import io

from dialogue import ANIMALS, get_questions_for_animal, format_answers_for_prompt
from alert import build_mailto_link, simulate_alert

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="FarmGuard AI",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  /* Main background */
  .stApp { background-color: #f5f0e8; }
  
  /* Hide default streamlit menu/footer */
  #MainMenu, footer, header { visibility: hidden; }
  
  /* Force ALL text black */
  .stApp, .stApp p, .stApp div, .stApp span, .stApp label,
  .stMarkdown, .stRadio label, .stMultiSelect label,
  .stRadio div, .stMultiSelect div,
  [data-testid="stMarkdownContainer"],
  [data-testid="stWidgetLabel"] {
    color: #1a1a1a !important;
  }
  
  /* Radio and multiselect option text */
  .stRadio > div > label,
  .stRadio > div > label > div,
  .stMultiSelect > div > div,
  div[role="radiogroup"] label,
  div[role="radiogroup"] p {
    color: #1a1a1a !important;
  }

  /* Button text */
  .stButton > button {
    color: #1a1a1a !important;
    background-color: #ffffff !important;
    border: 1.5px solid #ccc !important;
    border-radius: 10px !important;
  }
  /* Back button — small and compact */
  .stButton > button[kind="secondary"] {
    padding: 4px 14px !important;
    min-height: unset !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
  }

  .stButton > button:hover {
    border-color: #5a8a3c !important;
    color: #2d4a1e !important;
  }

  /* Primary button stays green */
  .stButton > button[kind="primary"] {
    background-color: #5a8a3c !important;
    color: #ffffff !important;
    border: none !important;
  }

  /* Progress bar */
  .stProgress > div > div {
    background-color: #5a8a3c !important;
  }

  /* Input fields */
  .stTextInput input, .stTextArea textarea {
    color: #1a1a1a !important;
    background: white !important;
  }

  /* Multiselect tags */
  .stMultiSelect span {
    color: #1a1a1a !important;
  }

  /* Animal cards */
  .animal-card {
    background: white;
    border: 2px solid #e0d5c5;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 8px;
  }
  .animal-card:hover { border-color: #5a8a3c; background: #f0f7ec; }
  .animal-card.selected { border-color: #5a8a3c; background: #e8f5e0; }
  
  /* Triage card */
  .triage-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #e0d5c5;
    margin-top: 16px;
  }
  
  /* Source citation */
  .source-tag {
    display: inline-block;
    background: #eef2f7;
    color: #4a5568 !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    margin: 2px;
  }
  
  /* Question box */
  .question-box {
    background: white;
    border-left: 4px solid #5a8a3c;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 16px;
    color: #1a1a1a !important;
  }

  /* Sidebar text */
  .stSidebar, .stSidebar p, .stSidebar div, .stSidebar label {
    color: #1a1a1a !important;
  }




</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "screen": "home",           # home → dialogue → result
        "selected_animal": None,
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

# ── Helper: reset to home ─────────────────────────────────────────────────────

def go_home():
    for key in ["screen", "selected_animal", "current_question", "answers",
                "questions", "uploaded_image", "triage_result"]:
        st.session_state[key] = None if key not in ["screen", "current_question", "answers", "questions"] else \
                                 ("home" if key == "screen" else 0 if key == "current_question" else {} if key == "answers" else [])
    st.rerun()

# ── Severity color helper ─────────────────────────────────────────────────────

SEVERITY_COLORS = {
    "LOW": ("#155724", "#d4edda"),
    "MEDIUM": ("#856404", "#fff3cd"),
    "HIGH": ("#842029", "#f8d7da"),
    "CRITICAL": ("#ffffff", "#842029"),
}

def severity_badge(level: str) -> str:
    level = level.upper()
    color, bg = SEVERITY_COLORS.get(level, ("#333", "#eee"))
    return f'<span style="background:{bg};color:{color};padding:4px 14px;border-radius:20px;font-weight:700;font-size:14px;">{level}</span>'

# ── Helper: navigate to animal dialogue ──────────────────────────────────────

def select_animal(animal_key: str):
    st.session_state.selected_animal = animal_key
    st.session_state.questions = get_questions_for_animal(animal_key)
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.screen = "dialogue"

# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 1: HOME — Animal Selection
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

    # ── Full page farm CSS + background scene ────────────────────────────────
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Nunito:wght@400;600;700;800&display=swap');
      #MainMenu, footer, header { visibility: hidden; }

      .stApp {
        background: linear-gradient(180deg, #87CEEB 0%, #b8e4f7 35%, #c8efc0 60%, #8bc34a 100%) !important;
      }
      .farm-scene {
        position: fixed; top:0; left:0; right:0; bottom:0;
        pointer-events: none; z-index:0; overflow:hidden;
      }
      /* SUN */
      .sun { position:absolute; top:40px; right:80px; width:70px; height:70px;
        background:radial-gradient(circle,#FFE44D 60%,#FFD700 100%); border-radius:50%;
        box-shadow:0 0 30px 10px rgba(255,228,77,0.4); animation:sunPulse 4s ease-in-out infinite; }
      @keyframes sunPulse {
        0%,100%{box-shadow:0 0 30px 10px rgba(255,228,77,0.4);}
        50%{box-shadow:0 0 50px 20px rgba(255,228,77,0.6);}
      }
      /* CLOUDS */
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
      /* BIRDS */
      .bird{position:absolute;animation:birdFly linear infinite;opacity:0.85;}
      .bird-1{top:80px;font-size:14px;left:-40px;animation-duration:22s;animation-delay:2s;}
      .bird-2{top:110px;font-size:10px;left:-40px;animation-duration:26s;animation-delay:9s;}
      .bird-3{top:55px;font-size:16px;left:-40px;animation-duration:30s;animation-delay:16s;}
      @keyframes birdFly{
        0%{left:-60px;transform:scaleX(1);}49%{transform:scaleX(1);}
        50%{left:110%;transform:scaleX(-1);}100%{left:-60px;transform:scaleX(-1);}
      }
      /* HILLS */
      .hills{position:absolute;bottom:0;left:0;right:0;height:200px;}
      .hill-back{position:absolute;bottom:80px;left:-5%;right:-5%;height:160px;
        background:#6baa3a;border-radius:50% 50% 0 0/100% 100% 0 0;}
      .hill-front{position:absolute;bottom:0;left:-10%;right:-10%;height:120px;
        background:#7bc142;border-radius:60% 40% 0 0/100% 100% 0 0;}
      /* FENCE */
      .fence-full{position:absolute;bottom:83px;left:0;right:0;height:40px;
        background:repeating-linear-gradient(90deg,#8B6914 0px,#8B6914 10px,transparent 10px,transparent 38px);}
      .fence-full::before{content:'';position:absolute;top:6px;left:0;right:0;height:6px;background:#A0782A;border-radius:3px;}
      .fence-full::after{content:'';position:absolute;top:18px;left:0;right:0;height:6px;background:#A0782A;border-radius:3px;}
      /* FLOWERS */
      .flower{position:absolute;bottom:100px;font-size:20px;animation:flowerSway 3s ease-in-out infinite;}
      @keyframes flowerSway{0%,100%{transform:rotate(-5deg);}50%{transform:rotate(5deg);}}
      /* SCARECROW */
      .scarecrow{position:absolute;bottom:108px;right:60px;font-size:52px;
        animation:scarecrowWave 4s ease-in-out infinite;transform-origin:bottom center;
        filter:drop-shadow(2px 2px 4px rgba(0,0,0,0.2));}
      @keyframes scarecrowWave{0%,100%{transform:rotate(-3deg);}25%{transform:rotate(4deg);}75%{transform:rotate(-5deg);}}
      /* BARN & TREES */
      .barn{position:absolute;bottom:103px;left:30px;font-size:72px;
        filter:drop-shadow(3px 3px 6px rgba(0,0,0,0.25));opacity:0.9;}
      .tree{position:absolute;bottom:98px;font-size:52px;filter:drop-shadow(2px 2px 3px rgba(0,0,0,0.15));}
      /* WALKING ANIMALS */
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

      /* ── HERO CARD ── */
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
      .farm-name{font-family:'Fredoka One',cursive;font-size:48px;color:#2d4a1e;
        line-height:1.1;margin:0 0 4px;text-shadow:2px 2px 0 rgba(90,138,60,0.15);}
      .stat-farm-label{font-family:'Nunito',sans-serif;font-size:20px;color:#7a9a6a;
        font-weight:800;margin-bottom:6px;letter-spacing:0.05em;}
      .tagline{font-family:'Nunito',sans-serif;font-size:18px;color:#5a7a45;font-weight:600;margin:0 0 8px;}
      .subtagline{font-family:'Nunito',sans-serif;font-size:13px;color:#7a9a6a;margin:0;}

      /* ── SECTION LABEL ── */
      .animal-buttons-label{font-family:'Nunito',sans-serif;font-size:16px;font-weight:800;
        color:#2d4a1e;text-align:center;margin:0 0 12px;position:relative;z-index:10;}

      /* ── NATIVE ANIMAL CARD BUTTONS ── */
      div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
        position: relative !important;
        z-index: 10 !important;
        background: rgba(255,255,255,0.88) !important;
        border: 2.5px solid rgba(90,138,60,0.2) !important;
        border-radius: 20px !important;
        padding: 18px 12px !important;
        width: 100% !important;
        min-height: 64px !important;
        cursor: pointer !important;
        transition: all 0.22s cubic-bezier(0.34,1.56,0.64,1) !important;
        box-shadow: 0 4px 16px rgba(80,120,40,0.1) !important;
        color: #2d4a1e !important;
        font-family: 'Fredoka One', cursive !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        line-height: 1.2 !important;
      }
      /* Target inner <p> that Streamlit injects — this is what actually renders the text */
      div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button p {
        font-family: 'Fredoka One', cursive !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        color: #2d4a1e !important;
      }
      div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:first-child > button:hover {
        border-color: #5a8a3c !important;
        background: rgba(240,247,236,0.97) !important;
        transform: translateY(-4px) scale(1.03) !important;
        box-shadow: 0 12px 28px rgba(80,120,40,0.22) !important;
      }
      div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:last-child > button:hover {
        border-color: #DAA520 !important;
        background: rgba(255,251,230,0.97) !important;
        transform: translateY(-4px) scale(1.03) !important;
        box-shadow: 0 12px 28px rgba(218,165,32,0.22) !important;
      }

      /* Info pill */
      .info-pill{
        position:relative;z-index:10;
        background:rgba(255,255,255,0.75);backdrop-filter:blur(8px);
        border:1.5px solid rgba(90,138,60,0.25);border-radius:16px;padding:12px 18px;
        font-family:'Nunito',sans-serif;font-size:13px;color:#4a6a35;
        text-align:center;margin-top:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);
      }
    </style>

    <!-- FARM BACKGROUND -->
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

    # ── Hero Card ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-card">
      <div class="welcome-text">Welcome to</div>
      <div class="farm-name">Farmer's Friend</div>
      <div class="stat-farm-label">StatFarm</div>
      <div class="tagline">How can we help you today?</div>
      <div class="subtagline">Select an animal below to begin your livestock health check.</div>
    </div>
    """, unsafe_allow_html=True)

    # st.markdown('<div class="animal-buttons-label">Who needs attention?</div>', unsafe_allow_html=True)

    # ── Native Streamlit buttons styled as animal cards ───────────────────────
    # These replace the previous components.html iframe — same visual style,
    # but now they correctly trigger session state changes and st.rerun().
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🐮  Cattle",
            key="btn_cow",
            use_container_width=True,
        ):
            select_animal("🐄 Cow")
            st.rerun()

    with col2:
        if st.button(
            "🐣  Chicken",
            key="btn_chicken",
            use_container_width=True,
        ):
            select_animal("🐔 Chicken")
            st.rerun()

    st.markdown("""
    <div class="info-pill">
      Answer a few quick questions, optionally snap a photo, and Farmer's Friend will recommend
      what to do next — backed by agricultural extension knowledge.
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 2: DIALOGUE — Guided Symptom Questions
# ═════════════════════════════════════════════════════════════════════════════

def screen_dialogue():
    animal = ANIMALS[st.session_state.selected_animal]
    questions = st.session_state.questions
    q_idx = st.session_state.current_question
    
    # Progress
    total = len(questions) + 1  # +1 for photo step
    progress = q_idx / total
    
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
      <span style="font-size:32px;">{animal['emoji']}</span>
      <div>
        <div style="font-weight:700; font-size:18px; color:#2d4a1e;">{animal['label']} Health Check</div>
        <div style="color:#6b7c61; font-size:13px;">Step {min(q_idx+1, total)} of {total}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress)
    
    # Back button — rendered in a narrow column so it stays small
    col_back, _ = st.columns([0.15, 0.85])
    with col_back:
        if st.button("← Back", key="back_btn"):
            if q_idx > 0:
                st.session_state.current_question -= 1
                st.rerun()
            else:
                go_home()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Photo upload step (last step before submit) ───────────────────────────
    if q_idx == len(questions):
        st.markdown("""
        <div class="question-box">
          <div style="font-size:13px; color:#6b7c61; margin-bottom:4px;">OPTIONAL — but very helpful</div>
          <div style="font-size:18px; font-weight:700; color:#2d4a1e;">📸 Add a photo of the animal</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("A photo helps FarmGuard give a more accurate assessment. Upload if you have one — or skip.")
        
        uploaded = st.file_uploader(
            "Upload a photo",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
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
    
    # ── Symptom question step ─────────────────────────────────────────────────
    q = questions[q_idx]
    
    st.markdown(f"""
    <div class="question-box">
      <div style="font-size:13px; color:#6b7c61; margin-bottom:4px;">QUESTION {q_idx + 1}</div>
      <div style="font-size:18px; font-weight:700; color:#2d4a1e;">{q['question']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    answer = None
    
    if q["type"] == "single":
        answer = st.radio(
            "Select one:",
            options=q["options"],
            key=f"q_{q_idx}",
            label_visibility="collapsed",
        )
        
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.answers[q["id"]] = answer
            st.session_state.current_question += 1
            st.rerun()
    
    elif q["type"] == "multi":
        selected = st.multiselect(
            "Select all that apply:",
            options=q["options"],
            key=f"q_{q_idx}",
            label_visibility="collapsed",
        )
        
        col_none, col_next = st.columns([1, 2])
        with col_none:
            if st.button("None of these", use_container_width=True):
                st.session_state.answers[q["id"]] = ["None"]
                st.session_state.current_question += 1
                st.rerun()
        with col_next:
            if st.button("Next →", type="primary", use_container_width=True, disabled=len(selected) == 0):
                st.session_state.answers[q["id"]] = selected
                st.session_state.current_question += 1
                st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 3: RESULT — Triage Card
# ═════════════════════════════════════════════════════════════════════════════

JUDGE_MODE_CACHE = {
    "likely_conditions": [
        {"name": "Bovine Respiratory Disease (BRD)", "confidence": "HIGH", "explanation": "Labored breathing, nasal discharge, and reduced appetite are classic BRD signs."},
        {"name": "Pneumonia", "confidence": "MEDIUM", "explanation": "Could be secondary to BRD or caused by other pathogens."},
        {"name": "Hardware Disease", "confidence": "LOW", "explanation": "Less likely but worth noting if bloating is present."},
    ],
    "immediate_actions": [
        "Separate the animal from the herd immediately to prevent spread.",
        "Take the animal's temperature — fever above 104°F (40°C) confirms infection.",
        "Ensure access to fresh water and palatable feed.",
        "Contact your vet if temperature is high or symptoms worsen within 12 hours.",
    ],
    "severity": "HIGH",
    "escalate_to_vet": True,
    "vet_summary": "Farmer reports a cow with labored breathing, nasal discharge, and reduced appetite for 2 days. Multiple animals may be affected. FarmGuard AI assessment suggests Bovine Respiratory Disease (BRD) as the most likely condition. Animal has been isolated. Requesting guidance on antibiotic protocol and whether a farm visit is warranted.",
    "cited_sources": ["illinois_extension_cattle_respiratory.pdf", "usda_brd_factsheet.txt"],
    "uncertainty_note": "Cannot confirm causative pathogen without lab testing. Severity may be higher if other animals show symptoms.",
    "image_observations": "Image shows visible nasal discharge and the animal appears to have a slightly hunched posture, consistent with respiratory distress.",
}


def screen_result():
    animal = ANIMALS[st.session_state.selected_animal]
    
    # Run triage if not already done
    if st.session_state.triage_result is None:
        if st.session_state.judge_mode:
            import time
            with st.spinner("🔍 Analyzing symptoms..."):
                time.sleep(2)  # simulate API call in judge mode
            st.session_state.triage_result = JUDGE_MODE_CACHE
        else:
            # Build symptom summary from answers
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
    
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <span style="font-size:36px;">{animal['emoji']}</span>
      <div>
        <div style="font-weight:800; font-size:22px; color:#2d4a1e;">Triage Assessment</div>
        <div style="color:#6b7c61; font-size:13px;">{animal['label']} · AI-assisted recommendation</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Severity banner
    sev_color, sev_bg = SEVERITY_COLORS.get(severity, ("#333", "#eee"))
    st.markdown(f"""
    <div style="background:{sev_bg}; border:1px solid {sev_color}40; border-radius:12px; 
                padding:14px 20px; margin:12px 0; display:flex; align-items:center; gap:12px;">
      <span style="font-size:24px;">{"🚨" if severity in ["HIGH","CRITICAL"] else "⚠️" if severity == "MEDIUM" else "✅"}</span>
      <div>
        <div style="font-size:12px; color:{sev_color}; font-weight:600; letter-spacing:0.05em;">SEVERITY LEVEL</div>
        <div style="font-size:20px; font-weight:800; color:{sev_color};">{severity}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Likely conditions ─────────────────────────────────────────────────────
    st.markdown("#### 🩺 Possible Conditions")
    
    for condition in r.get("likely_conditions", []):
        conf = condition.get("confidence", "?")
        conf_colors = {"HIGH": "#d4edda", "MEDIUM": "#fff3cd", "LOW": "#f8d7da"}
        conf_text_colors = {"HIGH": "#155724", "MEDIUM": "#856404", "LOW": "#842029"}
        bg = conf_colors.get(conf, "#eee")
        tc = conf_text_colors.get(conf, "#333")
        
        st.markdown(f"""
        <div style="background:white; border:1px solid #e0d5c5; border-radius:10px; 
                    padding:12px 16px; margin-bottom:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; color:#2d4a1e; font-size:15px;">{condition['name']}</span>
            <span style="background:{bg}; color:{tc}; padding:2px 10px; border-radius:20px; 
                         font-size:12px; font-weight:600;">{conf} confidence</span>
          </div>
          <div style="color:#6b7c61; font-size:13px; margin-top:4px;">{condition.get('explanation','')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ── Immediate actions ─────────────────────────────────────────────────────
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
    
    # ── Image observations (if photo was uploaded) ────────────────────────────
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
    
    # ── Uncertainty note ──────────────────────────────────────────────────────
    if r.get("uncertainty_note"):
        st.markdown(f"""
        <div style="background:#f8f6f0; border-left:3px solid #aaa; border-radius:0 8px 8px 0;
                    padding:10px 14px; margin:12px 0; font-size:13px; color:#6b7c61;">
          💭 <strong>Uncertainty:</strong> {r['uncertainty_note']}
        </div>
        """, unsafe_allow_html=True)
    
    # ── Sources ───────────────────────────────────────────────────────────────
    sources = r.get("cited_sources", [])
    if sources:
        st.markdown("#### 📚 Sources used")
        sources_html = " ".join(f'<span class="source-tag">{s}</span>' for s in sources)
        st.markdown(f'<div>{sources_html}</div>', unsafe_allow_html=True)
    
    # ── VET ALERT SECTION ─────────────────────────────────────────────────────
    if escalate or severity in ["HIGH", "CRITICAL"]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#fff0f0; border:2px solid #dc3545; border-radius:14px; padding:20px;">
          <div style="font-size:18px; font-weight:800; color:#842029; margin-bottom:8px;">
            🚨 Vet Consultation Recommended
          </div>
          <div style="color:#6b2737; font-size:13px; margin-bottom:16px;">
            Based on the severity of these symptoms, FarmGuard recommends contacting your veterinarian.
            Click below to send them a pre-filled summary.
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.judge_mode:
            # Judge mode: show simulated alert
            if st.button("🚨 Alert Vet (Judge Mode — Simulated)", type="primary", use_container_width=True):
                sim = simulate_alert(animal["label"], severity, r.get("vet_summary", ""))
                st.success(f"✅ {sim['message']}")
                st.code(sim["preview"])
        else:
            # Real mode: build mailto link
            mailto_link = build_mailto_link(
                vet_email=st.session_state.vet_email,
                animal_type=animal["label"],
                severity=severity,
                vet_summary=r.get("vet_summary", ""),
                conditions=r.get("likely_conditions", []),
            )
            st.markdown(f"""
            <a href="{mailto_link}" style="display:block; background:#dc3545; color:black; 
               text-align:center; padding:14px; border-radius:10px; font-weight:700; 
               font-size:16px; text-decoration:none; margin-bottom:12px;">
              🚨 Alert Your Vet (Opens Email)
            </a>
            """, unsafe_allow_html=True)
            
            with st.expander("👁️ Preview vet message"):
                st.text_area("Message preview:", value=r.get("vet_summary", ""), height=150, disabled=True)
    
    # ── Navigation ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Check another animal", use_container_width=True):
            go_home()
    with col2:
        if st.button("📋 New check (same animal)", use_container_width=True):
            st.session_state.answers = {}
            st.session_state.current_question = 0
            st.session_state.triage_result = None
            st.session_state.uploaded_image = None
            st.session_state.questions = get_questions_for_animal(st.session_state.selected_animal)
            st.session_state.screen = "dialogue"
            st.rerun()
    
    # Judge mode badge
    if st.session_state.judge_mode:
        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#999; font-size:12px;">
          🧪 Judge mode active — responses use cached demo data
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════

screen = st.session_state.screen

if screen == "home":
    screen_home()
elif screen == "dialogue":
    screen_dialogue()
elif screen == "result":
    screen_result()