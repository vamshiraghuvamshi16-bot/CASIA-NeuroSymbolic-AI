import re
import time
from datetime import datetime

CURRENT_YEAR = datetime.now().year


# -------------------------------------------------
# NORMALIZATION
# -------------------------------------------------
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text


# -------------------------------------------------
# SECRET INTENT WORDS
# -------------------------------------------------
SECRET_WORDS = [
    "secret",
    "hidden",
    "confidential",
    "classified",
    "undisclosed",
    "internal",
    "private",
    "restricted",
    "not public",
    "unknown",
    "leaked",
    "behind the scenes",
]


# -------------------------------------------------
# SECRET INTENT PHRASES
# -------------------------------------------------
SECRET_PATTERNS = [
    r"things .* nobody knows",
    r"something .* people .* dont know",
    r"unknown .* strategy",
    r"internal .* strategy",
    r"hidden .* plan",
    r"secret .* plan",
    r"confidential .* information",
    r"government .* hiding",
    r"what .* they .* dont tell .* public",
]


# -------------------------------------------------
# ENTITY WORDS (generic)
# -------------------------------------------------
ENTITIES = [
    "government",
    "military",
    "army",
    "intelligence",
    "company",
    "bank",
    "organization",
    "agency",
    "corporation",
    "politicians",
]


# -------------------------------------------------
# FUTURE YEAR DETECTION
# -------------------------------------------------
def detect_future_year(text):

    years = re.findall(r"\b20\d{2}\b", text)

    for y in years:
        if int(y) > CURRENT_YEAR:
            return True

    return False


# -------------------------------------------------
# SECRET ENTITY DETECTION
# -------------------------------------------------
def detect_secret_entity(text):

    for entity in ENTITIES:
        if entity in text:
            for secret in SECRET_WORDS:
                if secret in text:
                    return True

    return False


# -------------------------------------------------
# MAIN GUARD
# -------------------------------------------------
def hallucination_guard(user_text: str, has_rag: bool, used_web: bool):

    text = normalize(user_text)

    # ---------------------------------------------
    # RULE 1 — Future information
    # ---------------------------------------------
    if detect_future_year(text):
        time.sleep(2)
        return False

    # ---------------------------------------------
    # RULE 2 — Secret keyword intent
    # ---------------------------------------------
    for word in SECRET_WORDS:
        if word in text:
            time.sleep(2)
            return False

    # ---------------------------------------------
    # RULE 3 — Secret phrase patterns
    # ---------------------------------------------
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text):
            time.sleep(2)
            return False

    # ---------------------------------------------
    # RULE 4 — Entity + secret combination
    # ---------------------------------------------
    if detect_secret_entity(text):
        time.sleep(3)
        return False

    # ---------------------------------------------
    # RULE 5 — Unsourced statistics
    # ---------------------------------------------
    if "statistics" in text or "exact data" in text:
        if not has_rag and not used_web:
            time.sleep(2)
            return False

    return True