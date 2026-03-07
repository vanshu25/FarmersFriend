# dialogue.py
# Structured symptom dialogue trees for each animal type.
# Each animal has a list of steps. Each step has a question and options.
# Options can be single-select or multi-select.

ANIMALS = {
    "🐄 Cow": {
        "label": "Cow",
        "emoji": "🐄",
        "color": "#8B4513",
        "description": "Dairy & beef cattle"
    },
    "🐔 Chicken": {
        "label": "Chicken",
        "emoji": "🐔",
        "color": "#DAA520",
        "description": "Poultry & hens"
    },
    "🐷 Pig": {
        "label": "Pig",
        "emoji": "🐷",
        "color": "#FFB6C1",
        "description": "Swine & hogs"
    },
    "🐑 Sheep": {
        "label": "Sheep",
        "emoji": "🐑",
        "color": "#708090",
        "description": "Sheep & lambs"
    },
}

# Shared base questions for all animals
BASE_QUESTIONS = [
    {
        "id": "issue_type",
        "question": "Is the issue physical, behavioral, or both?",
        "type": "single",
        "options": ["🤕 Physical (visible symptoms)", "😟 Behavioral (acting differently)", "⚠️ Both"]
    },
    {
        "id": "duration",
        "question": "How long has this been going on?",
        "type": "single",
        "options": ["⚡ Just noticed (today)", "📅 1–2 days", "📆 3–7 days", "🗓️ Over a week"]
    },
    {
        "id": "eating_status",
        "question": "Is the animal eating and drinking normally?",
        "type": "single",
        "options": ["✅ Yes, normal", "⬇️ Reduced appetite", "❌ Not eating/drinking at all"]
    },
    {
        "id": "multiple_animals",
        "question": "Is more than one animal showing these symptoms?",
        "type": "single",
        "options": ["❌ No, just this one", "✅ Yes, multiple animals", "🤔 Not sure"]
    },
]

# Animal-specific symptom questions
ANIMAL_QUESTIONS = {
    "🐄 Cow": [
        {
            "id": "visible_signs",
            "question": "Which of these are visible? (select all that apply)",
            "type": "multi",
            "options": [
                "🩸 Discharge or bleeding",
                "🤢 Vomiting or bloating",
                "🦵 Limping or trouble standing",
                "💨 Labored or fast breathing",
                "😵 Very tired / not moving",
                "🌡️ Swelling anywhere",
                "🥛 Drop in milk production",
                "💩 Diarrhea",
                "None of these"
            ]
        },
        {
            "id": "body_area",
            "question": "Which body area is most affected?",
            "type": "single",
            "options": ["🦵 Legs / hooves", "🫁 Chest / breathing", "🍼 Udder / reproductive", "🧠 Head / eyes / nose", "🫀 Whole body / unclear"]
        }
    ],
    "🐔 Chicken": [
        {
            "id": "visible_signs",
            "question": "Which of these are visible? (select all that apply)",
            "type": "multi",
            "options": [
                "💧 Runny eyes or nose",
                "🪶 Ruffled or missing feathers",
                "😵 Lethargy / not moving",
                "💩 Abnormal droppings",
                "🗣️ Coughing or sneezing",
                "❌ Stopped laying eggs",
                "🦵 Leg weakness or paralysis",
                "None of these"
            ]
        },
        {
            "id": "body_area",
            "question": "Which area seems most affected?",
            "type": "single",
            "options": ["👁️ Eyes / head / comb", "🫁 Breathing / respiratory", "🦵 Legs / wings", "🪶 Feathers / skin", "🫀 Whole body / unclear"]
        }
    ],
    "🐷 Pig": [
        {
            "id": "visible_signs",
            "question": "Which of these are visible? (select all that apply)",
            "type": "multi",
            "options": [
                "🤢 Vomiting",
                "💩 Diarrhea",
                "😵 Lethargy / weakness",
                "💨 Coughing or labored breathing",
                "🦵 Limping",
                "🌡️ Skin lesions or redness",
                "❌ Not eating at all",
                "None of these"
            ]
        },
        {
            "id": "body_area",
            "question": "Which area seems most affected?",
            "type": "single",
            "options": ["🫁 Respiratory / breathing", "🍽️ Digestive / stomach", "🦵 Legs / joints", "🌡️ Skin / surface", "🫀 Whole body / unclear"]
        }
    ],
    "🐑 Sheep": [
        {
            "id": "visible_signs",
            "question": "Which of these are visible? (select all that apply)",
            "type": "multi",
            "options": [
                "🦵 Limping or foot problem",
                "💩 Diarrhea (scours)",
                "😵 Lethargy / isolation",
                "💨 Nasal discharge or coughing",
                "🌡️ Swelling on body",
                "🪶 Wool loss or skin issue",
                "🤢 Bloating",
                "None of these"
            ]
        },
        {
            "id": "body_area",
            "question": "Which area seems most affected?",
            "type": "single",
            "options": ["🦵 Feet / legs", "🫁 Respiratory", "🍽️ Digestive / bloat", "🪶 Skin / wool", "🫀 Whole body / unclear"]
        }
    ]
}


def get_questions_for_animal(animal_key: str) -> list:
    """Returns the full ordered question list for a given animal."""
    animal_specific = ANIMAL_QUESTIONS.get(animal_key, [])
    # Insert animal-specific visible_signs after duration, body_area at end
    questions = (
        BASE_QUESTIONS[:2]           # issue_type, duration
        + [animal_specific[0]]       # visible_signs (animal-specific)
        + BASE_QUESTIONS[2:]         # eating_status, multiple_animals
        + [animal_specific[1]]       # body_area (animal-specific)
    )
    return questions


def format_answers_for_prompt(animal_key: str, answers: dict) -> str:
    """Formats collected dialogue answers into a clean string for the LLM prompt."""
    animal_label = ANIMALS[animal_key]["label"]
    lines = [f"Animal type: {animal_label}"]
    
    label_map = {
        "issue_type": "Issue type",
        "duration": "Duration",
        "visible_signs": "Visible signs",
        "eating_status": "Eating/drinking",
        "multiple_animals": "Multiple animals affected",
        "body_area": "Affected body area",
    }
    
    for key, label in label_map.items():
        if key in answers:
            val = answers[key]
            if isinstance(val, list):
                val = ", ".join(val)
            # Strip emojis for cleaner prompt (optional)
            lines.append(f"{label}: {val}")
    
    return "\n".join(lines)
