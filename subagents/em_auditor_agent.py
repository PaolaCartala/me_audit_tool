import os
import logging

import azure.functions as func
from dotenv import load_dotenv

from models.pydantic_models import EMEnhancementOutput, EMAuditOutput, em_auditor_agent
from settings import logger

# Load environment variables
load_dotenv()


async def main(input_payload: dict) -> dict:
    """
    E/M Auditor Agent - Stage E
    Reviews enhanced notes for compliance and produces final billing-ready documentation
    """
    try:
        # Parse input from Stage D
        data = EMEnhancementOutput(**input_payload)
        
        logger.info(f"🕵️ Auditor Agent: Starting audit for {data.document_id}")
        logger.info(f"📊 Auditor Agent: Enhancement agent assigned code {data.assigned_code}")
        
        # Prepare context for the AI agent
        user_prompt = f"""
        ORIGINAL PROGRESS NOTE:
        Document ID: {data.document_id}
        
        ENHANCEMENT AGENT RESULTS:
        Assigned E/M Code: {data.assigned_code}
        Justification: {data.justification}
        
        Code Recommendations:
        - 99212: {data.code_recommendations.code_99212}
        - 99213: {data.code_recommendations.code_99213}
        - 99214: {data.code_recommendations.code_99214}
        - 99215: {data.code_recommendations.code_99215}
        
        AUDIT REQUIREMENTS:
        Please audit this E/M coding assignment and recommendations for compliance and accuracy.
        Provide final code assignment, refined recommendations, and any compliance flags.
        """
        
        logger.info(f"🧠 Auditor Agent: Sending audit request to AI model...")
        logger.info(f"📝 Auditor Agent: Prompt preview: {user_prompt[:200]}...")
        
        # Run the PydanticAI agent
        result = await em_auditor_agent.run(user_prompt)
        
        logger.info(f"✅ Auditor Agent: Received audit response from AI model")
        logger.info(f"🎯 Auditor Agent: Final assigned code {result.data.final_assigned_code}")
        logger.info(f"🚨 Auditor Agent: Found {len(result.data.audit_flags)} audit flags")
        logger.info(f"💰 Auditor Agent: Billing note length: {len(result.data.billing_ready_note)} characters")
        
        # Log audit flags if any
        if result.data.audit_flags:
            logger.info(f"🚩 Auditor Agent: Audit flags detected:")
            for i, flag in enumerate(result.data.audit_flags, 1):
                logger.info(f"  {i}. {flag}")
        else:
            logger.info(f"✅ Auditor Agent: No compliance issues found")
        
        # Log final code recommendations
        logger.info(f"📊 Auditor Agent: Final code recommendations:")
        logger.info(f"  • 99212: {result.data.final_code_recommendations.code_99212[:100]}...")
        logger.info(f"  • 99213: {result.data.final_code_recommendations.code_99213[:100]}...")
        logger.info(f"  • 99214: {result.data.final_code_recommendations.code_99214[:100]}...")
        logger.info(f"  • 99215: {result.data.final_code_recommendations.code_99215[:100]}...")
        
        # Return structured response
        response = EMAuditOutput(
            document_id=data.document_id,
            audit_flags=result.data.audit_flags,
            final_assigned_code=result.data.final_assigned_code,
            final_justification=result.data.final_justification,
            final_code_recommendations=result.data.final_code_recommendations,
            billing_ready_note=result.data.billing_ready_note
        ).model_dump()
        
        logger.info(f"🎉 Auditor Agent: Successfully completed audit for {data.document_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in EM Auditor Agent: {str(e)}")
        raise
