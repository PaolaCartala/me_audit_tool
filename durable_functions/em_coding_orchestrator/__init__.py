import azure.durable_functions as df
from datetime import datetime

from settings import logger


def orchestrator_function(context: df.DurableOrchestrationContext):
    # Use durable context for orchestration
    orchestration_id = context.instance_id
    # orchestration_start_time = context.current_utc_datetime
    
    document = context.get_input()
    
    context.set_custom_status("Starting document processing")
    logger.debug("🚀 OPTIMIZED EM Coding Pipeline: Request Ingested", 
                orchestration_id=orchestration_id,
                document_id=str(document)[:50],
                pipeline_tracking="enabled")

    # Process documents through OPTIMIZED enhancement agent
    context.set_custom_status("Starting enhancement agent")
    enhancement_tasks = [context.call_activity("enhancement_agent_activity", document)]
    
    # Track actual enhancement execution time
    enhancement_results = yield context.task_all(enhancement_tasks)
    
    logger.debug("⏱️ OPTIMIZED Enhancement Phase Complete", 
                orchestration_id=orchestration_id,
                process="optimized_enhancement_phase",
                results_count=len(enhancement_results))
    context.set_custom_status("Enhancement agent completed")
    
    # Process through OPTIMIZED auditor agent
    context.set_custom_status("Starting auditor agent")
    audit_tasks = [context.call_activity("auditor_agent_activity", result) for result in enhancement_results]
    
    # Track actual auditor execution time
    final_results = yield context.task_all(audit_tasks)
    
    logger.debug("⏱️ OPTIMIZED Audit Phase Complete", 
                orchestration_id=orchestration_id,
                process="optimized_audit_phase",
                results_count=len(final_results))
    context.set_custom_status("Auditor agent completed")
    
    # Generate Excel report
    # excel_start = time.perf_counter()
    # excel_b64 = yield context.call_activity("excel_export_activity", final_results)
    # excel_duration = time.perf_counter() - excel_start
    
    # logger.debug("⏱️ Excel Export Complete", 
    #             orchestration_id=orchestration_id,
    #             duration_seconds=excel_duration,
    #             process="excel_export_phase")
    
    # Calculate comprehensive performance metrics using agent data
    # enhancement_agent_metrics = enhancement_results[0].get('enhancement_performance', {}) if enhancement_results else {}
    # audit_agent_metrics = final_results[0].get('audit_performance', {}) if final_results else {}
    
    # Extract actual execution times from agents
    enhancement_agent_time = enhancement_results[0].get('enhancement_agent', {}).get('performance_metrics', {}).get('total_execution_time', 0) if enhancement_results else 0
    auditor_agent_time = final_results[0].get('auditor_agent', {}).get('performance_metrics', {}).get('total_execution_time', 0) if final_results else 0
    
    # Calculate total flow execution time from agent data
    total_flow_execution_time = enhancement_agent_time + auditor_agent_time
    
    # Count successful and failed documents
    successful_docs = len([r for r in final_results if not r.get('error')])
    failed_docs = len(final_results) - successful_docs

    # Process results to add document metadata only where needed (top level)
    processed_results = []
    for result in final_results:
        processed_result = {
            "enhancement_agent": result.get('enhancement_agent'),
            "auditor_agent": result.get('auditor_agent'),
            "timestamp": result.get('timestamp'),
            "enhancement_performance": result.get('enhancement_performance'),
            "audit_performance": result.get('audit_performance')
        }
        processed_results.append(processed_result)

    logger.debug("🏁 OPTIMIZED Pipeline Complete - COMPREHENSIVE PERFORMANCE SUMMARY",
               orchestration_id=orchestration_id,
               total_flow_execution_time=total_flow_execution_time,
               successful_documents=successful_docs,
               failed_documents=failed_docs)
    
    logger.debug("🏁 EM Coding Orchestrator: Complete - PERFORMANCE SUMMARY", 
                orchestration_id=orchestration_id,
                total_execution_time=round(total_flow_execution_time, 2),
                successful_documents=successful_docs,
                failed_documents=failed_docs,
                performance_breakdown={
                    "enhancement_phase": {
                        "duration": round(enhancement_agent_time, 2),
                        "percentage": f"{round((enhancement_agent_time / total_flow_execution_time) * 100 if total_flow_execution_time > 0 else 0, 2)}%"
                    },
                    "audit_phase": {
                        "duration": round(auditor_agent_time, 2),
                        "percentage": f"{round((auditor_agent_time / total_flow_execution_time) * 100 if total_flow_execution_time > 0 else 0, 2)}%"
                    }
                })
    
    # Return consolidated results with simple performance metrics
    context.set_custom_status("E/M Coding pipeline completed")
    return {
        "processed_documents": len(final_results),
        "successful_documents": successful_docs,
        "failed_documents": failed_docs,
        "processing_timestamp": datetime.now().isoformat(),
        "results": processed_results,
        "performance": {
            "orchestration_id": orchestration_id,
            "enhancement_agent_time": round(enhancement_agent_time, 2),
            "auditor_agent_time": round(auditor_agent_time, 2),
            "total_flow_execution_time": round(total_flow_execution_time, 2)
        }
    }


main = orchestrator_function
