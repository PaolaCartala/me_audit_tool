import time
from datetime import datetime

from agents.em_progress_note_agent import main as em_progress_note_agent
from settings import logger


async def main(appointment_id) -> dict:
    """
    Progress Note Agent Activity
    Now calling the actual em_progress_note_agent
    """
    activity_start = time.perf_counter()
    activity_session_id = f"activity_progress_note_{appointment_id}"
    
    logger.debug("🚀 Progress Note Agent Activity: Starting", 
                activity_session_id=activity_session_id,
                appointment_id=str(appointment_id),
                activity_type="progress_note_agent_activity")
    
    try:
        # Call the actual progress note agent with performance tracking
        progress_note_result = await em_progress_note_agent(appointment_id)
        
        # Track activity completion time
        activity_time = time.perf_counter() - activity_start
        
        # Extract performance metrics from progress note agent if available
        # agent_performance = progress_note_result.get('performance_metrics', {})
        # agent_total_time = agent_performance.get('total_execution_time', 0)
        
        result = {
            "progress_note": progress_note_result,
            "timestamp": datetime.now().isoformat(),
            "progress_note_performance": {
                # "agent_execution_time": round(agent_total_time, 2),
                "agent_execution_time": round(activity_time, 2),
                "activity_session_id": activity_session_id,
                "measured_at": datetime.now().isoformat()
            }
        }

        return result

    except Exception as e:
        activity_time = time.perf_counter() - activity_start
        logger.error("❌ Progress Note Agent Activity: Failed", 
                    activity_session_id=activity_session_id,
                    appointment_id=str(appointment_id),
                    error=str(e),
                    error_type=type(e).__name__,
                    activity_time_before_error=activity_time,
                    exc_info=True)
        
        return {
            "appointment_id": str(appointment_id),
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "progress_note_performance": {
                "activity_execution_time": round(activity_time, 2),
                "activity_session_id": activity_session_id,
                "error_occurred": True,
                "measured_at": datetime.now().isoformat()
            }
        }
