import logging
from datetime import datetime

from subagents.em_progress_note_agent import main as em_progress_note_agent
from models.pydantic_models import EMProgressNoteGeneratorInput


async def main(data) -> dict:
    try:
        progress_note_result = await em_progress_note_agent(data)
        result = {
            "progress_note": progress_note_result,
            "timestamp": datetime.now().isoformat(),
        }
        return result

    except Exception as e:
        logging.error(f"Error in Progress Note Activity for {data}: {e}")
        return {
            "patient_id": data,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
