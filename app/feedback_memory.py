# ================= ADVANCED FEEDBACK + RULE MEMORY =================

from collections import defaultdict
import time

# --------------------------------------------------
# RULE STORAGE
# user_id -> rule -> {value, confidence, last_updated}
# --------------------------------------------------
FORCED_RULES = defaultdict(dict)

# --------------------------------------------------
# FEEDBACK HISTORY (LIMITED)
# --------------------------------------------------
FEEDBACK_HISTORY = defaultdict(list)

MAX_HISTORY = 100  # prevent memory overflow

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
DEFAULT_CONFIDENCE = 1.0
DECAY_RATE = 0.02        # slow decay over time
MIN_CONFIDENCE = 0.3     # below this → remove rule


# ==================================================
# STORE FEEDBACK
# ==================================================
def store_feedback(user_id: str, query: str, answer: str, feedback: str):
    FEEDBACK_HISTORY[user_id].append({
        "query": query,
        "answer": answer,
        "feedback": feedback.lower(),
        "time": time.time()
    })

    # limit memory size
    if len(FEEDBACK_HISTORY[user_id]) > MAX_HISTORY:
        FEEDBACK_HISTORY[user_id] = FEEDBACK_HISTORY[user_id][-50:]


# ==================================================
# SET RULE (SMART)
# ==================================================
def set_force_rule(user_id: str, rule: str, value: bool, confidence: float = DEFAULT_CONFIDENCE):
    FORCED_RULES[user_id][rule] = {
        "value": value,
        "confidence": confidence,
        "last_updated": time.time()
    }


# ==================================================
# GET RULE (WITH DECAY)
# ==================================================
def get_force_rule(user_id: str, rule: str):
    rule_data = FORCED_RULES.get(user_id, {}).get(rule)

    if not rule_data:
        return None

    # Apply decay based on time
    time_passed = time.time() - rule_data["last_updated"]
    decay_factor = (1 - DECAY_RATE) ** (time_passed / 60)

    rule_data["confidence"] *= decay_factor

    # remove weak rules
    if rule_data["confidence"] < MIN_CONFIDENCE:
        del FORCED_RULES[user_id][rule]
        return None

    return rule_data["value"]


# ==================================================
# BOOST RULE (POSITIVE FEEDBACK)
# ==================================================
def boost_rule(user_id: str, rule: str, amount: float = 0.5):
    if rule in FORCED_RULES[user_id]:
        FORCED_RULES[user_id][rule]["confidence"] += amount
        FORCED_RULES[user_id][rule]["last_updated"] = time.time()
    else:
        set_force_rule(user_id, rule, True, confidence=amount)


# ==================================================
# WEAKEN RULE (NEGATIVE FEEDBACK)
# ==================================================
def weaken_rule(user_id: str, rule: str, amount: float = 0.3):
    if rule in FORCED_RULES[user_id]:
        FORCED_RULES[user_id][rule]["confidence"] -= amount

        if FORCED_RULES[user_id][rule]["confidence"] < MIN_CONFIDENCE:
            del FORCED_RULES[user_id][rule]


# ==================================================
# AUTO LEARNING FROM FEEDBACK
# ==================================================
def learn_from_feedback(user_id: str):
    data = FEEDBACK_HISTORY[user_id][-5:]  # recent feedback only

    for item in data:
        fb = item["feedback"]

        # -------------------------------
        # POSITIVE SIGNALS
        # -------------------------------
        if "detail" in fb or "explain" in fb:
            boost_rule(user_id, "DETAILED_EXPLANATION")

        if "step" in fb:
            boost_rule(user_id, "STEP_BY_STEP")

        # -------------------------------
        # NEGATIVE SIGNALS
        # -------------------------------
        if "too short" in fb:
            boost_rule(user_id, "DETAILED_EXPLANATION", amount=0.7)

        if "too long" in fb:
            weaken_rule(user_id, "DETAILED_EXPLANATION")

        if "confusing" in fb:
            boost_rule(user_id, "STEP_BY_STEP")

        if "not helpful" in fb:
            weaken_rule(user_id, "DETAILED_EXPLANATION")


# ==================================================
# CLEAR RULE
# ==================================================
def clear_force_rule(user_id: str, rule: str):
    if rule in FORCED_RULES.get(user_id, {}):
        del FORCED_RULES[user_id][rule]


# ==================================================
# GET ALL RULES (FOR UI / DEBUG)
# ==================================================
def get_all_rules(user_id: str):
    return FORCED_RULES.get(user_id, {})