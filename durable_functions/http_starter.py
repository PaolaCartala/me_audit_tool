import azure.functions as func
import azure.durable_functions as df
import json

def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    try:
        documents = req.get_json()
        if not isinstance(documents, list):
            return func.HttpResponse(
                json.dumps({"error": "Input must be a list of documents"}),
                status_code=400,
                mimetype="application/json"
            )
        instance_id = client.start_new("orchestrator_function", None, documents)
        return client.create_check_status_response(req, instance_id)
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
