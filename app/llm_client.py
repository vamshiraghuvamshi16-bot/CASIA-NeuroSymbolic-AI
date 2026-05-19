import os
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
import chromadb

from app.web_search import web_search

# =================================================
# EMBEDDINGS
# =================================================
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# =================================================
# CHROMADB SETUP (replaces faiss)
# =================================================
_chroma_client = chromadb.Client()
_collection = _chroma_client.get_or_create_collection(
    name="casia_docs",
    metadata={"hnsw:space": "l2"}
)

doc_chunks = []

# =================================================
# DOCUMENT INGEST
# =================================================
def ingest_document(text: str):
    global doc_chunks

    # Clear existing collection
    try:
        _chroma_client.delete_collection("casia_docs")
    except Exception:
        pass

    collection = _chroma_client.get_or_create_collection(
        name="casia_docs",
        metadata={"hnsw:space": "l2"}
    )

    doc_chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
    vectors = embedder.encode(doc_chunks).tolist()

    collection.add(
        embeddings=vectors,
        documents=doc_chunks,
        ids=[f"chunk_{i}" for i in range(len(doc_chunks))]
    )


# =================================================
# DOCUMENT RETRIEVAL
# =================================================
def retrieve_from_docs(query: str, k=5, threshold=1.1):
    try:
        collection = _chroma_client.get_collection("casia_docs")
    except Exception:
        return []

    if collection.count() == 0:
        return []

    q_vec = embedder.encode([query]).tolist()

    results = collection.query(
        query_embeddings=q_vec,
        n_results=min(k, collection.count())
    )

    matched = []
    for doc, distance in zip(results["documents"][0], results["distances"][0]):
        if distance <= threshold:
            matched.append(doc)

    return matched


# =================================================
# ORCHESTRATOR (RAG + SYMBOLIC + FORCE RULES)
# =================================================
def orchestrate(
    user_id: str,
    query: str,
    uploaded_text: str = "",
    intent: str = "general",
    disable_web: bool = False,
    force_explain: bool | None = None
):
    document_uploaded = bool(uploaded_text.strip())

    # -------------------------------------------------
    # DOCUMENT INGEST & RETRIEVAL
    # -------------------------------------------------
    if document_uploaded:
        ingest_document(uploaded_text)
        doc_chunks_found = retrieve_from_docs(query)
    else:
        doc_chunks_found = []

    has_doc_answer = len(doc_chunks_found) > 0

    # -------------------------------------------------
    # SYMBOLIC STYLE CONTROL (INTENT)
    # -------------------------------------------------
    style_hint = ""
    if intent == "summarization":
        style_hint = "Provide a concise summary."
    elif intent == "comparison":
        style_hint = "Answer in a clear comparison table."
    elif intent == "explanation":
        style_hint = "Explain step-by-step."
    elif intent == "decision":
        style_hint = "Provide a recommendation with reasoning."

    # -------------------------------------------------
    # SYSTEM PROMPT BASE
    # -------------------------------------------------
    system_prompt = "You are CASIA.\n" + style_hint

    # -------------------------------------------------
    # FORCE-RULE OVERRIDE (ABSOLUTE PRIORITY)
    # -------------------------------------------------
    if force_explain is True:
        system_prompt += (
            "\nIMPORTANT: You MUST give a detailed explanation with examples."
        )
    elif force_explain is False:
        system_prompt += (
            "\nIMPORTANT: Keep the answer short, direct, and concise."
        )

    # -------------------------------------------------
    # CONTEXT SELECTION
    # -------------------------------------------------
    if has_doc_answer:
        context = "\n".join(doc_chunks_found)
        system_prompt += "\nAnswer strictly using the provided document context."
        mode = "DOCUMENT_ANSWER"

    elif document_uploaded:
        context = uploaded_text[:4000]
        system_prompt += (
            "\nThe document does not answer the question. "
            "Provide a clear summary of the document only."
        )
        mode = "DOCUMENT_SUMMARY"

    else:
        context = "" if disable_web else web_search(query)[:3000]
        mode = "GENERAL"

    # -------------------------------------------------
    # FINAL PROMPT
    # -------------------------------------------------
    final_prompt = f"""
CONTEXT:
{context}

QUESTION:
{query}
""".strip()

    # -------------------------------------------------
    # LLM CALL
    # -------------------------------------------------
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt},
        ],
        temperature=0.2,
        max_tokens=700,
    )

    return response.choices[0].message.content, mode
