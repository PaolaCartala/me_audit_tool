"""
Quick Test Script for Progress Note Generator Agent
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from settings import logger
from agents.em_progress_note_agent import main as em_progress_note_generator_agent
# Load environment variables
load_dotenv()
# Define the test input data
test_input = {
    "transcription": "The patient is a 70-year-old male presenting with chronic left leg pain. Symptoms have persisted for years and have not improved with recent SI joint or caudal epidural injections. Pain starts in the lower back and radiates to the left buttock, thigh, and foot. There is no pain on the right side. Patient experiences increased discomfort with walking and sitting, relieved partially by leaning forward or support. Pain is rated 6/10. He has not participated in PT recently. Currently uses naproxen. No recent imaging reviewed, but prior surgery included L4-L5 TLIF and L3-L4 lateral fusion. The patient will retrieve his MRI for review. An EMG is recommended. Physical exam shows mild tenderness in the lumbar spine, no deformity, full ROM, intact motor and reflexes with minor discrepancies.",
    "patient_name": "Kaider, Eugene J",
    "patient_id": "146205",
    "patient_date_of_birth": "1954-07-18",
    "progress_note_type": "Ortho Follow-Up",
    "patient_data": """
        "Past Medical History": "Arthritis, Diabetes, Hypertension, Hyperlipidemia, History of cancer.",
        "Medications": "Metformin, Rosuvastatin, Norvasc, Hydrochlorothiazide, Naproxen.",
        "Allergies": "NKDA." """
}
async def run_test():
    """
    Run the test for the Progress Note Generator Agent
    """
    start_time = time.time()
    logger.debug("Starting Progress Note Generator Agent test...")

    try:
        # Call the agent with the test input
        result = await em_progress_note_generator_agent(test_input)

        # Log the result
        logger.debug(f"Progress Note Generated: {result['progress_note']}")
        logger.debug(f"Test completed successfully in {time.time() - start_time:.2f} seconds")
        
        # Save the result to a file
        output_file = Path("progress_note_output.json")
        with output_file.open("w") as f:
            json.dump(result, f, indent=4)
        logger.debug(f"Output saved to {output_file}")

    except Exception as e:
        logger.error(f"Error during test: {e}")
if __name__ == "__main__":
    # Run the test in an asyncio event loop
    asyncio.run(run_test())
    logger.debug("Test script completed.")