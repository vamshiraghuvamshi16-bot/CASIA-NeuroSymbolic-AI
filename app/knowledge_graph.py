import re
from collections import defaultdict
from typing import List, Dict, Tuple

# -----------------------------
# KNOWLEDGE GRAPH STRUCTURE
# -----------------------------
# GRAPH[entity] = set of (relation, object)
GRAPH: Dict[str, set] = defaultdict(set)

# -----------------------------
# ENTITY EXTRACTION (SYMBOLIC)
# -----------------------------
def extract_entities(text: str) -> List[str]:
    """
    Extract candidate entities using symbolic heuristics.
    Capitalized words + known AI terms.
    """
    entities = set()

    # Capitalized words (simple NER)
    entities.update(re.findall(r"\b[A-Z][a-zA-Z]+\b", text))

    # Domain-specific keywords
    domain_terms = [
        "Transformer", "Attention", "Neural Network",
        "Neural Model", "AI", "Machine Learning",
        "Deep Learning", "LLM"
    ]

    for term in domain_terms:
        if term.lower() in text.lower():
            entities.add(term)

    return list(entities)

# -----------------------------
# RELATION EXTRACTION (RULE-BASED)
# -----------------------------
def extract_relations(text: str, entities: List[str]) -> List[Tuple[str, str, str]]:
    """
    Extract relations using symbolic rules.
    Returns (subject, relation, object)
    """
    relations = []
    t = text.lower()

    for e in entities:
        if e.lower() == "transformer":
            relations.append(("Transformer", "uses", "Attention"))
            relations.append(("Transformer", "is_a", "Neural Model"))

        if "attention" in t and "transformer" in t:
            relations.append(("Attention", "enables", "Context Modeling"))

        if e.lower() == "ai":
            relations.append(("AI", "includes", "Machine Learning"))

        if "machine learning" in t:
            relations.append(("Machine Learning", "is_a", "AI Subfield"))

        if "deep learning" in t:
            relations.append(("Deep Learning", "is_a", "Machine Learning"))

    return relations

# -----------------------------
# GRAPH BUILDER
# -----------------------------
def build_graph_from_text(text: str) -> None:
    """
    Build / update knowledge graph from input text.
    """
    entities = extract_entities(text)
    relations = extract_relations(text, entities)

    for subj, rel, obj in relations:
        GRAPH[subj].add((rel, obj))

# -----------------------------
# GRAPH QUERY
# -----------------------------
def query_graph(entity: str) -> List[Tuple[str, str]]:
    """
    Return relations for an entity.
    """
    return list(GRAPH.get(entity, []))

# -----------------------------
# SYMBOLIC REASONING OVER GRAPH
# -----------------------------
def infer_facts(entity: str) -> List[str]:
    """
    Perform simple symbolic inference.
    """
    inferred = []

    relations = query_graph(entity)

    for rel, obj in relations:
        if rel == "is_a" and obj == "Neural Model":
            inferred.append(f"{entity} is a type of neural model.")

        if rel == "uses" and obj == "Attention":
            inferred.append(f"{entity} relies on attention mechanisms.")

    return inferred

# -----------------------------
# EXPLAINABLE GRAPH TRACE
# -----------------------------
def explain_graph(entity: str) -> str:
    """
    Human-readable explanation of KG reasoning.
    """
    relations = query_graph(entity)
    inferred = infer_facts(entity)

    if not relations and not inferred:
        return "No knowledge graph facts available."

    explanation = "🧠 Knowledge Graph Reasoning:\n"

    if relations:
        explanation += "Stored Facts:\n"
        for r, o in relations:
            explanation += f"- {entity} {r} {o}\n"

    if inferred:
        explanation += "Inferred Facts:\n"
        for f in inferred:
            explanation += f"- {f}\n"

    return explanation.strip()
