import logging
import time
from datetime import datetime

from agents.optimized_em_auditor_agent import main as optimized_auditor_agent_main
from settings import logger


async def main(enhancement_data: dict) -> dict:
    # Track activity execution time
    activity_start = time.perf_counter()
    doc_id = enhancement_data.get('enhancement_agent', {}).get('document_id', 'N/A')
    activity_session_id = f"opt_activity_auditor_{doc_id}"
    
    logger.debug("🚀 OPTIMIZED Auditor Agent Activity: Starting", 
                activity_session_id=activity_session_id,
                document_id=str(doc_id)[:50],
                activity_type="optimized_auditor_agent_activity",
                has_enhancement_data=bool(enhancement_data.get('enhancement_agent')))
    
    try:
        # Check if enhancement_data has error
        if "error" in enhancement_data:
            logger.warning("⚠️ Auditor Agent Activity: Received error from enhancement, passing through",
                          activity_session_id=activity_session_id,
                          error=enhancement_data.get('error'))
            return enhancement_data  # Pass through the error
        
        # Run OPTIMIZED auditor agent on the enhancement agent results with performance tracking
        auditor_result = await optimized_auditor_agent_main(enhancement_data.get('enhancement_agent', {}))
        
        # Track activity completion time
        activity_time = time.perf_counter() - activity_start
        
        # Simple result structure - let orchestrator handle final formatting
        result = {
            "enhancement_agent": enhancement_data.get('enhancement_agent'),
            "auditor_agent": auditor_result,
            "timestamp": datetime.now().isoformat(),
            "audit_performance": {
                "activity_execution_time": round(activity_time, 2),
                "activity_session_id": activity_session_id,
                "agent_execution_time": round(auditor_result.get('performance_metrics', {}).get('total_execution_time', 0), 2),
            }
        }
        
        logger.debug("🏁 OPTIMIZED Auditor Agent Activity: Complete", 
                   activity_session_id=activity_session_id,
                   activity_execution_time=round(activity_time, 2),
                   document_id=str(doc_id)[:50],
                   final_code=auditor_result.get('final_assigned_code', 'unknown'),
                   confidence_score=f"{round(auditor_result.get('confidence', {}).get('score', 0), 2)}%",
                   audit_flags_count=len(auditor_result.get('audit_flags', [])),
                   optimization_applied=True)
        
        return result
        
    except Exception as e:
        activity_time = time.perf_counter() - activity_start
        logger.error("❌ OPTIMIZED Auditor Agent Activity: Failed", 
                    activity_session_id=activity_session_id,
                    document_id=str(doc_id)[:50],
                    error=str(e),
                    error_type=type(e).__name__,
                    activity_time_before_error=activity_time,
                    optimization_applied=True,
                    exc_info=True)
        return {
            "document_id": doc_id,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "audit_performance": {
                "activity_execution_time": round(activity_time, 2),
                "activity_session_id": activity_session_id,
                "error_occurred": True,
            }
        }
