import os
import time
from datetime import datetime

import azure.functions as func
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerSSE

from agents.models.pydantic_models import EMProgressNoteGeneratorInput
from agents.models.progress_note_models import (
    StructuredProgressNote,
    get_optimized_progress_note_agent
)
from settings import logger

# Load environment variables
load_dotenv()


async def main(input_payload: dict) -> dict:
    """
    E/M Progress Note Generator Agent
    Generates a compliant medical progress note based on physician transcription and structured patient information.
    """
    start_time = time.perf_counter()
    session_id = f"progress_note_{input_payload}"
    
    logger.debug("🚀 Progress Note Agent: Starting execution", 
                session_id=session_id,
                appointment_id=str(input_payload))
    
    try:
        # Track MCP server connection time
        mcp_connection_start = time.perf_counter()
        server = MCPServerSSE(url=os.getenv("MCP_API_URL"), headers={"X-API-Key": os.getenv("MCP_API_KEY")})
        mcp_connection_time = time.perf_counter() - mcp_connection_start
        
        logger.debug("⏱️ MCP Server Connection", 
                    session_id=session_id,
                    duration_seconds=mcp_connection_time,
                    process="mcp_server_connection")
        
        async with server:
            # Track tools listing time
            tools_start = time.perf_counter()
            tools = await server.list_tools()
            tools_time = time.perf_counter() - tools_start
            
            logger.debug("⏱️ MCP List Tools", 
                        session_id=session_id,
                        duration_seconds=tools_time,
                        process="mcp_list_tools",
                        tools_count=len(tools))
            
            logger.debug(f"🔧 Available tools: {tools}")
            
            # Track appointment dictation call time
            api_call_start = time.perf_counter()
            response = await server.call_tool(tool_name="appointment-dictation", arguments={"appointmentId": input_payload})
            api_call_time = time.perf_counter() - api_call_start
            
            logger.debug("⏱️ MCP Appointment Dictation Call", 
                       session_id=session_id,
                       duration_seconds=api_call_time,
                       process="mcp_appointment_dictation_call",
                       appointment_id=str(input_payload))
            
            # Track data extraction and parsing time
            parsing_start = time.perf_counter()
            
            # Parse input
            dictation_data = response.get("dictation", {})
            file_content = dictation_data.get("fileContent", {})
            
            transcription = file_content.get("data", "")
            patient_name = dictation_data.get("patientName", "Unknown Patient")
            patient_id = dictation_data.get("patientId", "")
            patient_date_of_birth = dictation_data.get("patientDateOfBirth", "")
            date_of_service = dictation_data.get("dateOfService", "")
            provider = dictation_data.get("provider", "")
            created_by = dictation_data.get("createdBy", "")
            creation_date = dictation_data.get("creationDate", "")
            progress_note_type = dictation_data.get("dictationTypeName", "Progress Note")
            is_new_patient = dictation_data.get("isNewPatient")
            
            data = EMProgressNoteGeneratorInput(
                transcription=transcription,
                patient_name=patient_name, 
                patient_id=patient_id,
                patient_date_of_birth=patient_date_of_birth,
                date_of_service=date_of_service,
                provider=provider,
                progress_note_type=progress_note_type,
                created_by=created_by,
                creation_date=creation_date,
                is_new_patient=is_new_patient
            )
            
            parsing_time = time.perf_counter() - parsing_start
            
            logger.debug("⏱️ Data Extraction & Parsing", 
                        session_id=session_id,
                        duration_seconds=parsing_time,
                        process="data_extraction_parsing",
                        transcription_length=len(data.transcription),
                        patient_id=data.patient_id)
            
            logger.debug(f"📝 Progress Note Agent: Generating note for patient {data.patient_name} (ID: {data.patient_id})")
            logger.debug(f"👤 Patient type: {'New' if data.is_new_patient else 'Established' if data.is_new_patient is False else 'Unknown'}")
            
            # Track prompt preparation time
            prompt_start = time.perf_counter()
            user_prompt = f"""
            PATIENT INFORMATION:
            Name: {data.patient_name}
            ID: {data.patient_id}
            Date of Birth: {data.patient_date_of_birth}
            Date of Service: {data.date_of_service}
            Provider: {data.provider}
            Progress Note Type: {data.progress_note_type}
            Created By: {data.created_by}
            Creation Date: {data.creation_date}
            Patient Type: {'New Patient' if data.is_new_patient else 'Established Patient' if data.is_new_patient is False else 'Unknown'}
            
            TRANSCRIPTION:
            {data.transcription}
            """
            prompt_time = time.perf_counter() - prompt_start
            
            logger.debug("⏱️ Prompt Preparation", 
                        session_id=session_id,
                        duration_seconds=prompt_time,
                        process="prompt_preparation",
                        prompt_length=len(user_prompt),
                        transcription_length=len(data.transcription))
            
            logger.debug(f"🧠 Progress Note Agent: Sending prompt to AI model...")
            
            # Track agent initialization time
            agent_init_start = time.perf_counter()
            agent = get_optimized_progress_note_agent()
            agent_init_time = time.perf_counter() - agent_init_start
            
            logger.debug("⏱️ Agent Initialization", 
                        session_id=session_id,
                        duration_seconds=agent_init_time,
                        process="agent_initialization",
                        agent_type="progress_note_generator")
            
            # Track AI model inference time
            inference_start = time.perf_counter()
            ai_result = await agent.run(user_prompt)
            inference_time = time.perf_counter() - inference_start
            
            logger.debug(f"✅ Progress Note Agent: Received structured note from optimized AI model")
            
            # Track response formatting time
            formatting_start = time.perf_counter()
            
            # Extract structured data from agent result
            structured_data = ai_result.output
            
            response = structured_data.model_dump()
            
            formatting_time = time.perf_counter() - formatting_start
            
            logger.debug("⏱️ Response Formatting", 
                        session_id=session_id,
                        duration_seconds=formatting_time,
                        process="response_formatting",
                        is_structured=True)
            
            total_time = time.perf_counter() - start_time
            
            response.update({
                # "performance_metrics": {
                #     "total_execution_time": round(total_time, 2),
                #     # "api_call_time": round(api_call_time, 2),
                #     # "parsing_time": round(parsing_time, 2),
                #     # "agent_init_time": round(agent_init_time, 2),
                #     # "inference_time": round(inference_time, 2),
                #     # "formatting_time": round(formatting_time, 2),
                #     # "measured_at": datetime.now().isoformat(),
                #     # "error_occurred": False
                # },
                "meta": {
                    "session_id": session_id,
                    "agent_type": "progress_note_generator",
                    "model_used": "optimized_structured_agent",
                    "structured_output_enabled": True,
                }
            })
            
            logger.debug(f"🎉 Progress Note Agent: Successfully generated note for patient {data.patient_name}")
            return response
  
    except Exception as e:
        total_time = time.perf_counter() - start_time
        logger.error("❌ Progress Note Agent: execution Failed", 
                    session_id=session_id,
                    error=str(e),
                    total_time_before_error=total_time,
                    exc_info=True)
        
        # Fallback response
        return {
            "appointment_id": str(input_payload),
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "patient_name": "Error - Unable to retrieve",
            "patient_id": str(input_payload),
            "performance_metrics": {
                "session_id": session_id,
                "total_execution_time": round(total_time, 2),
                "measured_at": datetime.now().isoformat(),
                "error_occurred": True
            },
            "timestamp": datetime.now().isoformat()
        }
