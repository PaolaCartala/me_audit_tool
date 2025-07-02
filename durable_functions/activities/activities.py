
import os
import logging
from dotenv import load_dotenv
from models.pydantic_models import EMInput, em_enhancement_agent
from azure.functions import FunctionApp

load_dotenv()

app = FunctionApp()

@app.activity_trigger(input_name="doc")
def main(doc: dict) -> dict:
    """
    Activity function: evaluates a single progress note using PydanticAI and Azure OpenAI GPT-4.1
    """
    try:
        # Validate and parse input
        em_input = EMInput(**doc)
        # Prepare prompt and run enhancement agent
        result = em_enhancement_agent.run_sync(f"""
        Document ID: {em_input.document_id}\nDate of Service: {em_input.date_of_service}\nProvider: {em_input.provider}\n\nMedical Progress Note:\n{em_input.text}
        """)
        # Return structured result
        return {
            "document_id": em_input.document_id,
            "date_of_service": em_input.date_of_service,
            "provider": em_input.provider,
            "assigned_code": result.data.assigned_code,
            "justification": result.data.justification,
            "recommendations": {
                "99212": result.data.code_recommendations.code_99212,
                "99213": result.data.code_recommendations.code_99213,
                "99214": result.data.code_recommendations.code_99214,
                "99215": result.data.code_recommendations.code_99215
            }
        }
    except Exception as e:
        logging.error(f"Activity error: {str(e)}")
        return {"error": str(e)}
