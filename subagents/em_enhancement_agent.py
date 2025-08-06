import os
import logging

import azure.functions as func
from dotenv import load_dotenv

from models.pydantic_models import EMInput, EMEnhancementOutput, em_enhancement_agent
from settings import logger
from pydantic_ai.mcp import MCPServerSSE, MCPServerStreamableHTTP, MCPServerStdio
import json

# Load environment variables
load_dotenv()


async def main(input_payload) -> dict:
    """
    E/M Enhancement Agent - Stage D
    Analyzes medical progress notes and assigns appropriate E/M codes with justifications
    """
    try:
        # Parse input
        server = MCPServerSSE(url=os.getenv("MCP_API_URL"), headers={"X-API-Key": os.getenv("MCP_API_KEY")})
        async with server:
            tools = await server.list_tools()
            logger.info(f"🔧 Available tools: {tools}")
            response = await server.call_tool(tool_name="appointment-progressnote", arguments={"documentId": input_payload})
            #response = await server.call_tool(tool_name="appointment-dictation", arguments={"appointmentId": "563543C8-23FF-481B-93DE-1D2C93959DE8"})

        logger.info(f"Received document for analysis: {response['document']}")
        # Parse the response into json
        
        data = EMInput(
            document_id=response['document']['id'],
            date_of_service=response['document']['dateOfService'],
            provider=response['document']['provider'],
            patient_name= response['document']['patientName'],
            text=response['document']['fileContent']['data'],
            patient_id=response['document']['patientId'],
        )
        
        logger.debug(f"🤖 Enhancement Agent: Starting analysis for {data.document_id}")
        logger.debug(f"📄 Document text length: {len(data.text)} characters")
        
        # Prepare context for the AI agent
        user_prompt = f"""
        Document ID: {data.document_id}
        Date of Service: {data.date_of_service}
        Provider: {data.provider}
        
        Medical Progress Note:
        {data.text}
        
        TASK: Assign appropriate E/M code (99212-99215) with justification.
        For each code level, specify what additional documentation would be needed.
        """
        
        logger.debug(f"🧠 Enhancement Agent: Sending optimized prompt to AI model...")
        logger.debug(f"📝 Optimized prompt length: {len(user_prompt)} characters")
        
        # Run the PydanticAI agent
        result = await em_enhancement_agent.run(user_prompt)
        
        logger.debug(f"✅ Enhancement Agent: Received response from AI model")
        logger.debug(f"🎯 Enhancement Agent: Assigned code {result.output.assigned_code}")
        logger.debug(f"📋 Enhancement Agent: Justification length: {len(result.output.justification)} characters")
        
        # Log code recommendations
        logger.debug(f"📊 Enhancement Agent: Code recommendations generated:")
        logger.debug(f"  • 99212: {result.output.code_recommendations.code_99212[:100]}...")
        logger.debug(f"  • 99213: {result.output.code_recommendations.code_99213[:100]}...")
        logger.debug(f"  • 99214: {result.output.code_recommendations.code_99214[:100]}...")
        logger.debug(f"  • 99215: {result.output.code_recommendations.code_99215[:100]}...")
        
        # Return structured response
        response = EMEnhancementOutput(
            document_id=data.document_id,
            text=data.text,
            assigned_code=result.output.assigned_code,
            justification=result.output.justification,
            code_recommendations=result.output.code_recommendations
        ).model_dump()
        
        logger.debug(f"🎉 Enhancement Agent: Successfully completed analysis for {data.document_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in EM Enhancement Agent: {str(e)}")
        raise
