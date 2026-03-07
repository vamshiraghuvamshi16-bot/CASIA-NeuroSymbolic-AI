def safety_check(user_text: str) -> dict:
    t = user_text.lower()

    medical = any(k in t for k in ["diagnosis", "medicine", "treatment"])
    legal = any(k in t for k in ["legal advice", "court", "law"])

    return {
        "medical": medical,
        "legal": legal,
        "needs_disclaimer": medical or legal
    }
