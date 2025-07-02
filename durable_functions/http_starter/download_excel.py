def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
import os
import logging
from dotenv import load_dotenv
import azure.functions as func
import azure.durable_functions as df
import base64
import json
from azure.functions import FunctionApp

load_dotenv()

app = FunctionApp()

@app.http_trigger(route="download_excel", methods=["GET"])
def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    instance_id = req.params.get("instanceId") or req.route_params.get("instanceId")
    if not instance_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing instanceId parameter"}),
            status_code=400,
            mimetype="application/json"
        )
    status = client.get_status(instance_id)
    if not status or not status.output:
        return func.HttpResponse(
            json.dumps({"error": "Orchestration not complete or no output"}),
            status_code=404,
            mimetype="application/json"
        )
    output = status.output
    excel_b64 = output.get("excel_base64")
    if not excel_b64:
        return func.HttpResponse(
            json.dumps({"error": "No Excel file found in output"}),
            status_code=404,
            mimetype="application/json"
        )
    excel_bytes = base64.b64decode(excel_b64)
    return func.HttpResponse(
        body=excel_bytes,
        status_code=200,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=em_evaluation_results.xlsx"}
    )
