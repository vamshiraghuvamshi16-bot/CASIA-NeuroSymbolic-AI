# ================= CASIA FINAL STABLE BACKEND =================

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
from app.feedback_memory import get_force_rule, set_force_rule

print("🔥 CASIA BACKEND LOADED (FORCE-RULE SELF-LEARNING ENABLED)")

# ---------------- FASTAPI APP ----------------
app = FastAPI(title="CASIA – Neuro-Symbolic Backend")

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

        # ---------------- HANDLE FEEDBACK ----------------
        if not query and request.feedback:
            set_force_rule(user_id, "DETAILED_EXPLANATION", True)

            return ChatResponse(
                reply="✅ Feedback received. CASIA will adapt.",
                metrics={"mode": "FEEDBACK"}
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

        # ---------------- FORCE RULES ----------------
        force_explain = get_force_rule(user_id, "DETAILED_EXPLANATION")
        force_no_rag = get_force_rule(user_id, "NO_DOCUMENT_MODE")
        force_no_web = get_force_rule(user_id, "NO_WEB")

        if force_explain is True:
            intent = "explanation"
        elif force_explain is False and intent == "explanation":
            intent = "general"

        if force_no_rag:
            requires_docs = False
            doc_uploaded = False

        if force_no_web:
            needs_web = False

        # ---------------- DOCUMENT ENFORCEMENT ----------------
        if requires_docs and not doc_uploaded:
            return ChatResponse(
                reply="📎 Please upload the required document to continue.",
                metrics={"mode": "SYMBOLIC_BLOCK"}
            )

        # ---------------- LLM ORCHESTRATION ----------------
        answer, mode = orchestrate(
            user_id=user_id,
            query=query,
            uploaded_text=document_text,
            intent=intent,
            disable_web=not needs_web,
            force_explain=force_explain
        )

        # ---------------- SAFETY CHECK ----------------
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

        # ---------------- CONFIDENCE ENGINE ----------------
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

        # ---------------- EXPLAINABILITY METRICS ----------------
        explainability_score = (
            1.0 if intent == "explanation"
            else 0.8 if memories
            else 0.6 if doc_uploaded
            else 0.4
        )

        trace_score = (
            1.0 if memories
            else 0.8 if doc_uploaded
            else 0.6 if needs_web
            else 0.3
        )

        # ---------------- RESPONSE ----------------
        return ChatResponse(
            reply=answer,
            metrics={
                "mode": mode,
                "intent": intent,

                "confidence": conf["confidence"],
                "confidence_level": conf["confidence_level"],
                "confidence_breakdown": conf["confidence_breakdown"],

                "rag_used": doc_uploaded,
                "web_used": needs_web,
                "force_explain": force_explain,

                "safety_score": 1.0 if safe else 0.0,

                "explainability_score": explainability_score,
                "trace_score": trace_score
            }
        )

    except Exception:
        logger.exception("🔥 Backend crashed")
        return ChatResponse(
            reply="⚠️ Internal server error. Please try again.",
            metrics={"mode": "ERROR"}
        )


# =========================================================
# IMAGE GENERATION
# =========================================================
@app.post("/generate-image")
async def generate_image(payload: dict = Body(...)):
    prompt = payload.get("prompt", "").strip()

    if not prompt:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Empty image prompt"}
        )

    encoded_prompt = urllib.parse.quote_plus(prompt)

    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

    return {
        "success": True,
        "image_url": image_url,
        "provider": "pollinations"
    }