import azure.functions as func

def evaluate_progress_note_activity(doc):
    # TODO: Implement logic to evaluate a single progress note and return recommendations
    # This should use PydanticAI and OpenAI GPT-4.1 as described in the PRD
    # Return a dict with Document ID, Date of Service, Provider, and recommendations for each E&M code
    return {
        "document_id": doc.get("document_id"),
        "date_of_service": doc.get("date_of_service"),
        "provider": doc.get("provider"),
        "em_codes": [
            {"code": "99212", "recommendation": "TODO"},
            {"code": "99213", "recommendation": "TODO"},
            {"code": "99214", "recommendation": "TODO"},
            {"code": "99215", "recommendation": "TODO"}
        ]
    }
