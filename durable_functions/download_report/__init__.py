import logging
import base64
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df


async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    instance_id = req.route_params.get("instance_id")
    logging.debug(f"Report download requested for instance ID: {instance_id}")

    status = await client.get_status(instance_id)

    if not status:
        return func.HttpResponse("Orchestration instance not found.", status_code=HTTPStatus.NOT_FOUND)

    if status.runtime_status != df.OrchestrationRuntimeStatus.Completed:
        return func.HttpResponse(
            f"Orchestration has not completed. Current status: {status.runtime_status.value}",
            status_code=HTTPStatus.ACCEPTED
        )

    try:
        b64_excel = status.output.get("excel_report_base64")
        if not b64_excel:
            raise ValueError("Base64 Excel report not found in orchestration output.")

        excel_bytes = base64.b64decode(b64_excel)
        filename = f"audit_report_{instance_id[:8]}.xlsx"

        return func.HttpResponse(
            body=excel_bytes,
            status_code=HTTPStatus.OK,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logging.error(f"Error processing file for download for instance {instance_id}: {e}")
        return func.HttpResponse("Error processing the report for download.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
