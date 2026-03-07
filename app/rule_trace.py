# ================= RULE TRACE (SYMBOLIC-AWARE) =================

def rule_trace(controller: dict):
    """
    Generates explainable rule trace from symbolic controller output
    """
    rules = []

    if controller.get("has_documents"):
        rules.append({
            "rule": "DOCUMENT_REQUIRED",
            "severity": "HIGH"
        })

    if controller.get("needs_web"):
        rules.append({
            "rule": "WEB_ALLOWED",
            "severity": "MEDIUM"
        })
    else:
        rules.append({
            "rule": "WEB_BLOCKED",
            "severity": "LOW"
        })

    intent = controller.get("intent")
    if intent:
        rules.append({
            "rule": f"INTENT_{intent.upper()}",
            "severity": "INFO"
        })

    return rules
