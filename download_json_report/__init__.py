import logging
import json
from datetime import datetime
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df


async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    instance_id = req.route_params.get("instance_id")
    logging.info(f"JSON report download requested for instance ID: {instance_id}")

    status = await client.get_status(instance_id)

    if not status:
        return func.HttpResponse("Orchestration instance not found.", status_code=HTTPStatus.NOT_FOUND)

    if status.runtime_status != df.OrchestrationRuntimeStatus.Completed:
        return func.HttpResponse(
            f"Orchestration has not completed. Current status: {status.runtime_status.value}",
            status_code=HTTPStatus.ACCEPTED
        )

    try:
        # Use the test_summary and results from the orchestrator output
        orchestrator_output = status.output
        test_summary = orchestrator_output.get("test_summary", {})
        results = orchestrator_output.get("results", [])
        
        # Create consolidated JSON exactly like test_quick.py
        consolidated_result = {
            "test_summary": {
                "total_documents": test_summary.get("total_documents", len(results)),
                "successful_documents": test_summary.get("successful_documents", len([r for r in results if "error" not in r])),
                "failed_documents": test_summary.get("failed_documents", len([r for r in results if "error" in r])),
                "test_timestamp": test_summary.get("test_timestamp", datetime.now().isoformat()),
                "test_type": test_summary.get("test_type", "azure_durable_functions_processing"),
                "instance_id": instance_id,
                "total_processing_time_seconds": "N/A",
                "average_time_per_document": "N/A"
            },
            "results": results
        }
        
        json_content = json.dumps(consolidated_result, indent=2, ensure_ascii=False)
        filename = f"audit_results_consolidated_{instance_id[:8]}.json"

        return func.HttpResponse(
            body=json_content,
            status_code=HTTPStatus.OK,
            mimetype="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/json; charset=utf-8"
            }
        )
    except Exception as e:
        logging.error(f"Error processing JSON report for download for instance {instance_id}: {e}")
        return func.HttpResponse("Error processing the JSON report for download.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
