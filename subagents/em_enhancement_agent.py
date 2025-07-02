import os
import logging

import azure.functions as func
from dotenv import load_dotenv

from models.pydantic_models import EMInput, EMEnhancementOutput, em_enhancement_agent
from settings import logger

# Load environment variables
load_dotenv()


async def main(input_payload: dict) -> dict:
    """
    E/M Enhancement Agent - Stage D
    Analyzes medical progress notes and assigns appropriate E/M codes with justifications
    """
    try:
        # Parse input
        data = EMInput(**input_payload)
        
        logger.info(f"🤖 Enhancement Agent: Starting analysis for {data.document_id}")
        logger.info(f"📄 Document text length: {len(data.text)} characters")
        
        # Prepare context for the AI agent
        user_prompt = f"""
        Document ID: {data.document_id}
        Date of Service: {data.date_of_service}
        Provider: {data.provider}
        
        Medical Progress Note:
        {data.text}
        
        ANALYSIS REQUIRED:
        1. Assign the most appropriate E/M code (99212, 99213, 99214, or 99215)
        2. Provide detailed justification for the assigned code
        3. For ALL codes (99212, 99213, 99214, 99215), specify what additional information would be needed to justify each level
        
        Please analyze this medical progress note comprehensively."""
        
        logger.info(f"🧠 Enhancement Agent: Sending prompt to AI model...")
        logger.info(f"📝 Prompt preview: {user_prompt[:200]}...")
        
        # Run the PydanticAI agent
        result = await em_enhancement_agent.run(user_prompt)
        
        logger.info(f"✅ Enhancement Agent: Received response from AI model")
        logger.info(f"🎯 Enhancement Agent: Assigned code {result.data.assigned_code}")
        logger.info(f"📋 Enhancement Agent: Justification length: {len(result.data.justification)} characters")
        
        # Log code recommendations
        logger.info(f"📊 Enhancement Agent: Code recommendations generated:")
        logger.info(f"  • 99212: {result.data.code_recommendations.code_99212[:100]}...")
        logger.info(f"  • 99213: {result.data.code_recommendations.code_99213[:100]}...")
        logger.info(f"  • 99214: {result.data.code_recommendations.code_99214[:100]}...")
        logger.info(f"  • 99215: {result.data.code_recommendations.code_99215[:100]}...")
        
        # Return structured response
        response = EMEnhancementOutput(
            document_id=data.document_id,
            assigned_code=result.data.assigned_code,
            justification=result.data.justification,
            code_recommendations=result.data.code_recommendations
        ).model_dump()
        
        logger.info(f"🎉 Enhancement Agent: Successfully completed analysis for {data.document_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in EM Enhancement Agent: {str(e)}")
        raise
