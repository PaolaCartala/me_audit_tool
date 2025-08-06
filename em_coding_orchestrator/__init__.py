import azure.durable_functions as df
import logging
from datetime import datetime
from utils.html_processor import parse_payload_to_eminput


def orchestrator_function(context: df.DurableOrchestrationContext):
    payload = context.get_input()
    logging.info(f"Processing payload for document: {payload['document'].get('id', 'N/A')}")

    try:
        # Parse the HTML payload to EMInput format
        em_input = parse_payload_to_eminput(payload)
        logging.info(f"Successfully parsed document: {em_input.document_id}")
        
        # Convert EMInput to dict for passing to activities
        document_data = {
            "document_id": em_input.document_id,
            "patient_name": em_input.patient_name,
            "patient_id": em_input.patient_id,
            "date_of_service": em_input.date_of_service,
            "provider": em_input.provider,
            "text": em_input.text,
            "original_text_length": len(em_input.text)
        }

        # Process document through enhancement agent
        enhancement_result = yield context.call_activity("enhancement_agent_activity", document_data)
        
        # Process through auditor agent
        final_result = yield context.call_activity("auditor_agent_activity", enhancement_result)
        
        # Generate Excel report
        excel_b64 = yield context.call_activity("excel_export_activity", [final_result])
        
        # Return consolidated results similar to test_quick.py structure
        return {
            "test_summary": {
                "total_documents": 1,
                "successful_documents": 1 if "error" not in final_result else 0,
                "failed_documents": 1 if "error" in final_result else 0,
                "test_timestamp": datetime.now().isoformat(),
                "test_type": "azure_durable_functions_processing"
            },
            "results": [final_result],
            "excel_report_base64": excel_b64
        }
        
    except Exception as e:
        logging.error(f"Error in orchestrator: {str(e)}")
        error_result = {
            "document_id": payload['document'].get('id', 'N/A'),
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "test_summary": {
                "total_documents": 1,
                "successful_documents": 0,
                "failed_documents": 1,
                "test_timestamp": datetime.now().isoformat(),
                "test_type": "azure_durable_functions_processing"
            },
            "results": [error_result],
            "excel_report_base64": None
        }

main = orchestrator_function
