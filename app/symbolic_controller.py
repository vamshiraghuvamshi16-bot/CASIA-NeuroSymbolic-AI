

import re

# -------------------------------------------------
# INTENT DETECTION
# -------------------------------------------------

def detect_intent(text: str) -> str:
    t = text.lower()

    if any(k in t for k in ["compare", "vs", "difference"]):
        return "comparison"
    if any(k in t for k in ["summarize", "summary"]):
        return "summarization"
    if any(k in t for k in ["recommend", "should i", "decide"]):
        return "decision"
    if any(k in t for k in ["why", "explain", "what is", "define"]):
        return "explanation"

    return "general"


# -------------------------------------------------
# AI CONTROLLER (RULE-BASED SYMBOLIC LOGIC)
# -------------------------------------------------

def ai_controller(user_text: str) -> dict:
    t = user_text.lower()
    intent = detect_intent(user_text)

    controller = {
        "intent": intent,
        "doc_count": 0,
        "has_documents": False,
        "needs_web": False,
        "output_format": "general",
    }

    # -------- EXPLICIT DOCUMENT REFERENCES --------
    explicit_docs = re.findall(r"\[document\s+\d+", t)
    if explicit_docs:
        controller["doc_count"] = len(explicit_docs)

    # -------- IMPLICIT DOCUMENT SIGNALS --------
    doc_keywords = [
        "doc", "docs", "document", "documents",
        "file", "files", "uploaded", "provided",
        "notes", "materials", "dataset", "text",
    ]

    if any(k in t for k in doc_keywords):
        controller["doc_count"] = max(controller["doc_count"], 1)

    # -------- CONTENT-BASED DOCUMENT TRIGGERS --------
    content_triggers = [
        "according to", "based on", "from the",
        "mentioned", "discussed", "explained", "described",
    ]

    if any(k in t for k in content_triggers):
        controller["doc_count"] = max(controller["doc_count"], 1)

    # -------- WEB SEARCH TRIGGER --------
    if any(k in t for k in ["latest", "current", "today", "news", "2024", "2025"]):
        controller["needs_web"] = True

    controller["has_documents"] = controller["doc_count"] > 0
    return controller


# -------------------------------------------------
# 🔒 SECRET / CONFIDENTIAL POLICY (NEW)
# -------------------------------------------------

SECRET_KEYWORDS = [
    "password",
    "secret",
    "api key",
    "apikey",
    "token",
    "access key",
    "private key",
    "credentials",
    "confidential",
    "system prompt",
    "internal rules",
    "backend code",
    "database password",
]

def is_secret_request(text: str) -> bool:
    """
    Detects whether the user is asking for secrets,
    credentials, or internal/private information.
    """
    t = text.lower()
    return any(k in t for k in SECRET_KEYWORDS)


def enforce_secret_policy(text: str) -> dict:
    """
    Hard symbolic block.
    LLM / RAG / Web is NEVER called if triggered.
    """
    if is_secret_request(text):
        return {
            "blocked": True,
            "reply": (
                "🚫 I can’t help with secrets, credentials, "
                "or confidential/internal information."
            ),
            "metrics": {
                "confidence": 1.0,
                "rag_used": False,
                "web_used": False,
                "safety_score": 1.0,
                "trace_score": 1.0,
                "explainability_score": 1.0,
                "blocked_by": "SECRET_POLICY"
            }
        }

    return {"blocked": False}


# -------------------------------------------------
# IDENTITY ENFORCEMENT
# -------------------------------------------------

def enforce_identity(text: str) -> bool:
    """
    Triggers ONLY when the user asks about CASIA's identity.
    Does NOT trigger on self-introductions.
    """
    t = text.lower().strip()

    if t.startswith(("i am ", "my name is ", "i'm ")):
        return False

    identity_patterns = [
        r"\bwhat is your name\b",
        r"\bwho are you\b",
        r"\bwhat are you\b",
        r"\byour name\b",
        r"\bai name\b",
    ]

    return any(re.search(p, t) for p in identity_patterns)


# -------------------------------------------------
# SELF-INTRODUCTION DETECTION
# -------------------------------------------------

def detect_self_intro(text: str) -> str | None:
    """
    Detects: 'i am raghu', 'i'm raghu', 'my name is raghu'
    Returns the name if found.
    """
    t = text.lower().strip()
    match = re.match(r"(i am|i'm|my name is)\s+([a-zA-Z]+)", t)

    if match:
        return match.group(2).capitalize()

    return None
