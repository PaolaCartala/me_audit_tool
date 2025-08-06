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
        
        logger.debug(f"🕵️ Auditor Agent: Starting audit for {data.document_id}")
        logger.debug(f"📊 Auditor Agent: Enhancement agent assigned code {data.assigned_code}")
        
        # Prepare context for the AI agent
        user_prompt = f"""
        ORIGINAL PROGRESS NOTE:
        Document ID: {data.document_id}
        Text: {data.text}
        
        ENHANCEMENT AGENT RESULTS:
        Assigned E/M Code: {data.assigned_code}
        Justification: {data.justification}
        
        Code Recommendations:
        - 99212: {data.code_recommendations.code_99212}
        - 99213: {data.code_recommendations.code_99213}
        - 99214: {data.code_recommendations.code_99214}
        - 99215: {data.code_recommendations.code_99215}
        
        TASK: Audit coding assignment for compliance and accuracy. Provide final code assignment and any compliance flags.
        """
        
        logger.debug(f"🧠 Auditor Agent: Sending optimized audit request to AI model...")
        logger.debug(f"📝 Auditor Agent: Optimized prompt length: {len(user_prompt)} characters")
        
        # Run the PydanticAI agent
        result = await em_auditor_agent.run(user_prompt)
        
        logger.debug(f"✅ Auditor Agent: Received audit response from AI model")
        logger.debug(f"🎯 Auditor Agent: Final assigned code {result.output.final_assigned_code}")
        logger.debug(f"🚨 Auditor Agent: Found {len(result.output.audit_flags)} audit flags")
        logger.debug(f"💰 Auditor Agent: Billing note length: {len(result.output.billing_ready_note)} characters")
        logger.debug(f"📊 Auditor Agent: Confidence - Score: {result.output.confidence.score}%, Tier: {result.output.confidence.tier}")
        logger.debug(f"🧠 Auditor Agent: Confidence reasoning: {result.output.confidence.reasoning[:150]}...")
        
        # Log score deductions if any
        if result.output.confidence.score_deductions:
            logger.debug(f"⚠️ Auditor Agent: Score deductions:")
            for deduction in result.output.confidence.score_deductions:
                logger.debug(f"  {deduction}")
        
        # Log audit flags if any
        if result.output.audit_flags:
            logger.debug(f"🚩 Auditor Agent: Audit flags detected:")
            for i, flag in enumerate(result.output.audit_flags, 1):
                logger.debug(f"  {i}. {flag}")
        else:
            logger.debug(f"✅ Auditor Agent: No compliance issues found")
        
        # Log code evaluations
        logger.debug(f"📊 Auditor Agent: Code evaluations:")
        logger.debug(f"  • 99212: {result.output.code_evaluations.code_99212_evaluation[:100]}...")
        logger.debug(f"  • 99213: {result.output.code_evaluations.code_99213_evaluation[:100]}...")
        logger.debug(f"  • 99214: {result.output.code_evaluations.code_99214_evaluation[:100]}...")
        logger.debug(f"  • 99215: {result.output.code_evaluations.code_99215_evaluation[:100]}...")
        
        # Return structured response
        response = EMAuditOutput(
            document_id=data.document_id,
            text=data.text,
            audit_flags=result.output.audit_flags,
            final_assigned_code=result.output.final_assigned_code,
            final_justification=result.output.final_justification,
            code_evaluations=result.output.code_evaluations,
            billing_ready_note=result.output.billing_ready_note,
            confidence=result.output.confidence
        ).model_dump()
        
        logger.debug(f"🎉 Auditor Agent: Successfully completed audit for {data.document_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in EM Auditor Agent: {str(e)}")
        raise
