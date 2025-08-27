import os
import time
import json
from datetime import datetime

import azure.functions as func
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerSSE

from agents.models.optimized_pydantic_models import (
    OptimizedEMInput, 
    OptimizedEMEnhancementOutput, 
    get_optimized_em_enhancement_agent
)
from settings import logger

# Load environment variables
load_dotenv()


async def main(input_payload) -> dict:
    """
    Optimized E/M Enhancement Agent - Stage D
    Minimal output: only assigned_code and justification
    Optimized for speed with reduced prompts and aggressive timeouts
    """
    # Track overall execution time
    start_time = time.perf_counter()
    session_id = f"opt_enhancement_{input_payload}"
    
    logger.debug("🚀 Optimized Enhancement Agent: Starting execution", 
                session_id=session_id,
                document_id=str(input_payload)[:50])
    
    try:
        # Track MCP server connection time with aggressive timeout
        mcp_start = time.perf_counter()
        server = MCPServerSSE(
            url=os.getenv("MCP_API_URL"), 
            headers={"X-API-Key": os.getenv("MCP_API_KEY")},
            timeout=8.0  # Aggressive MCP timeout
        )
        mcp_connection_time = time.perf_counter() - mcp_start
        
        logger.debug("⏱️ MCP Server Connection", 
                    session_id=session_id,
                    duration_seconds=mcp_connection_time,
                    process="mcp_server_connection")
        
        async with server:
            # Track progress note retrieval time
            api_call_start = time.perf_counter()
            response = await server.call_tool(
                tool_name="appointment-progressnote", 
                arguments={"documentId": input_payload}
            )
            api_call_time = time.perf_counter() - api_call_start
            
            logger.debug("⏱️ MCP Progress Note Call", 
                       session_id=session_id,
                       duration_seconds=api_call_time,
                       process="mcp_progress_note_call",
                       document_id=str(input_payload)[:50])

        logger.debug(f"Received document for analysis: {response['document']['id']}")
        
        # Track data extraction and parsing time (optimized)
        parsing_start = time.perf_counter()
        doc = response.get("document", {})
        
        # patient type string to boolean: "new" -> True, "established" -> False
        patient_type_str = response.get("isNewPatient", "established")
        is_new_patient = patient_type_str.lower() == "new"
        
        data = OptimizedEMInput(
            document_id=doc.get("id", ""),
            date_of_service=doc.get("dateOfService", ""),
            provider=doc.get("provider", ""),
            patient_name=doc.get("patientName", ""),
            text=doc.get("fileContent", {}).get("data", ""),
            patient_id=doc.get("patientId", ""),
            is_new_patient=is_new_patient
            # is_new_patient=True
        )
        parsing_time = time.perf_counter() - parsing_start
        
        logger.debug("⏱️ Data Extraction & Parsing", 
                    session_id=session_id,
                    duration_seconds=parsing_time,
                    process="data_extraction_parsing",
                    text_length=len(data.text),
                    document_id=data.document_id)
        
        # Track agent initialization time (cached)
        agent_init_start = time.perf_counter()
        agent = get_optimized_em_enhancement_agent()
        agent_init_time = time.perf_counter() - agent_init_start
        
        logger.debug("⏱️ Agent Initialization", 
                    session_id=session_id,
                    duration_seconds=agent_init_time,
                    process="agent_initialization",
                    agent_type="optimized_enhancement_agent")
        
        # Track prompt preparation time (minimal prompt)
        prompt_start = time.perf_counter()
        patient_type = "new patient" if data.is_new_patient else "established patient"
        code_range = "99202-99205" if data.is_new_patient else "99212-99215"
        
        user_prompt = f"""Document ID: {data.document_id}
Date: {data.date_of_service}
Provider: {data.provider}
Patient Type: {patient_type}

Medical Note:
{data.text}

Analyze and assign appropriate E/M code ({code_range}) with brief MDM-focused justification. Use {code_range} codes for {patient_type} visits."""
        prompt_time = time.perf_counter() - prompt_start
        
        logger.debug("⏱️ Minimal Prompt Preparation", 
                    session_id=session_id,
                    duration_seconds=prompt_time,
                    process="prompt_preparation",
                    prompt_length=len(user_prompt),
                    text_length=len(data.text))
        
        logger.debug(f"🧠 Optimized Enhancement Agent: Sending minimal prompt to AI model...")
        logger.debug(f"📝 Optimized prompt length: {len(user_prompt)} characters")
        
        # Track AI model inference time with timeout (this is usually the slowest part)
        inference_start = time.perf_counter()
        try:
            # Use asyncio timeout for additional safety
            import asyncio
            result = await asyncio.wait_for(
                agent.run(user_prompt), 
                timeout=15.0  # Aggressive AI timeout
            )
        except asyncio.TimeoutError:
            logger.error("❌ AI Model Timeout", session_id=session_id)
            raise TimeoutError("AI model inference timed out after 15 seconds")
            
        inference_time = time.perf_counter() - inference_start
        
        logger.debug("⏱️ AI Model Inference - CRITICAL BOTTLENECK", 
                   session_id=session_id,
                   duration_seconds=inference_time,
                   process="ai_model_inference",
                   prompt_length=len(user_prompt),
                   text_length=len(data.text),
                   document_id=data.document_id)
        
        logger.debug(f"✅ Optimized Enhancement Agent: Received response from AI model")
        logger.debug(f"🎯 Optimized Enhancement Agent: Assigned code {result.output.assigned_code}")
        logger.debug(f"📋 Optimized Enhancement Agent: Justification length: {len(result.output.justification)} characters")
        
        # Track response formatting time (minimal processing)
        formatting_start = time.perf_counter()
        response = OptimizedEMEnhancementOutput(
            document_id=data.document_id,
            text=data.text,
            assigned_code=result.output.assigned_code,
            justification=result.output.justification,
            is_new_patient=data.is_new_patient
        ).model_dump()
        formatting_time = time.perf_counter() - formatting_start
        
        logger.debug("⏱️ Response Formatting", 
                    session_id=session_id,
                    duration_seconds=formatting_time,
                    process="response_formatting",
                    response_size=len(str(response)))
        
        # Calculate and log total execution time and performance summary
        total_time = time.perf_counter() - start_time
        
        # Calculate time breakdown percentages
        mcp_total = mcp_connection_time + api_call_time
        mcp_percentage = (mcp_total / total_time) * 100
        inference_percentage = (inference_time / total_time) * 100
        processing_percentage = ((parsing_time + prompt_time + formatting_time) / total_time) * 100
        
        logger.debug("🏁 Optimized Enhancement Agent: Execution Complete", 
                   session_id=session_id,
                   total_execution_time=total_time,
                   document_id=data.document_id,
                   assigned_code=result.output.assigned_code)
        
        # Add simple performance metrics to response - just execution times
        response["performance_metrics"] = {
            "session_id": session_id,
            "total_execution_time": round(total_time, 2),
            "execution_breakdown": {
                "mcp_server_connection": round(mcp_connection_time, 3),
                "progress_note_api_call": round(api_call_time, 3),
                "json_parsing": round(parsing_time, 3),
                "agent_initialization": round(agent_init_time, 3),
                "prompt_preparation": round(prompt_time, 3),
                "ai_model_inference": round(inference_time, 3),
                "response_formatting": round(formatting_time, 3)
            }
        }
        
        logger.debug(f"🎉 Optimized Enhancement Agent: Successfully completed analysis for {data.document_id}")
        return response
        
    except Exception as e:
        total_time = time.perf_counter() - start_time
        logger.error("❌ Optimized Enhancement Agent: Execution Failed", 
                    session_id=session_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    total_time_before_error=total_time,
                    exc_info=True)
        raise
