# animal_registry.py
# Persistent animal registry and health history for Farmer's Friend.
# Uses a local JSON file (farm_data.json) — no database needed.

import json
import os
from datetime import datetime
from typing import Optional

DATA_FILE = "farm_data.json"

# Short IDs: CO1, CO2... / CH1, CH2...
SPECIES_ID_PREFIX = {
    "🐄 Cow":     "CO",
    "🐔 Chicken": "CH",
    "🐷 Pig":     "PI",
    "🐑 Sheep":   "SH",
    "Cow":        "CO",
    "Chicken":    "CH",
    "Pig":        "PI",
    "Sheep":      "SH",
}

SPECIES_PREFIXES = SPECIES_ID_PREFIX  # alias for backward compat

# ── Demo seed data ────────────────────────────────────────────────────────────

DEMO_ANIMALS = {
    "CO1": {"id":"CO1","name":"Bessie","species":"🐄 Cow","notes":"Holstein, pen 2","registered_at":"2025-01-10T08:00:00"},
    "CO2": {"id":"CO2","name":"Duke",  "species":"🐄 Cow","notes":"Angus, pen 3",   "registered_at":"2025-01-12T09:00:00"},
    "CO3": {"id":"CO3","name":"Millie","species":"🐄 Cow","notes":"Jersey, pen 1",  "registered_at":"2025-02-01T10:00:00"},
    "CO4": {"id":"CO4","name":"Rex",   "species":"🐄 Cow","notes":"Hereford, pen 4","registered_at":"2025-02-14T11:00:00"},
    "CH1": {"id":"CH1","name":"Goldie","species":"🐔 Chicken","notes":"Layer, coop A","registered_at":"2025-01-15T08:00:00"},
    "CH2": {"id":"CH2","name":"Speckle","species":"🐔 Chicken","notes":"Broiler, coop B","registered_at":"2025-01-20T09:00:00"},
    "CH3": {"id":"CH3","name":"Feathers","species":"🐔 Chicken","notes":"Layer, coop A","registered_at":"2025-03-01T10:00:00"},
}

DEMO_RECORDS = [
    {"record_id":"REC-DEMO-001","animal_id":"CO1","species":"🐄 Cow","timestamp":"2025-03-01T09:00:00",
     "severity":"HIGH","conditions":[{"name":"Bovine Respiratory Disease","confidence":"HIGH","explanation":"Labored breathing, nasal discharge."},{"name":"Pneumonia","confidence":"MEDIUM","explanation":"Secondary infection possible."}],
     "answers":{},"vet_alerted":True,"image_observations":"","uncertainty_note":"Lab test needed."},
    {"record_id":"REC-DEMO-002","animal_id":"CO2","species":"🐄 Cow","timestamp":"2025-03-03T11:00:00",
     "severity":"MEDIUM","conditions":[{"name":"Lameness","confidence":"HIGH","explanation":"Limping on rear left leg."},{"name":"Foot Rot","confidence":"MEDIUM","explanation":"Possible hoof infection."}],
     "answers":{},"vet_alerted":False,"image_observations":"","uncertainty_note":""},
    {"record_id":"REC-DEMO-003","animal_id":"CO3","species":"🐄 Cow","timestamp":"2025-03-05T14:00:00",
     "severity":"LOW","conditions":[{"name":"Mild Nutritional Deficiency","confidence":"MEDIUM","explanation":"Reduced feed intake."}],
     "answers":{},"vet_alerted":False,"image_observations":"","uncertainty_note":""},
    {"record_id":"REC-DEMO-004","animal_id":"CO1","species":"🐄 Cow","timestamp":"2025-03-10T10:00:00",
     "severity":"MEDIUM","conditions":[{"name":"Mastitis","confidence":"HIGH","explanation":"Swollen udder, reduced milk."}],
     "answers":{},"vet_alerted":False,"image_observations":"","uncertainty_note":""},
    {"record_id":"REC-DEMO-005","animal_id":"CH1","species":"🐔 Chicken","timestamp":"2025-03-02T08:30:00",
     "severity":"HIGH","conditions":[{"name":"Newcastle Disease","confidence":"HIGH","explanation":"Neurological signs, reduced egg production."}],
     "answers":{},"vet_alerted":True,"image_observations":"","uncertainty_note":"Contagious — isolate flock."},
    {"record_id":"REC-DEMO-006","animal_id":"CH2","species":"🐔 Chicken","timestamp":"2025-03-06T09:00:00",
     "severity":"MEDIUM","conditions":[{"name":"Coccidiosis","confidence":"HIGH","explanation":"Bloody droppings, lethargy."}],
     "answers":{},"vet_alerted":False,"image_observations":"","uncertainty_note":""},
]


# ── Low-level I/O ─────────────────────────────────────────────────────────────

def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        # First run — seed with demo data
        data = {"animals": DEMO_ANIMALS, "records": DEMO_RECORDS}
        _save(data)
        return data
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"animals": {}, "records": []}


def _save(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Animal CRUD ───────────────────────────────────────────────────────────────

def get_all_animals() -> dict:
    """Returns {animal_id: animal_dict} for all registered animals."""
    return _load()["animals"]


def get_animals_by_species(species_key: str) -> list[dict]:
    """Returns list of animals matching a species key (e.g. '🐄 Cow')."""
    animals = _load()["animals"]
    return [a for a in animals.values() if a["species"] == species_key]


def get_animal(animal_id: str) -> Optional[dict]:
    return _load()["animals"].get(animal_id)


def register_animal(species_key: str, name: str, notes: str = "", custom_num: int = None) -> str:
    """
    Register a new animal. ID format: CO1, CO2... / CH1, CH2...
    If custom_num provided, uses that number (e.g. farmer enters '5' → CO5).
    Returns the animal_id.
    """
    data = _load()
    prefix = SPECIES_ID_PREFIX.get(species_key, "AN")

    if custom_num is not None:
        animal_id = f"{prefix}{custom_num}"
    else:
        existing_nums = []
        for k in data["animals"]:
            if k.startswith(prefix):
                try:
                    existing_nums.append(int(k[len(prefix):]))
                except ValueError:
                    pass
        next_num = max(existing_nums, default=0) + 1
        animal_id = f"{prefix}{next_num}"

    data["animals"][animal_id] = {
        "id": animal_id,
        "name": name.strip() or animal_id,
        "species": species_key,
        "notes": notes.strip(),
        "registered_at": datetime.now().isoformat(),
    }
    _save(data)
    return animal_id


def get_or_create_animal(species_key: str, num: int) -> str:
    """
    Given a species and number (e.g. 3), return animal_id CO3/CH3.
    Creates the animal if it doesn't exist yet.
    """
    prefix = SPECIES_ID_PREFIX.get(species_key, "AN")
    animal_id = f"{prefix}{num}"
    data = _load()
    if animal_id not in data["animals"]:
        register_animal(species_key, animal_id, custom_num=num)
    return animal_id


def get_ids_for_species(species_key: str) -> list[str]:
    """Returns sorted list of animal IDs for a species e.g. ['CO1','CO2','CO3']."""
    data = _load()
    prefix = SPECIES_ID_PREFIX.get(species_key, "AN")
    ids = [k for k in data["animals"] if k.startswith(prefix)]
    return sorted(ids, key=lambda x: int(x[len(prefix):]) if x[len(prefix):].isdigit() else 0)


def update_animal(animal_id: str, name: str, notes: str):
    data = _load()
    if animal_id in data["animals"]:
        data["animals"][animal_id]["name"] = name.strip()
        data["animals"][animal_id]["notes"] = notes.strip()
        _save(data)


def delete_animal(animal_id: str):
    data = _load()
    data["animals"].pop(animal_id, None)
    # Keep health records (historical value), just orphan them
    _save(data)


# ── Health Records ────────────────────────────────────────────────────────────

def save_health_record(
    animal_id: str,
    species_key: str,
    severity: str,
    conditions: list[dict],
    answers: dict,
    vet_alerted: bool = False,
    image_observations: str = "",
    uncertainty_note: str = "",
) -> str:
    """
    Save a triage result to the animal's health history.
    Returns the record_id.
    """
    data = _load()
    record_id = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{animal_id}"

    record = {
        "record_id": record_id,
        "animal_id": animal_id,
        "species": species_key,
        "timestamp": datetime.now().isoformat(),
        "severity": severity.upper(),
        "conditions": conditions,          # [{name, confidence, explanation}]
        "answers": answers,                # raw symptom answers
        "vet_alerted": vet_alerted,
        "image_observations": image_observations,
        "uncertainty_note": uncertainty_note,
    }

    data["records"].append(record)
    _save(data)
    return record_id


def get_records_for_animal(animal_id: str) -> list[dict]:
    """Returns all health records for a given animal, newest first."""
    data = _load()
    recs = [r for r in data["records"] if r["animal_id"] == animal_id]
    return sorted(recs, key=lambda r: r["timestamp"], reverse=True)


def save_chat_session(
    animal_id: Optional[str],
    species_key: Optional[str],
    messages: list[dict],
    summary: str,
    topics: list[str],
) -> str:
    """
    Save a freeform chat session to an animal's history (or as unlinked).
    messages: [{"role": "user"|"assistant", "content": "..."}]
    summary:  1-2 sentence AI-generated summary of what was discussed
    topics:   list of keywords e.g. ["lameness", "feed", "vaccination"]
    Returns the session_id.
    """
    data = _load()
    session_id = f"CHAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if animal_id:
        session_id += f"-{animal_id}"

    session = {
        "record_id": session_id,
        "type": "chat",
        "animal_id": animal_id,          # None if unlinked
        "species": species_key,
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "topics": topics,
        "messages": messages,
        "severity": "INFO",              # chats don't have severity flags
    }
    data["records"].append(session)
    _save(data)
    return session_id


def get_all_records() -> list[dict]:
    """All records, newest first."""
    data = _load()
    return sorted(data["records"], key=lambda r: r["timestamp"], reverse=True)


def get_recent_flags(limit: int = 10) -> list[dict]:
    """
    Returns recent HIGH/CRITICAL triage records enriched with animal name.
    """
    data = _load()
    flagged = [
        r for r in data["records"]
        if r.get("type") != "chat" and r["severity"] in ("HIGH", "CRITICAL")
    ]
    flagged = sorted(flagged, key=lambda r: r["timestamp"], reverse=True)[:limit]

    # Enrich with animal name
    for rec in flagged:
        animal = data["animals"].get(rec["animal_id"])
        rec["animal_name"] = animal["name"] if animal else "Unknown"
    return flagged


# ── Helpers ───────────────────────────────────────────────────────────────────

def severity_emoji(severity: str) -> str:
    return {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "🚨", "INFO": "💬"}.get(
        severity.upper(), "⚪"
    )


def format_timestamp(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%b %d, %Y  %I:%M %p")
    except Exception:
        return iso