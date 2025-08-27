import os
import logging
import json
import time
from datetime import datetime

import azure.functions as func
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerSSE, MCPServerStreamableHTTP, MCPServerStdio

from agents.models.pydantic_models import EMInput, EMEnhancementOutput, get_em_enhancement_agent
from settings import logger

# Load environment variables
load_dotenv()


async def main(input_payload) -> dict:
    """
    E/M Enhancement Agent - Stage D
    Analyzes medical progress notes and assigns appropriate E/M codes with justifications
    """
    # Track overall execution time
    start_time = time.perf_counter()
    session_id = f"enhancement_{input_payload}"
    
    logger.debug("🚀 Enhancement Agent: Starting execution", 
                session_id=session_id,
                document_id=str(input_payload)[:50])
    
    try:
        # Track MCP server connection time
        mcp_start = time.perf_counter()
        server = MCPServerSSE(url=os.getenv("MCP_API_URL"), headers={"X-API-Key": os.getenv("MCP_API_KEY")})
        mcp_connection_time = time.perf_counter() - mcp_start
        
        logger.debug("⏱️ MCP Server Connection", 
                    session_id=session_id,
                    duration_seconds=mcp_connection_time,
                    process="mcp_server_connection")
        
        async with server:
            # Track tools listing time
            # tools_start = time.perf_counter()
            # tools = await server.list_tools()
            # tools_time = time.perf_counter() - tools_start
            
            # logger.debug("⏱️ MCP List Tools", 
            #             session_id=session_id,
            #             duration_seconds=tools_time,
            #             process="mcp_list_tools",
            #             tools_count=len(tools))
            
            # logger.debug(f"🔧 Available tools: {tools}")
            
            # Track progress note retrieval time
            api_call_start = time.perf_counter()
            response = await server.call_tool(tool_name="appointment-progressnote", arguments={"documentId": input_payload})
            api_call_time = time.perf_counter() - api_call_start
            
            logger.debug("⏱️ MCP Progress Note Call", 
                       session_id=session_id,
                       duration_seconds=api_call_time,
                       process="mcp_progress_note_call",
                       document_id=str(input_payload)[:50])

        logger.debug(f"Received document for analysis: {response['document']}")
        
        # Track data extraction and parsing time
        parsing_start = time.perf_counter()
        doc = response.get("document", {})
        document_id = doc.get("id", "")
        date_of_service = doc.get("dateOfService", "")
        provider = doc.get("provider", "")
        patient_name = doc.get("patientName", "")
        text = doc.get("fileContent", {}).get("data", "")
        patient_id = doc.get("patientId", "")
        is_new_patient = response.get("isNewPatient")

        # Parse the response into json
        data = EMInput(
            document_id=document_id, date_of_service=date_of_service, provider=provider,
            patient_name=patient_name, text=text, patient_id=patient_id,
            is_new_patient=is_new_patient
        )
        parsing_time = time.perf_counter() - parsing_start
        
        logger.debug("⏱️ Data Extraction & Parsing", 
                    session_id=session_id,
                    duration_seconds=parsing_time,
                    process="data_extraction_parsing",
                    text_length=len(data.text),
                    document_id=data.document_id)
        
        logger.debug(f"🤖 Enhancement Agent: Starting analysis for {data.document_id}")
        logger.debug(f"📄 Document text length: {len(data.text)} characters")
        logger.debug(f"👤 Patient type: {'New' if data.is_new_patient else 'Established' if data.is_new_patient is False else 'Unknown'}")
        
        # Determine patient type description for prompt
        patient_type_context = ""
        if data.is_new_patient is not None:
            if data.is_new_patient:
                patient_type_context = "\nPATIENT TYPE: NEW PATIENT (Use codes 99202-99205)"
            else:
                patient_type_context = "\nPATIENT TYPE: ESTABLISHED PATIENT (Use codes 99212-99215)"
        else:
            patient_type_context = "\nPATIENT TYPE: UNKNOWN - Default to established patient codes (99212-99215)"
        
        # Track prompt preparation time
        prompt_start = time.perf_counter()
        user_prompt = f"""
        Document ID: {data.document_id}
        Date of Service: {data.date_of_service}
        Provider: {data.provider}{patient_type_context}
        
        Medical Progress Note:
        {data.text}
        
        TASK: Assign appropriate E/M code based on patient type and medical complexity.
        {"For NEW PATIENTS, assign codes 99202-99205 based on complexity." if data.is_new_patient else "For ESTABLISHED PATIENTS, assign codes 99212-99215 based on complexity." if data.is_new_patient is False else "Patient type unknown - default to established patient codes 99212-99215."}
        For each code level, specify what additional documentation would be needed.
        """
        prompt_time = time.perf_counter() - prompt_start
        
        logger.debug("⏱️ Prompt Preparation", 
                    session_id=session_id,
                    duration_seconds=prompt_time,
                    process="prompt_preparation",
                    prompt_length=len(user_prompt),
                    text_length=len(data.text))
        
        # Track agent initialization time
        agent_init_start = time.perf_counter()
        agent = get_em_enhancement_agent()
        agent_init_time = time.perf_counter() - agent_init_start
        
        logger.debug("⏱️ Agent Initialization", 
                    session_id=session_id,
                    duration_seconds=agent_init_time,
                    process="agent_initialization",
                    agent_type="enhancement_agent")
        
        logger.debug(f"🧠 Enhancement Agent: Sending optimized prompt to AI model...")
        logger.debug(f"📝 Optimized prompt length: {len(user_prompt)} characters")
        
        # Track AI model inference time (this is usually the slowest part)
        inference_start = time.perf_counter()
        result = await agent.run(user_prompt)
        inference_time = time.perf_counter() - inference_start
        
        logger.debug("⏱️ AI Model Inference - CRITICAL BOTTLENECK", 
                   session_id=session_id,
                   duration_seconds=inference_time,
                   process="ai_model_inference",
                   prompt_length=len(user_prompt),
                   text_length=len(data.text),
                   document_id=data.document_id)
        
        logger.debug(f"✅ Enhancement Agent: Received response from AI model")
        logger.debug(f"🎯 Enhancement Agent: Assigned code {result.output.assigned_code}")
        logger.debug(f"📋 Enhancement Agent: Justification length: {len(result.output.justification)} characters")
        
        # Log code recommendations
        logger.debug(f"📊 Enhancement Agent: Code recommendations generated:")
        logger.debug(f"  • 99212: {result.output.code_recommendations.code_99212[:100]}...")
        logger.debug(f"  • 99213: {result.output.code_recommendations.code_99213[:100]}...")
        logger.debug(f"  • 99214: {result.output.code_recommendations.code_99214[:100]}...")
        logger.debug(f"  • 99215: {result.output.code_recommendations.code_99215[:100]}...")
        
        # Track response formatting time
        formatting_start = time.perf_counter()
        response = EMEnhancementOutput(
            document_id=data.document_id,
            text=data.text,
            assigned_code=result.output.assigned_code,
            justification=result.output.justification,
            code_recommendations=result.output.code_recommendations,
            billing_ready_note=result.output.billing_ready_note,
            confidence=result.output.confidence,
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
        
        logger.debug("🏁 Enhancement Agent: Execution Complete - PERFORMANCE SUMMARY", 
                   session_id=session_id,
                   total_execution_time=total_time,
                   document_id=data.document_id,
                   performance_breakdown={
                       "ai_model_inference": {
                           "duration": inference_time,
                           "percentage": inference_percentage,
                           "is_bottleneck": inference_percentage > 70
                       },
                       "mcp_operations": {
                           "duration": mcp_total,
                           "percentage": mcp_percentage,
                           "breakdown": {
                               "connection": mcp_connection_time,
                            #    "list_tools": tools_time,
                               "progress_note_call": api_call_time
                           }
                       },
                       "data_processing": {
                           "duration": parsing_time + prompt_time + formatting_time,
                           "percentage": processing_percentage,
                           "breakdown": {
                               "parsing": parsing_time,
                               "prompt_prep": prompt_time,
                               "formatting": formatting_time
                           }
                       },
                       "agent_initialization": {
                           "duration": agent_init_time,
                           "percentage": (agent_init_time / total_time) * 100
                       }
                   })
        
        # Add performance metrics to response for analysis
        response["performance_metrics"] = {
            "session_id": session_id,
            "total_execution_time": round(total_time, 2),
            "breakdown": {
                "ai_inference_time": round(inference_time, 2),
                "ai_inference_percentage": f"{round(inference_percentage, 2)}%",
                "mcp_operations_time": round(mcp_total, 2),
                "mcp_operations_percentage": f"{round(mcp_percentage, 2)}%",
                "data_processing_time": round(parsing_time + prompt_time + formatting_time, 2),
                "agent_init_time": round(agent_init_time, 2)
            },
            "bottleneck_analysis": {
                "primary_bottleneck": "ai_model_inference" if inference_percentage > 50 else "mcp_operations",
                # "optimization_recommendations": [
                #     "Consider prompt optimization to reduce inference time" if inference_percentage > 70 else None,
                #     "Consider MCP connection pooling" if mcp_percentage > 30 else None,
                #     "Consider caching agent initialization" if (agent_init_time / total_time) * 100 > 10 else None
                # ]
            },
            "measured_at": datetime.now().isoformat()
        }
        
        logger.debug(f"🎉 Enhancement Agent: Successfully completed analysis for {data.document_id}")
        return response
        
    except Exception as e:
        total_time = time.perf_counter() - start_time
        logger.error("❌ Enhancement Agent: Execution Failed", 
                    session_id=session_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    total_time_before_error=total_time,
                    exc_info=True)
        raise
