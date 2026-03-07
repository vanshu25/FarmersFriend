# dialogue.py
# Structured symptom dialogue trees for each animal type.
# Each animal has a list of steps. Each step has a question and options.
# Options can be single-select or multi-select.
#
# Chicken questions branch based on single bird vs flock:
#   - Flock path: screens for Avian Influenza, Newcastle Disease
#   - Single path: screens for respiratory, digestive, neurological diseases
# Branching is handled dynamically in app.py via maybe_branch_chicken_questions()

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

# ══════════════════════════════════════════════════════════════════════════════
# COW QUESTIONS
# ══════════════════════════════════════════════════════════════════════════════

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
        "question": "Look at the cow's left side — does it look swollen or bloated? (bloat is a buildup of gas in the rumen)",
        "type": "single",
        "options": [
            "Yes, visibly swollen on the left",
            "Slightly swollen, not sure",
            "No swelling"
        ],
        "photo_hint": True
    },
    {
        "id": "respiratory",
        "question": "Any respiratory symptoms — nasal discharge, coughing or breathing trouble? (select all that apply)",
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
        "question": "Any changes with the udder or milk? (udder is the milk gland between the hind legs — select all that apply)",
        "type": "multi",
        "options": [
            "Milk production suddenly dropped",
            "Udder feels swollen, hot or painful",
            "Milk looks abnormal (clumps, watery, bloody)",
            "Sweet or unusual smell from breath",
            "None of these"
        ],
        "photo_hint": True
    },
    {
        "id": "digestive_eyes",
        "question": "Any of these visible? Includes tremors, lesions or eye symptoms (select all that apply)",
        "type": "multi",
        "options": [
            "Diarrhea",
            "Significant weight loss",
            "Eye redness, tearing or cloudy eye",
            "Kicking at belly or restless",
            "Muscle tremors or cold ears",
            "None of these"
        ],
        "photo_hint": True
    },
]

# Inserted dynamically only if cow is limping
COW_HOOF_QUESTION = {
    "id": "hoof_signs",
    "question": "Look closely at the hooves — any lesions, swelling or foul smell? (select all that apply)",
    "type": "multi",
    "options": [
        "Swelling between the toes",
        "Foul smell from hoof area",
        "Hoof looks cracked or damaged",
        "Nothing obvious"
    ],
    "photo_hint": True
}


# ══════════════════════════════════════════════════════════════════════════════
# CHICKEN QUESTIONS
# ══════════════════════════════════════════════════════════════════════════════

# Always asked first — answer determines which branch follows
CHICKEN_COUNT_QUESTION = {
    "id": "chicken_count",
    "question": "How many chickens are showing symptoms?",
    "type": "single",
    "options": [
        "Just one chicken",
        "Multiple chickens (2-10)",
        "Many chickens (10+)"
    ]
}

# ── Branch A: Flock ───────────────────────────────────────────────────────────

CHICKEN_FLOCK_QUESTIONS = [
    {
        "id": "flock_duration",
        "question": "How long have the chickens been showing symptoms?",
        "type": "single",
        "options": [
            "Just noticed (today)",
            "1-2 days",
            "3-7 days",
            "Over a week"
        ]
    },
    {
        "id": "flock_head_swelling",
        "question": "Do any of the chickens have swollen heads or faces?",
        "type": "single",
        "options": ["Yes", "No", "Not sure"],
        "photo_hint": True
    },
    {
        "id": "flock_comb_color",
        "question": "Are any combs or wattles discolored — dark purple, blue or black?",
        "type": "single",
        "options": ["Yes", "No", "Not sure"],
        "photo_hint": True
    },
    {
        "id": "flock_breathing",
        "question": "Are any chickens gasping, rattling or breathing with their mouth open?",
        "type": "single",
        "options": ["Yes", "No", "Not sure"]
    },
    {
        "id": "flock_neurological",
        "question": "Do any chickens have tremors, a twisted neck or move in circles?",
        "type": "single",
        "options": ["Yes", "No", "Not sure"],
        "photo_hint": True
    },
    {
        "id": "flock_other",
        "question": "Any other signs across the flock? (select all that apply)",
        "type": "multi",
        "options": [
            "Sudden deaths with no prior warning",
            "Drop in egg production",
            "Loss of appetite across the flock",
            "Diarrhea in multiple birds",
            "None of these"
        ]
    },
]

# ── Branch B: Single bird ─────────────────────────────────────────────────────

CHICKEN_SINGLE_BASE_QUESTIONS = [
    {
        "id": "single_duration",
        "question": "How long has this chicken been showing symptoms?",
        "type": "single",
        "options": [
            "Just noticed (today)",
            "1-2 days",
            "3-7 days",
            "Over a week"
        ]
    },
    {
        "id": "single_respiratory",
        "question": "Does the chicken have any breathing or nose issues — coughing, sneezing, discharge or watery eyes?",
        "type": "single",
        "options": ["Yes", "No", "Not sure"]
    },
    {
        "id": "single_digestive",
        "question": "Does the chicken have any digestive issues — diarrhea, weight loss or weakness?",
        "type": "single",
        "options": ["Yes", "No", "Not sure"]
    },
    {
        "id": "single_neurological",
        "question": "Does the chicken show any neurological signs — paralysis, tremors or twisted neck?",
        "type": "single",
        "options": ["Yes", "No", "Not sure"]
    },
]

# Detail questions — inserted conditionally based on yes/unsure answers
CHICKEN_RESP_DETAIL = {
    "id": "single_resp_detail",
    "question": "Which of these do you see on the sick chicken? (select all that apply)",
    "type": "multi",
    "options": [
        "Facial swelling or bad odor from face",
        "Egg production has dropped or shell quality is poor",
        "Swollen sinuses or foamy eyes",
        "None of these"
    ],
    "photo_hint": True
}

CHICKEN_DIGEST_DETAIL = {
    "id": "single_digest_detail",
    "question": "Which of these do you see? (select all that apply)",
    "type": "multi",
    "options": [
        "Bloody droppings",
        "White or green diarrhea with signs of dehydration",
        "None of these"
    ],
    "photo_hint": True
}

CHICKEN_NEURO_DETAIL = {
    "id": "single_neuro_detail",
    "question": "Which of these do you see? (select all that apply)",
    "type": "multi",
    "options": [
        "Leg or wing paralysis (especially in young birds)",
        "Tremors or circling behavior",
        "Dark wart-like lesions on comb or wattles",
        "None of these"
    ],
    "photo_hint": True
}


# ══════════════════════════════════════════════════════════════════════════════
# DYNAMIC QUESTION INSERTION (called from app.py)
# ══════════════════════════════════════════════════════════════════════════════

def get_questions_for_animal(animal_key: str) -> list:
    """
    Returns initial question list.
    Chickens only get the first (count) question — rest inserted after branching.
    """
    if animal_key == "Cow":
        return list(COW_QUESTIONS)
    elif animal_key == "Chicken":
        return [CHICKEN_COUNT_QUESTION]
    return []


def maybe_insert_hoof_question(questions: list, answers: dict, current_index: int) -> list:
    """Call after cow mobility answer. Inserts hoof question if limping."""
    mobility = answers.get("mobility", "")
    already_inserted = any(q["id"] == "hoof_signs" for q in questions)
    if ("limping" in mobility.lower() or "reluctant" in mobility.lower()) and not already_inserted:
        questions.insert(current_index + 1, COW_HOOF_QUESTION)
    return questions


def maybe_branch_chicken_questions(questions: list, answers: dict) -> list:
    """
    Call after chicken_count is answered.
    Appends flock or single-bird base questions to the list.
    Safe to call multiple times.
    """
    already_branched = any(
        q["id"] in ("flock_duration", "single_duration")
        for q in questions
    )
    if already_branched:
        return questions

    count = answers.get("chicken_count", "")
    if "Just one" in count:
        questions.extend(list(CHICKEN_SINGLE_BASE_QUESTIONS))
    else:
        questions.extend(list(CHICKEN_FLOCK_QUESTIONS))

    return questions


def maybe_insert_chicken_detail_questions(questions: list, answers: dict, current_index: int) -> list:
    """
    Call after each single-bird question is answered.
    Inserts resp/digest/neuro detail questions if farmer said Yes or Not sure.
    Safe to call multiple times — checks if already inserted.
    """
    existing_ids = {q["id"] for q in questions}

    # Respiratory detail — insert after single_respiratory
    if (
        "single_resp_detail" not in existing_ids
        and answers.get("single_respiratory") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_respiratory":
                questions.insert(i + 1, CHICKEN_RESP_DETAIL)
                break

    # Digestive detail — insert after single_digestive
    if (
        "single_digest_detail" not in existing_ids
        and answers.get("single_digestive") in ["Yes", "Not sure"]
    ):
        for i, q in enumerate(questions):
            if q["id"] == "single_digestive":
                questions.insert(i + 1, CHICKEN_DIGEST_DETAIL)
                break

    # Neurological detail — insert after single_neurological
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
# SCORING
# ══════════════════════════════════════════════════════════════════════════════

def score_cow_conditions(answers: dict) -> dict:
    """Scores cow conditions. Returns dict sorted highest first, zeros excluded."""
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

    # Milk Fever
    if "Struggling to stand" in mobility or "Cannot stand" in mobility:
        if "calved within last 3 days" in calving:
            scores["Milk Fever (Hypocalcemia)"] += 1
        elif "Not sure" in calving:
            scores["Milk Fever (Hypocalcemia)"] += 0.5
    if "Muscle tremors or cold ears" in digestive_eyes:
        scores["Milk Fever (Hypocalcemia)"] += 1

    # Bloat
    if "visibly swollen on the left" in abdomen:
        scores["Bloat"] += 1
    elif "Slightly swollen" in abdomen:
        scores["Bloat"] += 0.5
    if "Kicking at belly or restless" in digestive_eyes:
        scores["Bloat"] += 1

    # BRD
    if "Coughing" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    if "Nasal discharge (runny nose)" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    if "Breathing fast or with effort" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    if "Fever (hot nose, warm ears)" in respiratory:
        scores["Bovine Respiratory Disease (BRD)"] += 1
    if ("Multiple cows" in cow_count or "Many cows" in cow_count) and scores["Bovine Respiratory Disease (BRD)"] > 0:
        scores["Bovine Respiratory Disease (BRD)"] += 1

    # Foot Rot
    if "limping" in mobility.lower() or "reluctant" in mobility.lower():
        scores["Foot Rot"] += 1
    if isinstance(hoof_signs, list):
        if "Swelling between the toes" in hoof_signs:
            scores["Foot Rot"] += 1
        if "Foul smell from hoof area" in hoof_signs:
            scores["Foot Rot"] += 1
        if "Hoof looks cracked or damaged" in hoof_signs:
            scores["Foot Rot"] += 0.5

    # Mastitis
    if "Milk production suddenly dropped" in udder_milk:
        scores["Mastitis"] += 1
    if "Udder feels swollen, hot or painful" in udder_milk:
        scores["Mastitis"] += 1
    if "Milk looks abnormal (clumps, watery, bloody)" in udder_milk:
        scores["Mastitis"] += 1

    # Ketosis
    if "calved within last few weeks" in calving:
        scores["Ketosis"] += 1
    if "Milk production suddenly dropped" in udder_milk:
        scores["Ketosis"] += 0.5
    if "Sweet or unusual smell from breath" in udder_milk:
        scores["Ketosis"] += 1
    if "Reduced appetite" in answers.get("eating_status", ""):
        scores["Ketosis"] += 0.5

    # Pinkeye
    if "Eye redness, tearing or cloudy eye" in digestive_eyes:
        scores["Pinkeye"] += 1

    # BVD / Johne's
    if "Diarrhea" in digestive_eyes:
        scores["BVD / Johne's Disease"] += 1
    if "Significant weight loss" in digestive_eyes:
        scores["BVD / Johne's Disease"] += 1

    return dict(sorted(
        {k: v for k, v in scores.items() if v > 0}.items(),
        key=lambda x: -x[1]
    ))


def score_chicken_conditions(answers: dict) -> dict:
    """
    Scores chicken conditions for both flock and single-bird paths.
    Returns dict sorted highest first, zeros excluded.
    """
    scores = {
        "Avian Influenza": 0,
        "Newcastle Disease": 0,
        "Infectious Coryza": 0,
        "Infectious Bronchitis": 0,
        "Mycoplasmosis": 0,
        "Coccidiosis": 0,
        "Salmonellosis": 0,
        "Marek's Disease": 0,
        "Fowl Pox": 0,
    }

    count = answers.get("chicken_count", "")
    is_flock = "Just one" not in count

    if is_flock:
        # Avian Influenza
        if answers.get("flock_head_swelling") == "Yes":
            scores["Avian Influenza"] += 1
        elif answers.get("flock_head_swelling") == "Not sure":
            scores["Avian Influenza"] += 0.5

        if answers.get("flock_comb_color") == "Yes":
            scores["Avian Influenza"] += 1
        elif answers.get("flock_comb_color") == "Not sure":
            scores["Avian Influenza"] += 0.5

        if answers.get("flock_breathing") == "Yes":
            scores["Avian Influenza"] += 1
        elif answers.get("flock_breathing") == "Not sure":
            scores["Avian Influenza"] += 0.5

        flock_other = answers.get("flock_other", [])
        if "Sudden deaths with no prior warning" in flock_other:
            scores["Avian Influenza"] += 1

        # Newcastle Disease
        if answers.get("flock_neurological") == "Yes":
            scores["Newcastle Disease"] += 1
        elif answers.get("flock_neurological") == "Not sure":
            scores["Newcastle Disease"] += 0.5

        # Newcastle also possible with breathing but low AI score
        if answers.get("flock_breathing") == "Yes" and scores["Avian Influenza"] < 1:
            scores["Newcastle Disease"] += 0.5

    else:
        resp_detail   = answers.get("single_resp_detail", [])
        digest_detail = answers.get("single_digest_detail", [])
        neuro_detail  = answers.get("single_neuro_detail", [])

        # Infectious Coryza
        if "Facial swelling or bad odor from face" in resp_detail:
            scores["Infectious Coryza"] += 1

        # Infectious Bronchitis
        if "Egg production has dropped or shell quality is poor" in resp_detail:
            scores["Infectious Bronchitis"] += 1

        # Mycoplasmosis
        if "Swollen sinuses or foamy eyes" in resp_detail:
            scores["Mycoplasmosis"] += 1

        # Coccidiosis
        if "Bloody droppings" in digest_detail:
            scores["Coccidiosis"] += 1
        elif answers.get("single_digestive") == "Not sure":
            scores["Coccidiosis"] += 0.5

        # Salmonellosis
        if "White or green diarrhea with signs of dehydration" in digest_detail:
            scores["Salmonellosis"] += 1

        # Marek's Disease
        if "Leg or wing paralysis (especially in young birds)" in neuro_detail:
            scores["Marek's Disease"] += 1
        elif answers.get("single_neurological") == "Not sure":
            scores["Marek's Disease"] += 0.5

        # Newcastle Disease
        if "Tremors or circling behavior" in neuro_detail:
            scores["Newcastle Disease"] += 1

        # Fowl Pox
        if "Dark wart-like lesions on comb or wattles" in neuro_detail:
            scores["Fowl Pox"] += 1

    return dict(sorted(
        {k: v for k, v in scores.items() if v > 0}.items(),
        key=lambda x: -x[1]
    ))


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT FORMATTER
# ══════════════════════════════════════════════════════════════════════════════

def format_answers_for_prompt(animal_key: str, answers: dict) -> str:
    """
    Formats dialogue answers + pre-scored conditions into LLM prompt string.
    """
    animal_label = ANIMALS[animal_key]["label"]
    lines = [f"Animal type: {animal_label}"]

    if animal_key == "Cow":
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

        scores = score_cow_conditions(answers)
        if scores:
            lines.append("\nPre-scored condition likelihood (higher = more likely):")
            for condition, score in scores.items():
                lines.append(f"  - {condition}: {score:.1f} points")

    elif animal_key == "Chicken":
        count = answers.get("chicken_count", "")
        is_flock = "Just one" not in count
        lines.append(f"Single bird or flock: {'Flock' if is_flock else 'Single bird'}")

        if is_flock:
            label_map = {
                "chicken_count":       "Number of chickens affected",
                "flock_duration":      "Duration",
                "flock_head_swelling": "Head / face swelling",
                "flock_comb_color":    "Comb / wattle discoloration",
                "flock_breathing":     "Breathing problems",
                "flock_neurological":  "Tremors / twisted neck",
                "flock_other":         "Other flock signs",
            }
        else:
            label_map = {
                "chicken_count":        "Number of chickens affected",
                "single_duration":      "Duration",
                "single_respiratory":   "Respiratory issues",
                "single_resp_detail":   "Respiratory details",
                "single_digestive":     "Digestive issues",
                "single_digest_detail": "Digestive details",
                "single_neurological":  "Neurological signs",
                "single_neuro_detail":  "Neurological details",
            }

        for key, label in label_map.items():
            if key in answers:
                val = answers[key]
                if isinstance(val, list):
                    val = ", ".join(val)
                lines.append(f"{label}: {val}")

        scores = score_chicken_conditions(answers)
        if scores:
            lines.append("\nPre-scored condition likelihood (higher = more likely):")
            for condition, score in scores.items():
                lines.append(f"  - {condition}: {score:.1f} points")
        else:
            lines.append("\nNo strong condition match — full symptom review needed.")

    return "\n".join(lines)