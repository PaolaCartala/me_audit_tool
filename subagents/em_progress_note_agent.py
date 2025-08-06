import os
import logging

import azure.functions as func
from dotenv import load_dotenv

from models.pydantic_models import EMProgressNoteGeneratorInput, EMProgressNoteGeneratorOutput, em_progress_note_generator_agent
from settings import logger

# Load environment variables
load_dotenv()


async def main(input_payload: dict) -> dict:
    """
    E/M Progress Note Generator Agent
    Generates a compliant medical progress note based on physician transcription and structured patient information.
    """
    try:
        # Parse input
        data = EMProgressNoteGeneratorInput(
            transcription=input_payload["transcription"],
            patient_name=input_payload["patient_name"],
            patient_id=input_payload["patient_id"],
            patient_date_of_birth=input_payload["patient_date_of_birth"],
            progress_note_type=input_payload["progress_note_type"],
            patient_data=input_payload["patient_data"],
        )
        
        logger.debug(f"📝 Progress Note Agent: Generating note for patient {data.patient_name} (ID: {data.patient_id})")
        
        # Prepare context for the AI agent
        user_prompt = f"""
        TRANSCRIPTION:
        {data.transcription}
        
        PATIENT INFORMATION:
        Name: {data.patient_name}
        ID: {data.patient_id}
        Date of Birth: {data.patient_date_of_birth}
        Progress Note Type: {data.progress_note_type}
        Additional Data: {data.patient_data}
        
        TASK: Generate a compliant medical progress note using the provided transcription and patient information.
        """
        
        logger.debug(f"🧠 Progress Note Agent: Sending prompt to AI model...")
        
        # Run the PydanticAI agent
        result = await em_progress_note_generator_agent.run(user_prompt)
        
        logger.debug(f"✅ Progress Note Agent: Received generated note from AI model")
        
        # Return structured response
        response = EMProgressNoteGeneratorOutput(
            progress_note=result.output.progress_note
        ).model_dump()
        
        logger.debug(f"🎉 Progress Note Agent: Successfully generated note for patient {data.patient_name}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in Progress Note Generator Agent: {str(e)}")
        raise