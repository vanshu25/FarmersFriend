# app.py
# FarmGuard AI — Main Streamlit Application
# Run with: streamlit run app.py

import os
import streamlit as st
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
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  .stApp { background-color: #f5f0e8; }
  #MainMenu, footer, header { visibility: hidden; }

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

  .stProgress > div > div { background-color: #5a8a3c !important; }

  .stTextInput input, .stTextArea textarea {
    color: #1a1a1a !important;
    background: white !important;
  }

  .stMultiSelect span { color: #1a1a1a !important; }

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

  .stSidebar, .stSidebar p, .stSidebar div, .stSidebar label {
    color: #1a1a1a !important;
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

# ── Build chicken question list from type ─────────────────────────────────────

def build_chicken_questions(chicken_type: str) -> list:
    """
    Returns a flat list of questions for the chosen chicken type.
    For single birds, all questions are included upfront —
    conditional detail questions are inserted dynamically during dialogue.
    """
    if chicken_type == "flock":
        return list(CHICKEN_FLOCK_QUESTIONS)
    else:
        return list(CHICKEN_SINGLE_BASE_QUESTIONS)


def insert_chicken_detail_if_needed(questions: list, answers: dict) -> list:
    """
    After each single-bird answer is recorded, insert detail follow-up
    questions if the farmer said Yes or Not sure. Safe to call repeatedly.
    """
    existing_ids = {q["id"] for q in questions}

    # Respiratory detail — after single_respiratory
    if (
        "single_resp_detail" not in existing_ids
        and answers.get("single_respiratory") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_respiratory":
                questions.insert(i + 1, CHICKEN_RESP_DETAIL)
                break

    # Digestive detail — after single_digestive
    if (
        "single_digest_detail" not in existing_ids
        and answers.get("single_digestive") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_digestive":
                questions.insert(i + 1, CHICKEN_DIGEST_DETAIL)
                break

    # Neurological detail — after single_neurological
    if (
        "single_neuro_detail" not in existing_ids
        and answers.get("single_neurological") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_neurological":
                questions.insert(i + 1, CHICKEN_NEURO_DETAIL)
                break

    return questions


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 1: HOME
# ═════════════════════════════════════════════════════════════════════════════

def screen_home():
    st.markdown("""
    <div style="text-align:center; padding:20px 0 8px 0;">
      <h1 style="font-size:32px; font-weight:800; color:#2d4a1e; margin:0;">Farmer's Friend</h1>
      <p style="color:#6b7c61; font-size:16px; margin-top:6px;">
        Livestock health guidance — tap your animal to get started
      </p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### Settings")
        st.session_state.judge_mode = st.toggle(
            "Judge mode (no live API)", value=st.session_state.judge_mode
        )
        st.session_state.vet_email = st.text_input(
            "Vet email address", value=st.session_state.vet_email
        )
        st.markdown("---")
        st.markdown("RAG-powered livestock triage. Backed by Illinois Extension & USDA docs.")
        if st.session_state.judge_mode:
            st.info("Judge mode: Uses cached responses, no API key needed.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Which animal needs attention?")

    col1, col2 = st.columns(2)
    animal_keys = list(ANIMALS.keys())

    for i, animal_key in enumerate(animal_keys):
        animal = ANIMALS[animal_key]
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(
                f"**{animal['label']}**\n\n_{animal['description']}_",
                key=f"animal_{i}",
                use_container_width=True,
            ):
                st.session_state.selected_animal = animal_key
                st.session_state.answers = {}
                st.session_state.current_question = 0
                st.session_state.triage_result = None
                st.session_state.uploaded_image = None

                if animal_key == "Chicken":
                    # Chicken goes to type selection screen first
                    st.session_state.screen = "chicken_type"
                else:
                    # All other animals go straight to dialogue
                    st.session_state.questions = get_questions_for_animal(animal_key)
                    st.session_state.screen = "dialogue"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("Answer a few quick questions, optionally add a photo, and get evidence-backed guidance.")


# ═════════════════════════════════════════════════════════════════════════════
# SCREEN 1b: CHICKEN TYPE SELECTION (single vs flock)
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

    total = len(questions) + 1  # +1 for photo step
    progress = min(q_idx / max(total, 1), 1.0)

    # Header
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

    # Back button
    col_back, _ = st.columns([1, 4])
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
        st.markdown("""
        <div class="question-box">
          <div style="font-size:13px; color:#6b7c61; margin-bottom:4px;">OPTIONAL — but very helpful</div>
          <div style="font-size:18px; font-weight:700; color:#2d4a1e;">Add a photo of the animal</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("A photo helps give a more accurate assessment. Upload if you have one — or skip.")

        uploaded = st.file_uploader(
            "Upload a photo",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )

        if uploaded:
            st.session_state.uploaded_image = uploaded.read()
            img = Image.open(io.BytesIO(st.session_state.uploaded_image))
            st.image(img, caption="Photo uploaded", width=300)

        col_skip, col_analyze = st.columns([1, 2])
        with col_skip:
            if st.button("Skip photo", use_container_width=True):
                st.session_state.uploaded_image = None
                st.session_state.screen = "result"
                st.rerun()
        with col_analyze:
            if st.button("Analyze now", type="primary", use_container_width=True):
                st.session_state.screen = "result"
                st.rerun()
        return

    # ── Question step ─────────────────────────────────────────────────────────
    q = questions[q_idx]

    # Photo hint for relevant chicken questions
    photo_hint = q.get("photo_hint", False)

    st.markdown(f"""
    <div class="question-box">
      <div style="font-size:13px; color:#6b7c61; margin-bottom:4px;">QUESTION {q_idx + 1}</div>
      <div style="font-size:18px; font-weight:700; color:#2d4a1e;">{q['question']}</div>
      {"<div style='font-size:13px; color:#5a8a3c; margin-top:6px;'>📸 A photo can help here if you have one</div>" if photo_hint else ""}
    </div>
    """, unsafe_allow_html=True)

    # ── Single select ─────────────────────────────────────────────────────────
    if q["type"] == "single":
        answer = st.radio(
            "Select one:",
            options=q["options"],
            key=f"q_{q_idx}",
            label_visibility="collapsed",
        )

        if st.button("Next", type="primary", use_container_width=True, key=f"next_{q_idx}"):
            # Save answer
            st.session_state.answers[q["id"]] = answer
            st.session_state.current_question += 1

            # Cow: insert hoof question if limping
            if q["id"] == "mobility" and st.session_state.selected_animal == "Cow":
                st.session_state.questions = maybe_insert_hoof_question(
                    st.session_state.questions,
                    st.session_state.answers,
                    st.session_state.current_question - 1,
                )

            # Chicken single: insert detail questions if yes/unsure
            if st.session_state.selected_animal == "Chicken" and st.session_state.chicken_type == "single":
                st.session_state.questions = insert_chicken_detail_if_needed(
                    st.session_state.questions,
                    st.session_state.answers,
                )

            st.rerun()

    # ── Multi select ──────────────────────────────────────────────────────────
    elif q["type"] == "multi":
        selected = st.multiselect(
            "Select all that apply:",
            options=q["options"],
            key=f"q_{q_idx}",
            label_visibility="collapsed",
        )

        col_none, col_next = st.columns([1, 2])
        with col_none:
            if st.button("None of these", use_container_width=True, key=f"none_{q_idx}"):
                st.session_state.answers[q["id"]] = ["None"]
                st.session_state.current_question += 1
                st.rerun()
        with col_next:
            btn_disabled = len(selected) == 0
            if st.button(
                "Next",
                type="primary",
                use_container_width=True,
                disabled=btn_disabled,
                key=f"next_multi_{q_idx}",
            ):
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

    # Run triage if not done yet
    if st.session_state.triage_result is None:
        if st.session_state.judge_mode:
            import time
            with st.spinner("Analyzing symptoms..."):
                time.sleep(2)
            st.session_state.triage_result = JUDGE_MODE_CACHE
        else:
            symptom_summary = format_answers_for_prompt(
                st.session_state.selected_animal,
                st.session_state.answers,
            )
            with st.spinner("Retrieving knowledge and analyzing symptoms..."):
                try:
                    from rag_chain import run_triage
                    result = run_triage(
                        symptom_summary=symptom_summary,
                        image_bytes=st.session_state.uploaded_image,
                    )
                    st.session_state.triage_result = result
                except FileNotFoundError:
                    st.error("ChromaDB not found. Run: python ingest.py")
                    if st.button("← Go back"):
                        go_home()
                    return
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    if st.button("← Try again"):
                        st.session_state.triage_result = None
                        st.rerun()
                    return

    r = st.session_state.triage_result
    severity = r.get("severity", "MEDIUM").upper()
    escalate = r.get("escalate_to_vet", False)
    sev_color, sev_bg = SEVERITY_COLORS.get(severity, ("#333", "#eee"))

    # Header
    chicken_label = ""
    if st.session_state.selected_animal == "Chicken" and st.session_state.chicken_type:
        chicken_label = f" · {'Single Bird' if st.session_state.chicken_type == 'single' else 'Flock'}"

    st.markdown(f"""
    <div style="font-weight:800; font-size:22px; color:#2d4a1e; margin-bottom:4px;">
      Triage Assessment
    </div>
    <div style="color:#6b7c61; font-size:14px; margin-bottom:16px;">
      {animal['label']}{chicken_label} · AI-assisted recommendation
    </div>
    """, unsafe_allow_html=True)

    # Severity banner
    icon = "🚨" if severity in ["HIGH", "CRITICAL"] else "⚠️" if severity == "MEDIUM" else "✅"
    st.markdown(f"""
    <div style="background:{sev_bg}; border:1px solid {sev_color}40; border-radius:12px;
                padding:14px 20px; margin-bottom:16px; display:flex; align-items:center; gap:12px;">
      <span style="font-size:24px;">{icon}</span>
      <div>
        <div style="font-size:12px; color:{sev_color}; font-weight:600;">SEVERITY</div>
        <div style="font-size:20px; font-weight:800; color:{sev_color};">{severity}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Possible conditions
    st.markdown("#### Possible Conditions")
    for condition in r.get("likely_conditions", []):
        conf = condition.get("confidence", "?")
        conf_bg   = {"HIGH": "#d4edda", "MEDIUM": "#fff3cd", "LOW": "#f8d7da"}.get(conf, "#eee")
        conf_text = {"HIGH": "#155724", "MEDIUM": "#856404", "LOW": "#842029"}.get(conf, "#333")
        st.markdown(f"""
        <div style="background:white; border:1px solid #e0d5c5; border-radius:10px;
                    padding:12px 16px; margin-bottom:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; color:#2d4a1e; font-size:16px;">{condition['name']}</span>
            <span style="background:{conf_bg}; color:{conf_text}; padding:2px 10px;
                         border-radius:20px; font-size:12px; font-weight:600;">{conf} confidence</span>
          </div>
          <div style="color:#6b7c61; font-size:14px; margin-top:4px;">{condition.get('explanation','')}</div>
        </div>
        """, unsafe_allow_html=True)

    # Immediate actions
    st.markdown("#### What to do right now")
    for i, action in enumerate(r.get("immediate_actions", []), 1):
        st.markdown(f"""
        <div style="display:flex; gap:12px; align-items:flex-start; padding:10px 0;
                    border-bottom:1px solid #f0ebe0;">
          <span style="background:#5a8a3c; color:white; border-radius:50%; width:26px; height:26px;
                       display:flex; align-items:center; justify-content:center; font-size:13px;
                       font-weight:700; flex-shrink:0; margin-top:2px;">{i}</span>
          <span style="color:#2d4a1e; font-size:15px; line-height:1.5;">{action}</span>
        </div>
        """, unsafe_allow_html=True)

    # Photo observations
    img_obs = r.get("image_observations", "")
    if img_obs and img_obs != "No image provided" and st.session_state.uploaded_image:
        st.markdown("#### Photo Analysis")
        col_img, col_obs = st.columns([1, 2])
        with col_img:
            img = Image.open(io.BytesIO(st.session_state.uploaded_image))
            st.image(img, use_column_width=True)
        with col_obs:
            st.markdown(f"""
            <div style="background:#f8f6f0; border-radius:10px; padding:14px;
                        font-size:14px; color:#2d4a1e; line-height:1.6;">
              {img_obs}
            </div>
            """, unsafe_allow_html=True)

    # Uncertainty
    if r.get("uncertainty_note"):
        st.markdown(f"""
        <div style="background:#f8f6f0; border-left:3px solid #aaa; border-radius:0 8px 8px 0;
                    padding:10px 14px; margin:12px 0; font-size:14px; color:#6b7c61;">
          <strong>Note:</strong> {r['uncertainty_note']}
        </div>
        """, unsafe_allow_html=True)

    # Sources
    sources = r.get("cited_sources", [])
    if sources:
        st.markdown("#### Sources used")
        sources_html = " ".join(f'<span class="source-tag">{s}</span>' for s in sources)
        st.markdown(f"<div style='margin-bottom:16px;'>{sources_html}</div>", unsafe_allow_html=True)

    # Vet alert
    if escalate or severity in ["HIGH", "CRITICAL"]:
        st.markdown("""
        <div style="background:#fff0f0; border:2px solid #dc3545; border-radius:14px; padding:20px; margin-top:16px;">
          <div style="font-size:18px; font-weight:800; color:#842029; margin-bottom:8px;">
            Vet Consultation Recommended
          </div>
          <div style="color:#6b2737; font-size:14px;">
            Based on these symptoms, please contact your veterinarian.
            Click below to send them a pre-filled summary.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.judge_mode:
            if st.button("Alert Vet (Judge Mode — Simulated)", type="primary", use_container_width=True):
                sim = simulate_alert(animal["label"], severity, r.get("vet_summary", ""))
                st.success(sim["message"])
                st.code(sim["preview"])
        else:
            mailto_link = build_mailto_link(
                vet_email=st.session_state.vet_email,
                animal_type=animal["label"],
                severity=severity,
                vet_summary=r.get("vet_summary", ""),
                conditions=r.get("likely_conditions", []),
            )
            st.markdown(f"""
            <a href="{mailto_link}" style="display:block; background:#dc3545; color:white;
               text-align:center; padding:14px; border-radius:10px; font-weight:700;
               font-size:16px; text-decoration:none; margin-bottom:12px;">
              Alert Your Vet (Opens Email)
            </a>
            """, unsafe_allow_html=True)

            with st.expander("Preview vet message"):
                st.text_area("Message:", value=r.get("vet_summary", ""), height=150, disabled=True)

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Check another animal", use_container_width=True):
            go_home()
    with col2:
        if st.button("New check (same animal)", use_container_width=True):
            if st.session_state.selected_animal == "Chicken":
                st.session_state.screen = "chicken_type"
            else:
                st.session_state.questions = get_questions_for_animal(
                    st.session_state.selected_animal
                )
                st.session_state.screen = "dialogue"
            st.session_state.answers = {}
            st.session_state.current_question = 0
            st.session_state.triage_result = None
            st.session_state.uploaded_image = None
            st.rerun()

    if st.session_state.judge_mode:
        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#999; font-size:12px;">
          Judge mode active — responses use cached demo data
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