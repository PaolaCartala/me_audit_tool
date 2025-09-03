import azure.functions as func
import azure.durable_functions as df

# Health
from durable_functions.health import main as health_main
# Processing agents
from durable_functions.start_orchestration_from_body import main as start_orchestration_from_body_main
from durable_functions.download_json_report import main as download_json_report_main
from durable_functions.em_coding_orchestrator import main as em_coding_orchestrator_main
from durable_functions.enhancement_agent_activity import main as enhancement_agent_activity_main
from durable_functions.auditor_agent_activity import main as auditor_agent_activity_main
# Progress Note
from durable_functions.start_progress_note_from_id import main as progress_note_from_id_main
from durable_functions.em_progress_note_orchestrator import main as em_progress_note_orchestrator_main
from durable_functions.progress_note_agent_activity import main as progress_note_agent_activity_main
# Feedback endpoints
from durable_functions.submit_feedback import main as submit_feedback_main
from durable_functions.get_feedback_analytics import main as get_feedback_analytics_main


app = func.FunctionApp()

# HTTP Triggers
@app.function_name("health")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return health_main(req)

@app.function_name("start_orchestration_from_body")
@app.route(route="orchestrations", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
def start_orchestration_from_body(req: func.HttpRequest, client) -> func.HttpResponse:
    return start_orchestration_from_body_main(req, client)

@app.function_name("download_json_report")
@app.route(route="reports/json/{instance_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
def download_json_report(req: func.HttpRequest, client) -> func.HttpResponse:
    return download_json_report_main(req, client)

@app.function_name("progress_note_from_id")
@app.route(route="progress-notes", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
def progress_note_from_id(req: func.HttpRequest, client) -> func.HttpResponse:
    return progress_note_from_id_main(req, client)

@app.function_name("submit_feedback")
@app.route(route="feedback", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def submit_feedback(req: func.HttpRequest) -> func.HttpResponse:
    return submit_feedback_main(req)

@app.function_name("get_feedback_analytics")
@app.route(route="feedback/analytics", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_feedback_analytics(req: func.HttpRequest) -> func.HttpResponse:
    return get_feedback_analytics_main(req)

# Orchestrator
@app.function_name("em_coding_orchestrator")
@app.orchestration_trigger(context_name="context")
def em_coding_orchestrator(context: df.DurableOrchestrationContext):
    return em_coding_orchestrator_main(context)

@app.function_name("em_progress_note_orchestrator")
@app.orchestration_trigger(context_name="context")
def em_progress_note_orchestrator(context: df.DurableOrchestrationContext):
    return em_progress_note_orchestrator_main(context)

# Activities
@app.function_name("enhancement_agent_activity")
@app.activity_trigger(input_name="document")
async def enhancement_agent_activity(document: dict) -> dict:
    return await enhancement_agent_activity_main(document)

@app.function_name("auditor_agent_activity")
@app.activity_trigger(input_name="enhancement_data")
async def auditor_agent_activity(enhancement_data: dict) -> dict:
    return await auditor_agent_activity_main(enhancement_data)

@app.function_name("progress_note_agent_activity")
@app.activity_trigger(input_name="appointment_id")
async def progress_note_agent_activity(appointment_id: str) -> dict:
    return await progress_note_agent_activity_main(appointment_id)
