import time
from datetime import datetime

from agents.optimized_em_enhancement_agent import main as optimized_enhancement_agent_main
from settings import logger


async def main(document_id) -> dict:
    # Track activity execution time
    activity_start = time.perf_counter()
    activity_session_id = f"opt_activity_enhancement_{document_id}"
    
    logger.debug("🚀 OPTIMIZED Enhancement Agent Activity: Starting", 
                activity_session_id=activity_session_id,
                document_id=str(document_id)[:50],
                activity_type="optimized_enhancement_agent_activity")
    
    try:
        # Run the OPTIMIZED enhancement agent with performance tracking
        enhancement_result = await optimized_enhancement_agent_main(document_id)
        
        # Track activity completion time
        activity_time = time.perf_counter() - activity_start
        
        # Simple result structure - let orchestrator handle final formatting
        combined_result = {
            "enhancement_agent": enhancement_result,
            "timestamp": datetime.now().isoformat(),
            "enhancement_performance": {
                "agent_execution_time": round(enhancement_result.get('performance_metrics', {}).get('total_execution_time', 0), 2),
                "activity_wrapper_time": round(activity_time, 2),
                "activity_session_id": activity_session_id
            }
        }
        
        logger.debug("🏁 OPTIMIZED Enhancement Agent Activity: Complete", 
                   activity_session_id=activity_session_id,
                   activity_execution_time=round(activity_time, 2),
                   document_id=str(document_id)[:50],
                   assigned_code=enhancement_result.get('assigned_code', 'unknown'),
                   agent_time=round(enhancement_result.get('performance_metrics', {}).get('total_execution_time', 0), 2),
                   optimization_applied=True)
        
        return combined_result
        
    except Exception as e:
        activity_time = time.perf_counter() - activity_start
        logger.error("❌ Enhancement Agent Activity: Failed", 
                    activity_session_id=activity_session_id,
                    document_id=str(document_id)[:50],
                    error=str(e),
                    error_type=type(e).__name__,
                    activity_time_before_error=activity_time,
                    exc_info=True)
        return {
            "document_id": document_id,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "enhancement_performance": {
                "activity_execution_time": round(activity_time, 2),
                "activity_session_id": activity_session_id,
                "error_occurred": True
            }
        }
