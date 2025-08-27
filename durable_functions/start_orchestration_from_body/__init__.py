import logging
import json
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df


async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    logging.debug("Orchestration start from request body received.")
    try:
        document_id = req.params.get("document_id")

        instance_id = await client.start_new("em_coding_orchestrator", client_input=document_id)
        logging.debug(f"Orchestration started with ID: {instance_id}")
        return client.create_check_status_response(req, instance_id)

    except Exception as e:
        logging.error(f"Error starting orchestration: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Could not start the orchestration process.", "details": str(e)}),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/json"
        )
