import logging
import json
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df

from data.pdf_processor import process_pdf_samples


async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    logging.info("Orchestration start from samples requested.")
    try:
        limit_str = req.params.get('limit')
        limit = int(limit_str) if limit_str and limit_str.isdigit() else None

        sample_inputs = process_pdf_samples(limit=limit)

        if not sample_inputs:
            return func.HttpResponse(
                json.dumps({"message": "No sample PDF files were found or processed."}),
                status_code=HTTPStatus.NOT_FOUND,
                mimetype="application/json"
            )

        documents = [doc.model_dump() for doc in sample_inputs]
        instance_id = await client.start_new("em_coding_orchestrator", client_input=documents)
        logging.info(f"Orchestration started from samples with ID: {instance_id}")

        return client.create_check_status_response(req, instance_id)

    except Exception as e:
        logging.error(f"Error starting orchestration from samples: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to process sample files.", "details": str(e)}),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/json"
        )
