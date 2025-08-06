import logging
from datetime import datetime

from subagents.em_enhancement_agent import main as enhancement_agent_main


async def main(document_id) -> dict:
    logging.info(f"Running Enhancement Agent for document: {document_id}")
    try:
        enhancement_result = await enhancement_agent_main(document_id)
        
        # Create a structure similar to test_quick.py that includes original document data
        combined_result = {
            "enhancement_agent": enhancement_result,
            "timestamp": datetime.now().isoformat()
        }
        
        return combined_result
        
    except Exception as e:
        logging.error(f"Error in Enhancement Activity for {document_id}: {e}")
        return {
            "document_id": document_id,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
