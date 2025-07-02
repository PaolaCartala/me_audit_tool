def orchestrator_function(context: df.DurableOrchestrationContext):
import os
import logging
from dotenv import load_dotenv
import azure.durable_functions as df
from azure.functions import FunctionApp

load_dotenv()

app = FunctionApp()

@app.orchestration_trigger(context_name="context")
def main(context: df.DurableOrchestrationContext):
    # Scatter: fan-out to activity for each document
    documents = context.get_input()
    tasks = []
    for doc in documents:
        tasks.append(context.call_activity('EvaluateProgressNoteActivity', doc))
    results = yield context.task_all(tasks)

    # Call Excel export activity with all results
    excel_b64 = yield context.call_activity('ExcelExport', results)

    # Gather: return all results and Excel as base64
    return {
        "results": results,
        "excel_base64": excel_b64
    }
