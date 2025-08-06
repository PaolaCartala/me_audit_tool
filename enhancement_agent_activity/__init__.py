import logging
from datetime import datetime
from models.pydantic_models import EMInput, em_enhancement_agent


async def main(document_data: dict) -> dict:
    doc_id = document_data.get('document_id', 'N/A')
    logging.info(f"🤖 Enhancement Agent Activity: Starting for document {doc_id}")
    
    try:
        # Create enhancement prompt similar to test_quick.py
        enhancement_prompt = f"""
        Document ID: {document_data['document_id']}
        Patient Name: {document_data['patient_name']}
        Patient ID: {document_data['patient_id']}
        Date of Service: {document_data['date_of_service']}
        Provider: {document_data['provider']}
        
        Progress Note:
        {document_data['text']}
        
        Please analyze this progress note and assign the most appropriate E/M code with justifications.
        """
        
        logging.info(f"🧠 Running enhancement agent for document: {doc_id}")
        enhancement_result = await em_enhancement_agent.run(enhancement_prompt)
        
        # Create combined result with original document data
        combined_result = {
            "document_id": document_data['document_id'],
            "patient_name": document_data['patient_name'],
            "patient_id": document_data['patient_id'],
            "date_of_service": document_data['date_of_service'],
            "provider": document_data['provider'],
            "original_text_length": len(document_data['text']),
            "original_text_preview": document_data['text'],
            "enhancement_agent": {
                "assigned_code": enhancement_result.output.assigned_code,
                "justification": enhancement_result.output.justification,
                "code_recommendations": {
                    "code_99212": enhancement_result.output.code_recommendations.code_99212,
                    "code_99213": enhancement_result.output.code_recommendations.code_99213,
                    "code_99214": enhancement_result.output.code_recommendations.code_99214,
                    "code_99215": enhancement_result.output.code_recommendations.code_99215,
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logging.info(f"✅ Enhancement agent completed successfully for document: {doc_id}")
        return combined_result
        
    except Exception as e:
        logging.error(f"❌ Error in Enhancement Activity for {doc_id}: {e}")
        import traceback
        logging.error(f"🔍 Traceback: {traceback.format_exc()}")
        
        return {
            "document_id": doc_id,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
