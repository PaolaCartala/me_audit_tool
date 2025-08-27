import os
import time
import json
from datetime import datetime
from typing import Optional

import azure.functions as func
from dotenv import load_dotenv

from agents.models.optimized_pydantic_models import (
    OptimizedEMInput,
    OptimizedEMAuditOutput,
    get_optimized_em_auditor_agent
)
from settings import logger

# Load environment variables
load_dotenv()


class PatientCodeMapper:
    """Maps between new and established patient E/M codes and validates patient type consistency"""
    
    # Code mappings: established -> new
    CODE_MAPPINGS = {
        "99212": "99202",  # Level 2
        "99213": "99203",  # Level 3
        "99214": "99204",  # Level 4
        "99215": "99205"   # Level 5
    }
    
    # Reverse mapping: new -> established
    REVERSE_MAPPINGS = {v: k for k, v in CODE_MAPPINGS.items()}
    
    ESTABLISHED_CODES = set(CODE_MAPPINGS.keys())
    NEW_PATIENT_CODES = set(CODE_MAPPINGS.values())
    ALL_VALID_CODES = ESTABLISHED_CODES | NEW_PATIENT_CODES
    
    @classmethod
    def get_appropriate_code(cls, current_code: str, is_new_patient: bool) -> str:
        """
        Get the appropriate E/M code based on patient type
        
        Args:
            current_code: Current E/M code (99212-99215 or 99202-99205)
            is_new_patient: True for new patient, False for established
            
        Returns:
            Appropriate E/M code for the patient type
        """
        if current_code not in cls.ALL_VALID_CODES:
            return current_code  # Return as-is if not a valid E/M code
        
        if is_new_patient:
            # Need new patient code (99202-99205)
            if current_code in cls.NEW_PATIENT_CODES:
                return current_code  # Already correct
            elif current_code in cls.ESTABLISHED_CODES:
                return cls.CODE_MAPPINGS[current_code]  # Convert established -> new
        else:
            # Need established patient code (99212-99215)
            if current_code in cls.ESTABLISHED_CODES:
                return current_code  # Already correct
            elif current_code in cls.NEW_PATIENT_CODES:
                return cls.REVERSE_MAPPINGS[current_code]  # Convert new -> established
        
        return current_code
    
    @classmethod
    def validate_code_for_patient_type(cls, code: str, is_new_patient: bool) -> tuple[bool, str]:
        """
        Validate if the code is appropriate for the patient type
        
        Args:
            code: E/M code to validate
            is_new_patient: True for new patient, False for established
            
        Returns:
            Tuple of (is_valid, message)
        """
        if code not in cls.ALL_VALID_CODES:
            return True, "Code is not an E/M office visit code"
        
        if is_new_patient and code in cls.NEW_PATIENT_CODES:
            return True, "Code is appropriate for new patient"
        elif not is_new_patient and code in cls.ESTABLISHED_CODES:
            return True, "Code is appropriate for established patient"
        elif is_new_patient and code in cls.ESTABLISHED_CODES:
            correct_code = cls.CODE_MAPPINGS[code]
            return False, f"Code {code} is for established patients. Use {correct_code} for new patients"
        elif not is_new_patient and code in cls.NEW_PATIENT_CODES:
            correct_code = cls.REVERSE_MAPPINGS[code]
            return False, f"Code {code} is for new patients. Use {correct_code} for established patients"
        
        return True, "Code validation completed"


async def main(enhancement_result: dict) -> dict:
    """
    Optimized E/M Auditor Agent - Stage E
    Takes enhancement result and provides final audit with all required outputs
    Optimized for speed with focused prompts and aggressive timeouts
    """
    # Track overall execution time
    start_time = time.perf_counter()
    document_id = enhancement_result.get("document_id", "unknown")
    session_id = f"opt_auditor_{document_id}"
    
    logger.debug("🚀 Optimized Auditor Agent: Starting execution", 
                session_id=session_id,
                document_id=document_id,
                enhancement_code=enhancement_result.get("assigned_code"))
    
    try:
        # Track agent initialization time (cached)
        agent_init_start = time.perf_counter()
        agent = get_optimized_em_auditor_agent()
        agent_init_time = time.perf_counter() - agent_init_start
        
        logger.debug("⏱️ Agent Initialization", 
                    session_id=session_id,
                    duration_seconds=agent_init_time,
                    process="agent_initialization",
                    agent_type="optimized_auditor_agent")
        
        # Track prompt preparation time (focused prompt with enhancement result)
        prompt_start = time.perf_counter()
        
        # Extract patient type information
        is_new_patient = enhancement_result.get('is_new_patient')
        patient_type_info = ""
        code_validation_info = ""
        
        if is_new_patient is not None:
            patient_type = "new patient" if is_new_patient else "established patient"
            appropriate_codes = "99202-99205" if is_new_patient else "99212-99215"
            patient_type_info = f"\nPatient Type: {patient_type} (use codes {appropriate_codes})"
            
            # Validate current code for patient type
            current_code = enhancement_result.get('assigned_code', '')
            is_valid, validation_message = PatientCodeMapper.validate_code_for_patient_type(current_code, is_new_patient)
            if not is_valid:
                correct_code = PatientCodeMapper.get_appropriate_code(current_code, is_new_patient)
                code_validation_info = f"\nCODE VALIDATION ISSUE: {validation_message}. Suggested correction: {correct_code}"
        
        user_prompt = f"""AUDIT REQUEST
Document ID: {enhancement_result.get('document_id')}
Enhancement Agent Result:
- Assigned Code: {enhancement_result.get('assigned_code')}
- Justification: {enhancement_result.get('justification')}{patient_type_info}{code_validation_info}

Original Medical Note:
{enhancement_result.get('text', '')[:2000]}...

TASK: Review the enhancement agent's code assignment and provide:
1. Audit flags for compliance risks (include patient type validation if applicable)
2. Final code assignment (confirm or adjust, especially for patient type consistency)
3. Structured justification with MDM breakdown
4. Confidence assessment with specific score deductions

Focus on accuracy, compliance, patient type consistency, and actionable feedback."""
        prompt_time = time.perf_counter() - prompt_start
        
        logger.debug("⏱️ Focused Prompt Preparation", 
                    session_id=session_id,
                    duration_seconds=prompt_time,
                    process="prompt_preparation",
                    prompt_length=len(user_prompt),
                    enhancement_code=enhancement_result.get("assigned_code"))
        
        logger.debug(f"🧠 Optimized Auditor Agent: Sending focused prompt to AI model...")
        logger.debug(f"📝 Focused prompt length: {len(user_prompt)} characters")
        logger.debug(f"🔍 Auditing enhancement code: {enhancement_result.get('assigned_code')}")
        
        # Track AI model inference time with timeout (critical bottleneck)
        inference_start = time.perf_counter()
        try:
            # Use asyncio timeout for additional safety
            import asyncio
            result = await asyncio.wait_for(
                agent.run(user_prompt), 
                timeout=18.0  # Slightly higher timeout for auditor due to complexity
            )
        except asyncio.TimeoutError:
            logger.error("❌ AI Model Timeout", session_id=session_id)
            raise TimeoutError("AI model inference timed out after 18 seconds")
            
        inference_time = time.perf_counter() - inference_start
        
        logger.debug("⏱️ AI Model Inference - CRITICAL BOTTLENECK", 
                   session_id=session_id,
                   duration_seconds=inference_time,
                   process="ai_model_inference",
                   prompt_length=len(user_prompt),
                   document_id=document_id,
                   input_code=enhancement_result.get("assigned_code"),
                   final_code=result.output.final_assigned_code)
        
        logger.debug(f"✅ Optimized Auditor Agent: Received response from AI model")
        logger.debug(f"🎯 Optimized Auditor Agent: Final code {result.output.final_assigned_code}")
        logger.debug(f"📊 Optimized Auditor Agent: Confidence score {result.output.confidence.score}")
        logger.debug(f"🚩 Optimized Auditor Agent: Audit flags count: {len(result.output.audit_flags)}")
        
        # Post-process: Validate and correct final code for patient type consistency
        final_code = result.output.final_assigned_code
        audit_flags = list(result.output.audit_flags)
        is_new_patient = enhancement_result.get('is_new_patient')
        
        if is_new_patient is not None:
            is_valid, validation_message = PatientCodeMapper.validate_code_for_patient_type(final_code, is_new_patient)
            if not is_valid:
                corrected_code = PatientCodeMapper.get_appropriate_code(final_code, is_new_patient)
                audit_flags.append(f"Patient type mismatch: {validation_message}. Corrected from {final_code} to {corrected_code}")
                final_code = corrected_code
                logger.debug(f"🔧 Code corrected for patient type: {result.output.final_assigned_code} -> {final_code}")
        
        # Track response formatting time (document metadata added here, not from model)
        formatting_start = time.perf_counter()
        response = OptimizedEMAuditOutput(
            document_id=enhancement_result.get("document_id", ""),
            text=enhancement_result.get("text", ""),
            audit_flags=audit_flags,
            final_assigned_code=final_code,
            final_justification=result.output.final_justification,
            confidence=result.output.confidence,
            is_new_patient=is_new_patient
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
        inference_percentage = (inference_time / total_time) * 100
        processing_percentage = ((prompt_time + formatting_time) / total_time) * 100
        
        logger.debug("🏁 Optimized Auditor Agent: Execution Complete - PERFORMANCE SUMMARY", 
                   session_id=session_id,
                   total_execution_time=total_time,
                   document_id=document_id,
                   code_comparison={
                       "enhancement_code": enhancement_result.get("assigned_code"),
                       "final_audit_code": result.output.final_assigned_code,
                       "code_changed": enhancement_result.get("assigned_code") != result.output.final_assigned_code
                   },
                   performance_breakdown={
                       "ai_model_inference": {
                           "duration": inference_time,
                           "percentage": inference_percentage,
                           "is_bottleneck": inference_percentage > 70
                       },
                       "data_processing": {
                           "duration": prompt_time + formatting_time,
                           "percentage": processing_percentage,
                           "breakdown": {
                               "prompt_prep": prompt_time,
                               "formatting": formatting_time
                           }
                       },
                       "agent_initialization": {
                           "duration": agent_init_time,
                           "percentage": (agent_init_time / total_time) * 100
                       }
                   })
        
        # Add simple performance metrics to response - just execution times
        response["performance_metrics"] = {
            "session_id": session_id,
            "total_execution_time": round(total_time, 2),
            "execution_breakdown": {
                "agent_initialization": round(agent_init_time, 3),
                "prompt_preparation": round(prompt_time, 3),
                "ai_model_inference": round(inference_time, 3),
                "response_formatting": round(formatting_time, 3)
            }
        }
        
        logger.debug(f"🎉 Optimized Auditor Agent: Successfully completed audit for {document_id}")
        return response
        
    except Exception as e:
        total_time = time.perf_counter() - start_time
        logger.error("❌ Optimized Auditor Agent: Execution Failed", 
                    session_id=session_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    total_time_before_error=total_time,
                    document_id=document_id,
                    exc_info=True)
        raise
