def document_reasoning(doc_count: int) -> dict:
    return {
        "multi_document": doc_count > 1,
        "force_cross_reference": doc_count > 1,
        "must_mention_documents": doc_count >= 1
    }
