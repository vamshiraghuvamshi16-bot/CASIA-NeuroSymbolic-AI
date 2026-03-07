import json
import os
import re
import datetime
from typing import Any, Dict, List

# ---- Ensure absolute path so working-dir issues go away ----
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
MEMORY_PATH = os.path.join(DATA_DIR, "memory.json")


# ----------------- LOW-LEVEL LOAD / SAVE -----------------

def _load_all() -> Dict[str, Any]:
    """Load full memory JSON from disk. Returns {} on any problem."""
    if not os.path.exists(MEMORY_PATH):
        return {}
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        print(f"[memory] _load_all error reading {MEMORY_PATH}: {e}")
        return {}


def _save_all(data: Dict[str, Any]):
    """Write memory JSON to disk (creates folder if needed)."""
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    try:
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[memory] saved memory.json at {os.path.abspath(MEMORY_PATH)}; users={list(data.keys())}")
    except Exception as e:
        print(f"[memory] _save_all error writing {MEMORY_PATH}: {e}")


# ----------------- USER INITIALIZATION -----------------

def _ensure_user(all_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Ensure a user record exists and has required categories.
    Returns the user's dict (reference into all_data).
    """
    if user_id not in all_data or not isinstance(all_data[user_id], dict):
        all_data[user_id] = {
            "identity": [],
            "goals": [],
            "deadlines": [],
            "preferences": [],
            "habits": [],
            "history": [],
            "feedback": [],
            "self_learning": []
        }
    else:
        # ensure keys exist (defensive)
        for k in [
            "identity", "goals", "deadlines",
            "preferences", "habits",
            "history", "feedback", "self_learning"
        ]:
            if k not in all_data[user_id]:
                all_data[user_id][k] = []
    return all_data[user_id]


# ----------------- FACTS (IDENTITY / GOALS / ETC) -----------------

def add_fact(user_id: str, category: str, fact: str):
    """
    Save a fact under a specific category.
    Valid categories: identity, goals, deadlines, preferences, habits
    """
    if not fact or not category:
        return
    all_data = _load_all()
    user = _ensure_user(all_data, user_id)

    if fact not in user.get(category, []):
        user[category].append(fact)
        print(f"[memory] add_fact: user={user_id} category={category} fact={fact}")
        _save_all(all_data)


# ----------------- HISTORY + INTENTS -----------------

def add_history(user_id: str, message: str, intent: str):
    """
    Append conversation history + detected intent. Keeps last 50 messages.
    """
    all_data = _load_all()
    user = _ensure_user(all_data, user_id)

    user["history"].append({
        "message": message,
        "intent": intent,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    })
    user["history"] = user["history"][-50:]

    print(f"[memory] add_history: user={user_id} intent={intent} preview={(message or '')[:80]}")
    _save_all(all_data)


# ----------------- EXPLICIT FEEDBACK -----------------

def save_feedback(user_id: str, text: str):
    """
    Store explicit user feedback (strong learning signal).
    """
    if not text:
        return
    all_data = _load_all()
    user = _ensure_user(all_data, user_id)

    user["feedback"].append({
        "text": text,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    })
    print(f"[memory] save_feedback: user={user_id} feedback={text}")
    _save_all(all_data)


# ----------------- IMPLICIT SELF-LEARNING -----------------

def save_self_learning(user_id: str, signal: str):
    """
    Store implicit self-learning signal (weak learning signal).
    """
    if not signal:
        return
    all_data = _load_all()
    user = _ensure_user(all_data, user_id)

    user["self_learning"].append({
        "signal": signal,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    })
    print(f"[memory] save_self_learning: user={user_id} signal={signal}")
    _save_all(all_data)


# ----------------- FACT EXTRACTION -----------------

def _safe_split_after(text: str, marker: str) -> str:
    if not text or not marker:
        return ""
    lower = text.lower()
    idx = lower.find(marker.lower())
    if idx == -1:
        return ""
    return text[idx + len(marker):].strip()


def extract_facts(user_id: str, message: str):
    """
    Heuristic extractor for identity, goals, preferences, habits.
    """
    if not message or not message.strip():
        return

    text_lower = message.lower()

    # --- NAME ---
    name_match = re.search(r"\bmy name is\s+([A-Za-z][A-Za-z\s]{0,40})", message, flags=re.I)
    if not name_match:
        name_match = re.search(r"\b(i am|i'm)\s+([A-Za-z][A-Za-z\s]{0,40})", message, flags=re.I)
        extracted_name = name_match.group(2) if name_match else None
    else:
        extracted_name = name_match.group(1)

    if extracted_name:
        extracted_name = extracted_name.strip().strip(".!?,")
        add_fact(user_id, "identity", f"User's name is {extracted_name}.")

    # --- GOALS ---
    if "i want to" in text_lower:
        after = _safe_split_after(message, "i want to")
        if after:
            add_fact(user_id, "goals", f"User wants to {after}")

    # --- PREFERENCES ---
    if "prefer" in text_lower:
        after = _safe_split_after(message, "prefer")
        if after:
            add_fact(user_id, "preferences", f"User prefers {after}")

    # --- HABITS ---
    if "i usually" in text_lower:
        after = _safe_split_after(message, "i usually")
        if after:
            add_fact(user_id, "habits", f"User usually {after}")


# ----------------- MEMORY RETRIEVAL -----------------

def get_memories_for_prompt(user_id: str) -> Dict[str, List[str]]:
    """
    Returns only semantic memories (NOT raw history).
    """
    all_data = _load_all()
    user = _ensure_user(all_data, user_id)

    return {
        "identity": user.get("identity", []),
        "goals": user.get("goals", []),
        "deadlines": user.get("deadlines", []),
        "preferences": user.get("preferences", []),
        "habits": user.get("habits", []),
        "feedback": [f["text"] for f in user.get("feedback", [])],
        "self_learning": [s["signal"] for s in user.get("self_learning", [])],
    }


def get_recent_history(user_id: str, n: int = 5) -> List[Dict[str, Any]]:
    all_data = _load_all()
    user = _ensure_user(all_data, user_id)
    return user.get("history", [])[-n:]


# ----------------- LEARNING CONTEXT (FOR LLM PROMPT) -----------------

def get_learning_context(user_id: str) -> str:
    """
    Combine feedback + self-learning into a single prompt-ready string.
    """
    memories = get_memories_for_prompt(user_id)
    ctx = ""

    for key in ["feedback", "self_learning"]:
        for item in memories.get(key, []):
            ctx += f"- {item}\n"

    return ctx
