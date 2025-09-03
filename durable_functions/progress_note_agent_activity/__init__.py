import time
from datetime import datetime

from agents.em_progress_note_agent import generate_progress_note
from settings import logger


def main(appointment_id: str) -> str:
    start_time = time.time()
    
    logger.debug("🎯 Progress Note Agent Activity: Starting", 
                appointment_id=str(appointment_id),
                activity_start_time=start_time)
    
    try:
        result = generate_progress_note(appointment_id)
        
        duration = time.time() - start_time
        logger.debug("🎯 Progress Note Agent Activity: Completed successfully", 
                    appointment_id=str(appointment_id),
                    duration_seconds=duration)
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error("🎯 Progress Note Agent Activity: Error occurred", 
                    appointment_id=str(appointment_id),
                    error=str(e),
                    duration_seconds=duration,
                    exc_info=True)
        
        return {
            "status": "failed",
            "error": str(e),
            "appointment_id": str(appointment_id),
            "timestamp": datetime.now().isoformat()
        }
