import azure.functions as func
import azure.durable_functions as df

# Import all function handlers
from health import main as health_main
from start_orchestration_from_samples import main as start_orchestration_from_samples_main
from start_orchestration_from_body import main as start_orchestration_from_body_main
from download_report import main as download_report_main
from download_json_report import main as download_json_report_main
from em_coding_orchestrator import main as em_coding_orchestrator_main
from enhancement_agent_activity import main as enhancement_agent_activity_main
from auditor_agent_activity import main as auditor_agent_activity_main
from excel_export_activity import main as excel_export_activity_main

app = func.FunctionApp()

# HTTP Triggers
@app.function_name("health")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return health_main(req)

@app.function_name("start_orchestration_from_samples")
@app.route(route="orchestrations/from-samples", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
def start_orchestration_from_samples(req: func.HttpRequest, client) -> func.HttpResponse:
    return start_orchestration_from_samples_main(req, client)

@app.function_name("start_orchestration_from_body")
@app.route(route="orchestrations", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
def start_orchestration_from_body(req: func.HttpRequest, client) -> func.HttpResponse:
    return start_orchestration_from_body_main(req, client)

@app.function_name("download_report")
@app.route(route="reports/excel/{instance_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
def download_report(req: func.HttpRequest, client) -> func.HttpResponse:
    return download_report_main(req, client)

@app.function_name("download_json_report")
@app.route(route="reports/json/{instance_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
def download_json_report(req: func.HttpRequest, client) -> func.HttpResponse:
    return download_json_report_main(req, client)

# Orchestrator
@app.function_name("em_coding_orchestrator")
@app.orchestration_trigger(context_name="context")
def em_coding_orchestrator(context: df.DurableOrchestrationContext):
    return em_coding_orchestrator_main(context)

# Activities
@app.function_name("enhancement_agent_activity")
@app.activity_trigger(input_name="document")
def enhancement_agent_activity(document: dict) -> dict:
    return enhancement_agent_activity_main(document)

@app.function_name("auditor_agent_activity")
@app.activity_trigger(input_name="enhancement_data")
def auditor_agent_activity(enhancement_data: dict) -> dict:
    return auditor_agent_activity_main(enhancement_data)

@app.function_name("excel_export_activity")
@app.activity_trigger(input_name="final_results")
def excel_export_activity(final_results: list) -> str:
    return excel_export_activity_main(final_results)
