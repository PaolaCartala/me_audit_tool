import logging
import json
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df



async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    try:
        # Try to get appointment_id from multiple sources
        appointment_id = req.params.get("appointment_id")
        
        # If not in params, try to get from request body
        if not appointment_id:
            try:
                req_body = req.get_json()
                if req_body:
                    appointment_id = req_body.get("appointment_id")
            except ValueError:
                pass
        
        # If still no appointment_id, use a default for testing
        if not appointment_id:
            appointment_id = "test_appointment_001"
            
        logging.debug(f"📋 Starting progress note generation for appointment: {appointment_id}")

        # Start the orchestration with the appointment_id as input
        instance_id = await client.start_new("em_progress_note_orchestrator", client_input=appointment_id)
        
        logging.debug(f"🎭 Orchestration started with instance ID: {instance_id}, appointment ID: {appointment_id}")
        
        return client.create_check_status_response(req, instance_id)

    except Exception as e:
        logging.error(f"❌ Error starting progress note generation: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to generate progress note", 
                "details": str(e),
                "error_type": type(e).__name__
            }),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/json"
        )
