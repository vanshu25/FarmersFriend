# dialogue.py
# Structured symptom dialogue trees for each animal type.
# Each animal has a list of steps. Each step has a question and options.
# Options can be single-select or multi-select.

ANIMALS = {
    "Cow": {
        "label": "Cow",
        "color": "#8B4513",
        "description": "Dairy & beef cattle"
    },
    "Chicken": {
        "label": "Chicken",
        "color": "#DAA520",
        "description": "Poultry & hens"
    },
}

# ── Cow-specific questions (based on veterinary decision tree) ────────────────

COW_QUESTIONS = [
    {
        "id": "cow_count",
        "question": "How many cows are showing symptoms?",
        "type": "single",
        "options": [
            "Just one cow",
            "Multiple cows (2-5)",
            "Many cows (6+)"
        ]
    },
    {
        "id": "duration",
        "question": "How long has this been going on?",
        "type": "single",
        "options": [
            "Just noticed (today)",
            "1-2 days",
            "3-7 days",
            "Over a week"
        ]
    },
    {
        "id": "mobility",
        "question": "Can the cow stand up and walk?",
        "type": "single",
        "options": [
            "Yes, standing and walking normally",
            "Standing but limping or reluctant to walk",
            "Struggling to stand or very weak",
            "Cannot stand at all"
        ]
    },
    {
        "id": "calving",
        "question": "Has this cow given birth recently?",
        "type": "single",
        "options": [
            "Yes, calved within last 3 days",
            "Yes, calved within last few weeks",
            "No recent calving",
            "Not sure"
        ]
    },
    {
        "id": "abdomen",
        "question": "Look at the cow's left side — does it look swollen or bloated?",
        "type": "single",
        "options": [
            "Yes, visibly swollen on the left",
            "Slightly swollen, not sure",
            "No swelling"
        ]
    },
    {
        "id": "respiratory",
        "question": "Any breathing or nose symptoms? (select all that apply)",
        "type": "multi",
        "options": [
            "Coughing",
            "Nasal discharge (runny nose)",
            "Breathing fast or with effort",
            "Fever (hot nose, warm ears)",
            "None of these"
        ]
    },
    {
        "id": "udder_milk",
        "question": "Any changes with the udder or milk? (select all that apply)",
        "type": "multi",
        "options": [
            "Milk production suddenly dropped",
            "Udder feels swollen, hot or painful",
            "Milk looks abnormal (clumps, watery, bloody)",
            "Sweet or unusual smell from breath",
            "None of these"
        ]
    },
    {
        "id": "digestive_eyes",
        "question": "Any of these visible? (select all that apply)",
        "type": "multi",
        "options": [
            "Diarrhea",
            "Significant weight loss",
            "Eye redness, tearing or cloudy eye",
            "Kicking at belly or restless",
            "Muscle tremors or cold ears",
            "None of these"
        ]
    },
]

# Hoof question — only inserted if cow is limping
COW_HOOF_QUESTION = {
    "id": "hoof_signs",
    "question": "Look closely at the hooves — what do you see? (select all that apply)",
    "type": "multi",
    "options": [
        "Swelling between the toes",
        "Foul smell from hoof area",
        "Hoof looks cracked or damaged",
        "Nothing obvious"
    ]
}

# ── Chicken-specific questions ────────────────────────────────────────────────

CHICKEN_QUESTIONS = [
    {
        "id": "duration",
        "question": "How long has this been going on?",
        "type": "single",
        "options": [
            "Just noticed (today)",
            "1-2 days",
            "3-7 days",
            "Over a week"
        ]
    },
    {
        "id": "multiple_animals",
        "question": "Is more than one chicken showing these symptoms?",
        "type": "single",
        "options": [
            "No, just this one",
            "Yes, multiple chickens",
            "Not sure"
        ]
    },
    {
        "id": "eating_status",
        "question": "Is the chicken eating and drinking normally?",
        "type": "single",
        "options": [
            "Yes, normal",
            "Reduced appetite",
            "Not eating or drinking at all"
        ]
    },
    {
        "id": "visible_signs",
        "question": "Which of these are visible? (select all that apply)",
        "type": "multi",
        "options": [
            "Runny eyes or nose",
            "Ruffled or missing feathers",
            "Lethargy / not moving much",
            "Abnormal droppings",
            "Coughing or sneezing",
            "Stopped laying eggs",
            "Leg weakness or paralysis",
            "None of these"
        ]
    },
    {
        "id": "body_area",
        "question": "Which area seems most affected?",
        "type": "single",
        "options": [
            "Eyes / head / comb",
            "Breathing / respiratory",
            "Legs / wings",
            "Feathers / skin",
            "Whole body / unclear"
        ]
    },
]

# ── Question getters ──────────────────────────────────────────────────────────

def get_questions_for_animal(animal_key: str) -> list:
    """Returns the full ordered question list for a given animal."""
    if animal_key == "Cow":
        return list(COW_QUESTIONS)  # hoof question inserted dynamically in app.py
    elif animal_key == "Chicken":
        return list(CHICKEN_QUESTIONS)
    return []


def maybe_insert_hoof_question(questions: list, answers: dict, current_index: int) -> list:
    """
    Call this after mobility question is answered.
    If cow is limping, inserts the hoof question right after current position.
    Safe to call multiple times — checks if already inserted.
    """
    mobility = answers.get("mobility", "")
    hoof_already_inserted = any(q["id"] == "hoof_signs" for q in questions)

    if (
        "limping" in mobility.lower() or "reluctant" in mobility.lower()
    ) and not hoof_already_inserted:
        insert_at = current_index + 1
        questions.insert(insert_at, COW_HOOF_QUESTION)

    return questions


# ── Scoring (cows only) ───────────────────────────────────────────────────────

def score_cow_conditions(answers: dict) -> dict:
    """
    Scores likely cow conditions based on dialogue answers.
    Mirrors the decision tree scoring from the veterinary document.
    Returns dict of condition -> score, sorted highest first, zeros excluded.
    """
    scores = {
        "Milk Fever (Hypocalcemia)": 0,
        "Bloat": 0,
        "Foot Rot": 0,
        "Bovine Respiratory Disease (BRD)": 0,
        "Mastitis": 0,
        "Ketosis": 0,
        "Pinkeye": 0,
        "BVD / Johne's Disease": 0,
    }

    mobility       = answers.get("mobility", "")
    calving        = answers.get("calving", "")
    abdomen        = answers.get("abdomen", "")
    respiratory    = answers.get("respiratory", [])
    udder_milk     = answers.get("udder_milk", [])
    digestive_eyes = answers.get("digestive_eyes", [])
    hoof_signs     = answers.get("hoof_signs", [])
    cow_count      = answers.get("cow_count", "")

    # ── Milk Fever ──
    if "Struggling to stand" in mobility or "Cannot stand" in mobility:
        if "calved within last 3 days" in calving:
            scores["Milk Fever (Hypocalcemia)"] += 1
        elif "Not sure" in calving:
            scores["Milk Fever (Hypocalcemia)"] += 0.5
    if "Muscle tremors or cold ears" in digestive_eyes:
        scores["Milk Fever (Hypocalcemia)"] += 1

    # ── Bloat ──
    if "visibly swollen on the left" in abdomen:
        scores["Bloat"] += 1
    elif "Slightly swollen" in abdomen:
        scores["Bloat"] += 0.5
    if "Kicking at belly or restless" in digestive_eyes:
        scores["Bloat"] += 1

    # ── BRD ──
    if "Coughing" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    if "Nasal discharge (runny nose)" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    if "Breathing fast or with effort" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    if "Fever (hot nose, warm ears)" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    # Multiple cows coughing strongly suggests BRD outbreak
    if "Multiple cows" in cow_count or "Many cows" in cow_count:
        if scores["Bovine Respiratory Disease (BRD)"] > 0:
            scores["Bovine Respiratory Disease (BRD)"] += 1

    # ── Foot Rot ──
    if "limping" in mobility.lower() or "reluctant" in mobility.lower():
        scores["Foot Rot"] += 1
    if isinstance(hoof_signs, list):
        if "Swelling between the toes" in hoof_signs:
            scores["Foot Rot"] += 1
        if "Foul smell from hoof area" in hoof_signs:
            scores["Foot Rot"] += 1
        if "Hoof looks cracked or damaged" in hoof_signs:
            scores["Foot Rot"] += 0.5

    # ── Mastitis ──
    if "Milk production suddenly dropped" in udder_milk:
        scores["Mastitis"] += 1
    if "Udder feels swollen, hot or painful" in udder_milk:
        scores["Mastitis"] += 1
    if "Milk looks abnormal (clumps, watery, bloody)" in udder_milk:
        scores["Mastitis"] += 1

    # ── Ketosis ──
    if "calved within last few weeks" in calving:
        scores["Ketosis"] += 1
    if "Milk production suddenly dropped" in udder_milk:
        scores["Ketosis"] += 0.5
    if "Sweet or unusual smell from breath" in udder_milk:
        scores["Ketosis"] += 1
    if "Reduced appetite" in answers.get("eating_status", ""):
        scores["Ketosis"] += 0.5

    # ── Pinkeye ──
    if "Eye redness, tearing or cloudy eye" in digestive_eyes:
        scores["Pinkeye"] += 1

    # ── BVD / Johne's ──
    if "Diarrhea" in digestive_eyes:
        scores["BVD / Johne's Disease"] += 1
    if "Significant weight loss" in digestive_eyes:
        scores["BVD / Johne's Disease"] += 1

    # Filter zeros and sort highest first
    return dict(
        sorted(
            {k: v for k, v in scores.items() if v > 0}.items(),
            key=lambda x: -x[1]
        )
    )


# ── Prompt formatter ──────────────────────────────────────────────────────────

def format_answers_for_prompt(animal_key: str, answers: dict) -> str:
    """
    Formats collected dialogue answers into a clean string for the LLM prompt.
    For cows, also includes pre-scored condition likelihoods.
    """
    animal_label = ANIMALS[animal_key]["label"]
    lines = [f"Animal type: {animal_label}"]

    if animal_key == "Cow":
        # Cow-specific label map
        label_map = {
            "cow_count":      "Number of cows affected",
            "duration":       "Duration",
            "mobility":       "Mobility / ability to stand",
            "calving":        "Recent calving",
            "abdomen":        "Abdominal swelling",
            "respiratory":    "Respiratory signs",
            "udder_milk":     "Udder / milk changes",
            "digestive_eyes": "Digestive / eye symptoms",
            "hoof_signs":     "Hoof observations",
        }

        for key, label in label_map.items():
            if key in answers:
                val = answers[key]
                if isinstance(val, list):
                    val = ", ".join(val)
                lines.append(f"{label}: {val}")

        # Append scored conditions
        scores = score_cow_conditions(answers)
        if scores:
            lines.append("\nPre-scored condition likelihood (higher = more likely):")
            for condition, score in scores.items():
                lines.append(f"  - {condition}: {score:.1f} points")

    else:
        # Chicken (and any future animals) — generic label map
        label_map = {
            "duration":        "Duration",
            "multiple_animals":"Multiple animals affected",
            "eating_status":   "Eating / drinking",
            "visible_signs":   "Visible signs",
            "body_area":       "Affected body area",
        }

        for key, label in label_map.items():
            if key in answers:
                val = answers[key]
                if isinstance(val, list):
                    val = ", ".join(val)
                lines.append(f"{label}: {val}")

    return "\n".join(lines)