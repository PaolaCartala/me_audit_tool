import logging
import json
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df



async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    try:
        appointment_id = req.params.get("appointment_id")
        if not appointment_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing appointment_id parameter"}),
                status_code=HTTPStatus.BAD_REQUEST,
                mimetype="application/json"
            )

        logging.debug(f"📋 Starting progress note generation for appointment: {appointment_id}")
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
