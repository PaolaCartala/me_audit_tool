import logging
from datetime import datetime
from models.pydantic_models import em_auditor_agent


async def main(enhancement_data: dict) -> dict:
    doc_id = enhancement_data.get('document_id', 'N/A')
    logging.info(f"🕵️ Auditor Agent Activity: Starting for document {doc_id}")
    
    try:
        # Check if enhancement_data has error
        if "error" in enhancement_data:
            logging.warning(f"⚠️ Passing through error from enhancement agent for {doc_id}")
            return enhancement_data  # Pass through the error
        
        # Create auditor prompt similar to test_quick.py
        enhancement_agent_data = enhancement_data.get('enhancement_agent', {})
        
        auditor_prompt = f"""
        Patient Information:
        - Patient Name: {enhancement_data.get('patient_name')}
        - Patient ID: {enhancement_data.get('patient_id')}
        - Date of Service: {enhancement_data.get('date_of_service')}
        - Provider: {enhancement_data.get('provider')}
        
        Original Progress Note:
        {enhancement_data.get('original_text_preview', '')}
        
        Enhancement Agent Results:
        - Assigned Code: {enhancement_agent_data.get('assigned_code')}
        - Justification: {enhancement_agent_data.get('justification')}
        - Code Recommendations:
          * 99212: {enhancement_agent_data.get('code_recommendations', {}).get('code_99212', '')}
          * 99213: {enhancement_agent_data.get('code_recommendations', {}).get('code_99213', '')}
          * 99214: {enhancement_agent_data.get('code_recommendations', {}).get('code_99214', '')}
          * 99215: {enhancement_agent_data.get('code_recommendations', {}).get('code_99215', '')}
        
        Please audit this analysis for compliance and provide final recommendations.
        """
        
        logging.info(f"🧠 Running auditor agent for document: {doc_id}")
        auditor_result = await em_auditor_agent.run(auditor_prompt)
        
        # Combine enhancement and auditor results similar to test_quick.py structure
        final_result = {
            "document_id": enhancement_data.get('document_id'),
            "patient_name": enhancement_data.get('patient_name'),
            "patient_id": enhancement_data.get('patient_id'),
            "date_of_service": enhancement_data.get('date_of_service'),
            "provider": enhancement_data.get('provider'),
            "original_text_length": enhancement_data.get('original_text_length'),
            "original_text_preview": enhancement_data.get('original_text_preview'),
            "enhancement_agent": enhancement_data.get('enhancement_agent'),
            "auditor_agent": {
                "final_assigned_code": auditor_result.output.final_assigned_code,
                "final_justification": auditor_result.output.final_justification,
                "audit_flags": auditor_result.output.audit_flags,
                "billing_ready_note": auditor_result.output.billing_ready_note,
                "confidence": auditor_result.output.confidence.model_dump(),
                "code_evaluations": {
                    "code_99212_evaluation": auditor_result.output.code_evaluations.code_99212_evaluation,
                    "code_99213_evaluation": auditor_result.output.code_evaluations.code_99213_evaluation,
                    "code_99214_evaluation": auditor_result.output.code_evaluations.code_99214_evaluation,
                    "code_99215_evaluation": auditor_result.output.code_evaluations.code_99215_evaluation,
                }
            },
            "timestamp": datetime.now().isoformat(),
            "processing_metadata": {
                "enhancement_agent_model": "Azure OpenAI GPT-4.1 (embedded guidelines)",
                "auditor_agent_model": "Azure OpenAI GPT-4.1 (embedded guidelines)",
                "processing_time": datetime.now().isoformat(),
                "guidelines_method": "embedded_in_prompt",
                "tools_used": False
            }
        }
        
        logging.info(f"✅ Auditor agent completed successfully for document: {doc_id}")
        return final_result
        
    except Exception as e:
        logging.error(f"❌ Error in Auditor Activity for {doc_id}: {e}")
        import traceback
        logging.error(f"🔍 Traceback: {traceback.format_exc()}")
        
        return {
            "document_id": doc_id,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
