import logging
import json
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df


async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    logging.info("Orchestration start from request body received.")
    try:
        # Get the complete payload from the request body
        try:
            payload = req.get_json()
            if not payload:
                return func.HttpResponse(
                    json.dumps({"error": "Request body is required with document payload"}),
                    status_code=HTTPStatus.BAD_REQUEST,
                    mimetype="application/json"
                )
        except ValueError as e:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body", "details": str(e)}),
                status_code=HTTPStatus.BAD_REQUEST,
                mimetype="application/json"
            )

        # Validate payload structure
        if "document" not in payload:
            return func.HttpResponse(
                json.dumps({"error": "Payload must contain 'document' field"}),
                status_code=HTTPStatus.BAD_REQUEST,
                mimetype="application/json"
            )

        logging.info(f"Starting orchestration for document: {payload['document'].get('id', 'N/A')}")
        
        # Start orchestration with the complete payload
        instance_id = await client.start_new("em_coding_orchestrator", client_input=payload)
        logging.info(f"Orchestration started with ID: {instance_id}")
        return client.create_check_status_response(req, instance_id)

    except Exception as e:
        logging.error(f"Error starting orchestration: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Could not start the orchestration process.", "details": str(e)}),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/json"
        )
