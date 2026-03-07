from typing import Dict
from difflib import SequenceMatcher



# Confidence Level

def _confidence_level(score: float) -> str:
    if score >= 0.80:
        return "High"
    elif score >= 0.60:
        return "Medium"
    return "Low"



# Source Reliability

def _source_reliability(*, memory_used, doc_used, rag_used, web_used) -> float:
    if web_used:
        return 0.95
    if rag_used:
        return 0.90
    if doc_used:
        return 0.85
    if memory_used:
        return 0.80
    return 0.40



# Intent Certainty

def _intent_certainty(intent: str) -> float:
    intent_map = {
        "PERSONAL": 0.85,
        "FACTUAL": 0.85,
        "ACADEMIC": 0.80,
        "OPINION": 0.60,
        "CREATIVE": 0.55
    }
    return intent_map.get(intent.upper(), 0.40)



# Answer Stability

def _answer_stability(a1: str, a2: str) -> float:
    if not a1 or not a2:
        return 0.40
    return round(SequenceMatcher(None, a1, a2).ratio(), 2)



# ULTRA Emotion / Assertiveness Scoring 🔥

def _emotional_confidence(answer: str) -> float:
    strong_confidence = [
        "your name is", "this is", "it is", "will be", "confirmed",
        "verified", "definitely", "clearly", "exactly", "no doubt",
        "certainly", "guaranteed"
    ]

    weak_confidence = [
        "maybe", "might", "could", "possibly", "i think", "i feel",
        "i believe", "not sure", "uncertain", "seems like", "appears"
    ]

    empathy_or_softening = [
        "i understand", "i'm sorry", "it depends", "can vary",
        "in some cases", "generally"
    ]

    text = answer.lower()
    score = 0.65  # neutral emotional baseline

    # Strong assertive language boosts confidence
    for phrase in strong_confidence:
        if phrase in text:
            score += 0.08

    # Hesitation words reduce confidence sharply
    for phrase in weak_confidence:
        if phrase in text:
            score -= 0.12

    # Emotional softening slightly reduces certainty
    for phrase in empathy_or_softening:
        if phrase in text:
            score -= 0.05

    return max(0.30, min(round(score, 2), 1.0))



# MAIN CONFIDENCE ENGINE (FINAL)

def compute_confidence(
    *,
    answer_primary: str,
    answer_secondary: str,
    intent: str,
    memory_used: bool = False,
    doc_used: bool = False,
    rag_used: bool = False,
    web_used: bool = False,
    refused: bool = False
) -> Dict[str, object]:
    """
    Ultra Emotion-Aware Explainable Confidence Engine (CASIA)
    """

    if refused:
        return {
            "confidence": 0.10,
            "confidence_level": "Low",
            "confidence_breakdown": {},
            "explanation": "Response refused due to safety or policy rules"
        }

    emotion_score = _emotional_confidence(answer_primary)
    source_score = _source_reliability(
        memory_used=memory_used,
        doc_used=doc_used,
        rag_used=rag_used,
        web_used=web_used
    )
    intent_score = _intent_certainty(intent)
    stability_score = _answer_stability(answer_primary, answer_secondary)

    #  FINAL WEIGHTED CONFIDENCE (EMOTION DOMINATES)
    final_score = round(
        (0.40 * emotion_score) +
        (0.25 * source_score) +
        (0.20 * intent_score) +
        (0.15 * stability_score),
        2
    )

    final_score = max(0.0, min(final_score, 1.0))

    return {
        "confidence": final_score,
        "confidence_level": _confidence_level(final_score),
        "confidence_breakdown": {
            "emotional_assertiveness": emotion_score,
            "source_reliability": source_score,
            "intent_certainty": intent_score,
            "answer_stability": stability_score
        },
        "explanation": (
            "Confidence primarily driven by emotional assertiveness of the response, "
            "with supporting signals from data source, intent clarity, and stability"
        )
    }
