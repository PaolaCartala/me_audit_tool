import azure.durable_functions as df
from datetime import datetime


def orchestrator_function(context: df.DurableOrchestrationContext):
    input_data = context.get_input()
    
    try:
        # Log the orchestrator start
        context.set_custom_status("Starting progress note generation")
        
        # Call the progress note agent activity
        progress_note_result = yield context.call_activity("progress_note_agent_activity", input_data)
        
        context.set_custom_status("Progress note generation completed")
        
        # Return consolidated results
        return {
            "processed_documents": 1,
            "successful_documents": 1 if "error" not in progress_note_result else 0,
            "failed_documents": 1 if "error" in progress_note_result else 0,
            "processing_timestamp": datetime.now().isoformat(),
            "results": [progress_note_result],
        }
        
    except Exception as e:
        context.set_custom_status(f"Error: {str(e)}")
        return {
            "processed_documents": 1,
            "successful_documents": 0,
            "failed_documents": 1,
            "processing_timestamp": datetime.now().isoformat(),
            "error": str(e),
            "results": []
        }

main = orchestrator_function
