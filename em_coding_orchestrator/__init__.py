import azure.durable_functions as df
from datetime import datetime


def orchestrator_function(context: df.DurableOrchestrationContext):
    document = context.get_input()

    # Process documents through enhancement agent
    enhancement_tasks = [context.call_activity("enhancement_agent_activity", document)]
    enhancement_results = yield context.task_all(enhancement_tasks)
    
    # Process through auditor agent
    audit_tasks = [context.call_activity("auditor_agent_activity", result) for result in enhancement_results]
    final_results = yield context.task_all(audit_tasks)
    
    # Generate Excel report
    excel_b64 = yield context.call_activity("excel_export_activity", final_results)
    
    # Return consolidated results similar to test_quick.py structure
    return {
        "processed_documents": len(final_results),
        "successful_documents": len([r for r in final_results if "error" not in r]),
        "failed_documents": len([r for r in final_results if "error" in r]),
        "processing_timestamp": datetime.now().isoformat(),
        "results": final_results,
        "excel_report_base64": excel_b64
    }

main = orchestrator_function
