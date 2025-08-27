import os
import logging
import time
from datetime import datetime
from typing import Dict, Optional

import azure.functions as func
from dotenv import load_dotenv

from agents.models.pydantic_models import EMEnhancementOutput, EMAuditOutput, get_em_auditor_agent
from settings import logger

# Load environment variables
load_dotenv()


class PatientCodeMapper:
    """Maps between new patient and established patient E/M codes."""
    
    # Mapping: established_code -> new_patient_code
    ESTABLISHED_TO_NEW_MAPPING: Dict[str, str] = {
        "99212": "99202",
        "99213": "99203", 
        "99214": "99204",
        "99215": "99205"
    }
    
    # Reverse mapping: new_patient_code -> established_code
    NEW_TO_ESTABLISHED_MAPPING: Dict[str, str] = {
        "99202": "99212",
        "99203": "99213",
        "99204": "99214", 
        "99205": "99215"
    }
    
    @classmethod
    def get_appropriate_code(cls, base_code: str, is_new_patient: Optional[bool]) -> str:
        """
        Get the appropriate E/M code based on patient type.
        
        Args:
            base_code: The base code (established patient code like 99212-99215)
            is_new_patient: Boolean indicating if this is a new patient visit
            
        Returns:
            Appropriate E/M code for the patient type
        """
        if is_new_patient is None:
            logger.debug(
                "Patient type not specified, defaulting to established patient codes",
                base_code=base_code
            )
            return base_code
            
        if is_new_patient:
            # Convert to new patient code
            new_code = cls.ESTABLISHED_TO_NEW_MAPPING.get(base_code, base_code)
            logger.debug(
                "Converting to new patient code",
                established_code=base_code,
                new_patient_code=new_code
            )
            return new_code
        else:
            # Return established patient code as-is
            logger.debug(
                "Using established patient code",
                code=base_code
            )
            return base_code
    
    @classmethod
    def validate_code_for_patient_type(cls, code: str, is_new_patient: bool) -> bool:
        """
        Validate if the given code is appropriate for the patient type.
        
        Args:
            code: E/M code to validate
            is_new_patient: Patient type
            
        Returns:
            True if code matches patient type, False otherwise
        """
        if is_new_patient:
            # Code should be 99202-99205
            valid = code in cls.NEW_TO_ESTABLISHED_MAPPING
        else:
            # Code should be 99212-99215
            valid = code in cls.ESTABLISHED_TO_NEW_MAPPING
            
        if not valid:
            logger.error(
                "Code validation failed - mismatch between code and patient type",
                code=code,
                is_new_patient=is_new_patient
            )
            
        return valid


async def main(input_payload: dict) -> dict:
    """
    E/M Auditor Agent - Stage E
    Reviews enhanced notes for compliance and produces final billing-ready documentation
    """
    # Track overall execution time
    start_time = time.perf_counter()
    session_id = f"auditor_{input_payload.get('document_id', 'unknown')}"
    
    logger.debug("🚀 Auditor Agent: Starting execution", 
                session_id=session_id,
                document_id=input_payload.get('document_id', 'unknown')[:50])
    
    try:
        # Track input parsing time
        parsing_start = time.perf_counter()
        data = EMEnhancementOutput(**input_payload)
        parsing_time = time.perf_counter() - parsing_start
        
        logger.debug("⏱️ Input Parsing", 
                    session_id=session_id,
                    duration_seconds=parsing_time,
                    process="input_parsing",
                    document_id=data.document_id)
        
        logger.debug(f"🕵️ Auditor Agent: Starting audit for {data.document_id}")
        logger.debug(f"📊 Auditor Agent: Enhancement agent assigned code {data.assigned_code}")
        logger.debug(f"👤 Patient type: {'New' if data.is_new_patient else 'Established' if data.is_new_patient is False else 'Unknown'}")
        
        # Determine patient type context for prompt
        patient_type_context = ""
        if data.is_new_patient is not None:
            if data.is_new_patient:
                patient_type_context = f"\nPATIENT TYPE: NEW PATIENT (Valid codes: 99202-99205)"
            else:
                patient_type_context = f"\nPATIENT TYPE: ESTABLISHED PATIENT (Valid codes: 99212-99215)"
        else:
            patient_type_context = f"\nPATIENT TYPE: UNKNOWN - Default to established patient codes (99212-99215)"
        
        # Track prompt preparation time
        prompt_start = time.perf_counter()
        user_prompt = f"""
        ORIGINAL PROGRESS NOTE:
        Document ID: {data.document_id}
        Text: {data.text}{patient_type_context}
        
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
        prompt_time = time.perf_counter() - prompt_start
        
        logger.debug("⏱️ Prompt Preparation", 
                    session_id=session_id,
                    duration_seconds=prompt_time,
                    process="prompt_preparation",
                    prompt_length=len(user_prompt),
                    original_text_length=len(data.text))
        
        # Track agent initialization time
        agent_init_start = time.perf_counter()
        agent = get_em_auditor_agent()
        agent_init_time = time.perf_counter() - agent_init_start
        
        logger.debug("⏱️ Agent Initialization", 
                    session_id=session_id,
                    duration_seconds=agent_init_time,
                    process="agent_initialization",
                    agent_type="auditor_agent")
        
        logger.debug(f"🧠 Auditor Agent: Sending optimized audit request to AI model...")
        logger.debug(f"📝 Auditor Agent: Optimized prompt length: {len(user_prompt)} characters")
        
        # Track AI model inference time (critical bottleneck)
        inference_start = time.perf_counter()
        result = await agent.run(user_prompt)
        inference_time = time.perf_counter() - inference_start
        
        logger.debug("⏱️ AI Model Inference - CRITICAL BOTTLENECK", 
                   session_id=session_id,
                   duration_seconds=inference_time,
                   process="ai_model_inference",
                   prompt_length=len(user_prompt),
                   original_text_length=len(data.text),
                   document_id=data.document_id)
        
        logger.debug(f"✅ Auditor Agent: Received audit response from AI model")
        logger.debug(f"🎯 Auditor Agent: Initial assigned code {result.output.final_assigned_code}")
        
        # Validate and adjust final code based on patient type
        original_code = result.output.final_assigned_code
        
        # Check if we need to validate/adjust the code based on patient type
        if data.is_new_patient is not None:
            # Validate if the assigned code matches the patient type
            is_code_valid = PatientCodeMapper.validate_code_for_patient_type(
                original_code, data.is_new_patient
            )
            
            if not is_code_valid:
                # Code doesn't match patient type - we need to map it
                if data.is_new_patient:
                    # Patient is new, but code is established - convert to new patient code
                    if original_code in PatientCodeMapper.ESTABLISHED_TO_NEW_MAPPING:
                        corrected_code = PatientCodeMapper.ESTABLISHED_TO_NEW_MAPPING[original_code]
                        logger.info(
                            "Correcting code for new patient",
                            original_code=original_code,
                            corrected_code=corrected_code,
                            session_id=session_id
                        )
                        result.output.final_assigned_code = corrected_code
                        # Add audit flag about this correction
                        result.output.audit_flags.append(
                            f"Code corrected from {original_code} to {corrected_code} for new patient visit"
                        )
                else:
                    # Patient is established, but code is new patient - convert to established code
                    if original_code in PatientCodeMapper.NEW_TO_ESTABLISHED_MAPPING:
                        corrected_code = PatientCodeMapper.NEW_TO_ESTABLISHED_MAPPING[original_code]
                        logger.info(
                            "Correcting code for established patient",
                            original_code=original_code,
                            corrected_code=corrected_code,
                            session_id=session_id
                        )
                        result.output.final_assigned_code = corrected_code
                        # Add audit flag about this correction
                        result.output.audit_flags.append(
                            f"Code corrected from {original_code} to {corrected_code} for established patient visit"
                        )
        
        logger.debug(f"🎯 Auditor Agent: Final assigned code {result.output.final_assigned_code}")
        logger.debug(f"🚨 Auditor Agent: Found {len(result.output.audit_flags)} audit flags")
        logger.debug(f"💰 Auditor Agent: Billing note length: {len(result.output.billing_ready_note)} characters")
        logger.debug(f"📊 Auditor Agent: Confidence - Score: {result.output.confidence.score}%, Tier: {result.output.confidence.tier}")
        logger.debug(f"💡 Auditor Agent: Quick tip provided: {'Yes' if result.output.confidence.quick_tip else 'No'}")
        
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
        logger.debug(f"  • 99212: {len(result.output.code_evaluations.code_99212_evaluation.mdmAssignmentReason)} MDM reasons, {len(result.output.code_evaluations.code_99212_evaluation.documentationEnhancementOpportunities)} opportunities")
        logger.debug(f"  • 99213: {len(result.output.code_evaluations.code_99213_evaluation.mdmAssignmentReason)} MDM reasons, {len(result.output.code_evaluations.code_99213_evaluation.documentationEnhancementOpportunities)} opportunities")
        logger.debug(f"  • 99214: {len(result.output.code_evaluations.code_99214_evaluation.mdmAssignmentReason)} MDM reasons, {len(result.output.code_evaluations.code_99214_evaluation.documentationEnhancementOpportunities)} opportunities")
        logger.debug(f"  • 99215: {len(result.output.code_evaluations.code_99215_evaluation.mdmAssignmentReason)} MDM reasons, {len(result.output.code_evaluations.code_99215_evaluation.documentationEnhancementOpportunities)} opportunities")
        
        # Track response formatting time
        formatting_start = time.perf_counter()
        response = EMAuditOutput(
            document_id=data.document_id,
            text=data.text,
            audit_flags=result.output.audit_flags,
            final_assigned_code=result.output.final_assigned_code,
            final_justification=result.output.final_justification,
            code_evaluations=result.output.code_evaluations,
            billing_ready_note=result.output.billing_ready_note,
            confidence=result.output.confidence,
            is_new_patient=data.is_new_patient
        ).model_dump()
        formatting_time = time.perf_counter() - formatting_start
        
        logger.debug("⏱️ Response Formatting", 
                    session_id=session_id,
                    duration_seconds=formatting_time,
                    process="response_formatting",
                    billing_note_length=len(result.output.billing_ready_note))
        
        # Calculate and log total execution time and performance summary
        total_time = time.perf_counter() - start_time
        
        # Calculate time breakdown percentages
        inference_percentage = (inference_time / total_time) * 100
        processing_percentage = ((parsing_time + prompt_time + formatting_time) / total_time) * 100
        agent_init_percentage = (agent_init_time / total_time) * 100
        
        logger.debug("� Auditor Agent: Execution Complete - PERFORMANCE SUMMARY", 
                   session_id=session_id,
                   total_execution_time=total_time,
                   document_id=data.document_id,
                   performance_breakdown={
                       "ai_model_inference": {
                           "duration": inference_time,
                           "percentage": inference_percentage,
                           "is_bottleneck": inference_percentage > 70
                       },
                       "data_processing": {
                           "duration": parsing_time + prompt_time + formatting_time,
                           "percentage": processing_percentage,
                           "breakdown": {
                               "input_parsing": parsing_time,
                               "prompt_prep": prompt_time,
                               "formatting": formatting_time
                           }
                       },
                       "agent_initialization": {
                           "duration": agent_init_time,
                           "percentage": agent_init_percentage
                       }
                   },
                   audit_results={
                       "final_code": result.output.final_assigned_code,
                       "confidence_score": result.output.confidence.score,
                       "audit_flags_count": len(result.output.audit_flags),
                       "has_compliance_issues": len(result.output.audit_flags) > 0
                   })
        
        # Add performance metrics to response
        response["performance_metrics"] = {
            "session_id": session_id,
            "total_execution_time": round(total_time, 2),
            "breakdown": {
                "ai_inference_time": round(inference_time, 2),
                "ai_inference_percentage": f"{round(inference_percentage, 2)}%",
                "data_processing_time": round(parsing_time + prompt_time + formatting_time, 2),
                "data_processing_percentage": f"{round(processing_percentage, 2)}%",
                "agent_init_time": round(agent_init_time, 2),
                "agent_init_percentage": f"{round(agent_init_percentage, 2)}%"
            },
            "bottleneck_analysis": {
                "primary_bottleneck": "ai_model_inference" if inference_percentage > 50 else "data_processing",
                # "optimization_recommendations": [
                #     "Consider prompt optimization for audit tasks" if inference_percentage > 70 else None,
                #     "Consider caching agent initialization" if agent_init_percentage > 10 else None,
                #     "Consider pre-processing enhancement data" if processing_percentage > 20 else None
                # ]
            },
            # "measured_at": datetime.now().isoformat()
        }
        
        logger.debug(f"�🎉 Auditor Agent: Successfully completed audit for {data.document_id}")
        return response
        
    except Exception as e:
        total_time = time.perf_counter() - start_time
        logger.error("❌ Auditor Agent: Execution Failed", 
                    session_id=session_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    total_time_before_error=total_time,
                    exc_info=True)
        raise
