import azure.durable_functions as df
from datetime import datetime

from settings import logger


def orchestrator_function(context: df.DurableOrchestrationContext):
    # Get the input data passed to the orchestrator
    appointment_id = context.get_input()
    
    logger.debug("🎭 Progress Note Orchestrator: Starting", 
                orchestrator_instance_id=context.instance_id,
                appointment_id=str(appointment_id))

    try:
        # Log the orchestrator start
        context.set_custom_status("Starting progress note generation")
        logger.debug("🎭 Progress Note Orchestrator: About to call activity", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    activity_name="progress_note_agent_activity")
        
        # Call the progress note agent activity with the appointment_id
        progress_note_result = yield context.call_activity("progress_note_agent_activity", appointment_id)
        
        logger.debug("🎭 Progress Note Orchestrator: Activity completed", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    activity_result_type=type(progress_note_result).__name__)
        
        context.set_custom_status("Progress note generation completed")
        
        logger.debug("🎭 Progress Note Orchestrator: Completed successfully", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    has_result=bool(progress_note_result))
        
        # Return consolidated results
        return {
            "processed_documents": 1,
            "successful_documents": 1 if "error" not in str(progress_note_result) else 0,
            "failed_documents": 1 if "error" in str(progress_note_result) else 0,
            "processing_timestamp": datetime.now().isoformat(),
            "orchestrator_instance_id": context.instance_id,
            "appointment_id": str(appointment_id),
            "results": [progress_note_result],
        }
        
    except Exception as e:
        context.set_custom_status(f"Error: {str(e)}")
        
        logger.error("🎭 Progress Note Orchestrator: Failed", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    error=str(e),
                    exc_info=True)
        
        return {
            "processed_documents": 1,
            "successful_documents": 0,
            "failed_documents": 1,
            "processing_timestamp": datetime.now().isoformat(),
            "orchestrator_instance_id": context.instance_id,
            "appointment_id": str(appointment_id),
            "error": str(e),
            "results": []
        }

main = orchestrator_function
