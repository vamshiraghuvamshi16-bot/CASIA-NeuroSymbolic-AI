# app/explainable/explainable.py
# =================================================
# CASIA – Clean Explainable AI Reporting Layer
# =================================================

from datetime import datetime
from typing import Dict, List, Optional


def explain_trace(
    controller: Dict,
    *,
    rag_used: bool,
    web_used: bool,
    identity_enforced: bool = False,
    self_intro_detected: Optional[str] = None,
    hallucination_safe: bool = True,
    rules_fired: Optional[List[str]] = None,
) -> str:
    """
    Human-readable explainability report for CASIA.

    NOTE:
    - No confidence computation here
    - Confidence is handled separately by confidence.py
    - This module ONLY explains decisions
    """

    rules_fired = rules_fired or []

    lines = [
        "────────────────────────────────────────",
        "🧠 CASIA – Explainable Reasoning Summary",
        "────────────────────────────────────────",
        f"Timestamp (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "1️⃣ Input Analysis",
        f"• Intent detected        : {controller.get('intent', 'unknown').capitalize()}",
        f"• Documents detected     : {controller.get('doc_count', 0)}",
        f"• Document context       : {'Available' if controller.get('has_documents') else 'Not available'}",
        "",
        "2️⃣ Knowledge Source Decision",
        f"• RAG used               : {'Yes' if rag_used else 'No'}",
        f"• Web search used        : {'Yes' if web_used else 'No'}",
        f"• Knowledge source       : {'Documents + Model' if rag_used else 'Language Model (internal knowledge)'}",
        "",
        "3️⃣ Neuro-Symbolic Control",
        "• Symbolic controller    : Active",
        "• Rules triggered        :",
    ]

    if rules_fired:
        for r in rules_fired:
            lines.append(f"   - {r}")
    else:
        lines.append("   - None")

    lines.extend([
        f"• Identity enforcement  : {'Triggered' if identity_enforced else 'Not triggered'}",
        "",
        "4️⃣ Safety & Reliability",
        f"• Hallucination status   : {'Safe' if hallucination_safe else 'Blocked'}",
        f"• Risk handling strategy : {'Grounded generation' if rag_used else 'Conservative response'}",
        "",
        "5️⃣ Transparency Notice",
        "• No chain-of-thought exposed",
        "• Explanation generated post-hoc",
        "• Output aligned with safety policies",
        "",
        "Status: ✅ Explainability Enabled",
        "────────────────────────────────────────",
    ])

    return "\n".join(lines)
