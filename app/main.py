# ================= CASIA FINAL LEVEL-4 BACKEND =================

from dotenv import load_dotenv
load_dotenv()

import logging
import urllib.parse
from typing import Optional

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("casia-backend")

# ---------------- CASIA CORE ----------------
from app.memory import (
    extract_facts,
    add_history,
    get_memories_for_prompt
)

from app.symbolic_controller import ai_controller
from app.llm_client import orchestrate
from app.hallucination_guard import hallucination_guard
from app.confidence import compute_confidence

# 🔥 NEW IMPORTS (LEVEL 4)
from app.feedback_memory import (
    get_force_rule,
    store_feedback,
    learn_from_feedback,
    get_all_rules
)

print("🔥 CASIA LEVEL-4 BACKEND LOADED (SELF-LEARNING ENABLED)")

# ---------------- FASTAPI APP ----------------
app = FastAPI(title="CASIA – Self-Evolving AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MODELS ----------------
class ChatRequest(BaseModel):
    user_id: str
    message: str
    document_text: str = ""
    feedback: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    metrics: dict = {}


# ---------------- STATE (IMPORTANT) ----------------
LAST_QUERY = {}
LAST_ANSWER = {}

# ---------------- HEALTH ----------------
@app.get("/health")
def health():
    return {"status": "ok"}


# =========================================================
# CHAT ENDPOINT
# =========================================================
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        user_id = request.user_id
        query = request.message.strip()
        document_text = request.document_text.strip()
        doc_uploaded = bool(document_text)

        last_query = LAST_QUERY.get(user_id, "")
        last_answer = LAST_ANSWER.get(user_id, "")

        # =====================================================
        # 🔥 FEEDBACK HANDLING (LEVEL 4 LEARNING)
        # =====================================================
        if not query and request.feedback:
            if last_query and last_answer:
                store_feedback(user_id, last_query, last_answer, request.feedback)
                learn_from_feedback(user_id)

            return ChatResponse(
                reply="🔥 Learned from feedback. Improving automatically.",
                metrics={"mode": "LEARNING"}
            )

        # ---------------- MEMORY ----------------
        extract_facts(user_id, query)
        add_history(user_id, query, "chat")

        memories = get_memories_for_prompt(user_id)

        # ---------------- SYMBOLIC CONTROLLER ----------------
        controller = ai_controller(query)

        intent = controller.get("intent", "general")
        needs_web = controller.get("needs_web", False)
        requires_docs = controller.get("has_documents", False)

        # ---------------- SMART CONTROL ----------------
        if doc_uploaded:
            requires_docs = True
            needs_web = True

        if any(word in query.lower() for word in ["latest", "current", "today", "recent", "real-time"]):
            needs_web = True

        # =====================================================
        # 🔥 APPLY LEARNED RULES BEFORE LLM
        # =====================================================
        force_explain = get_force_rule(user_id, "DETAILED_EXPLANATION")
        step_mode = get_force_rule(user_id, "STEP_BY_STEP")

        if force_explain:
            intent = "explanation"

        if step_mode:
            intent = "explanation"
            query = f"Explain step-by-step:\n{query}"

        # ---------------- DOCUMENT ENFORCEMENT ----------------
        if requires_docs and not doc_uploaded:
            return ChatResponse(
                reply="📎 Please upload the required document to continue.",
                metrics={"mode": "SYMBOLIC_BLOCK"}
            )

        print("RAG USED:", doc_uploaded)
        print("WEB USED:", needs_web)

        # ---------------- LLM ----------------
        answer, mode = orchestrate(
            user_id=user_id,
            query=query,
            uploaded_text=document_text,
            intent=intent,
            disable_web=False if needs_web else True,
            force_explain=force_explain
        )

        # 🔥 STORE LAST (CRITICAL FOR LEARNING)
        LAST_QUERY[user_id] = query
        LAST_ANSWER[user_id] = answer

        # ---------------- SAFETY ----------------
        safe = hallucination_guard(
            query,
            has_rag=doc_uploaded,
            used_web=needs_web
        )

        if not safe:
            return ChatResponse(
                reply="⚠️ I can’t safely answer that.",
                metrics={"mode": "BLOCKED"}
            )

        # ---------------- CONFIDENCE ----------------
        conf = compute_confidence(
            answer_primary=answer,
            answer_secondary=answer[: max(80, int(len(answer) * 0.6))],
            intent=intent,
            memory_used=bool(memories),
            doc_used=doc_uploaded,
            rag_used=doc_uploaded,
            web_used=needs_web,
            refused=False
        )

        # ---------------- METRICS ----------------
        return ChatResponse(
            reply=answer,
            metrics={
                "mode": mode,
                "intent": intent,

                "confidence": conf["confidence"],
                "confidence_level": conf["confidence_level"],

                "rag_used": doc_uploaded,
                "web_used": needs_web,

                "learning_active": True,
                "rules_active": get_all_rules(user_id),

                "safety_score": 1.0 if safe else 0.0
            }
        )

    except Exception:
        logger.exception("🔥 Backend crashed")
        return ChatResponse(
            reply="⚠️ Internal server error. Please try again.",
            metrics={"mode": "ERROR"}
        )


# =========================================================
# IMAGE GENERATION (UNCHANGED)
# =========================================================

import requests
import base64

@app.post("/generate-image")
async def generate_image(payload: dict = Body(...)):
    prompt = payload.get("prompt", "").strip()

    if not prompt:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Empty image prompt"}
        )

    encoded_prompt = urllib.parse.quote_plus(prompt)

    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024"

    try:
        response = requests.get(pollinations_url, timeout=10)

        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode("utf-8")

            return {
                "success": True,
                "image_base64": image_base64,
                "provider": "pollinations"
            }

    except Exception:
        logger.warning("Pollinations failed")

    fallback = f"https://source.unsplash.com/1024x1024/?{encoded_prompt}"

    return {
        "success": True,
        "image_url": fallback,
        "provider": "unsplash"
    }