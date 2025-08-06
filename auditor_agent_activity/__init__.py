import logging
from datetime import datetime

from subagents.em_auditor_agent import main as auditor_agent_main


async def main(enhancement_data: dict) -> dict:
    doc_id = enhancement_data.get('document_id', 'N/A')
    logging.info(f"Running Auditor Agent for document: {doc_id}")
    
    try:
        # Check if enhancement_data has error
        if "error" in enhancement_data:
            return enhancement_data  # Pass through the error
        
        # Run auditor agent on the enhancement agent results
        auditor_result = await auditor_agent_main(enhancement_data.get('enhancement_agent', {}))
        
        # Combine enhancement and auditor results similar to test_quick.py structure
        final_result = {
            "enhancement_agent": enhancement_data.get('enhancement_agent'),
            "auditor_agent": auditor_result,
            "timestamp": datetime.now().isoformat(),
            "processing_metadata": {
                "enhancement_agent_model": "Azure OpenAI GPT-4.1",
                "auditor_agent_model": "Azure OpenAI GPT-4.1",
                "processing_time": datetime.now().isoformat()
            }
        }
        
        return final_result
        
    except Exception as e:
        logging.error(f"Error in Auditor Activity for {doc_id}: {e}")
        return {
            "document_id": doc_id,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
