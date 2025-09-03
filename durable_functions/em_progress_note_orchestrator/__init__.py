import azure.durable_functions as df
from datetime import datetime

from settings import logger


# TODO: [DELETE] Format progress note as markdown before returning
def format_progress_note_as_markdown(progress_note_result: dict) -> str:
    """Format progress note result as a readable markdown similar to original dictation format."""
    if not isinstance(progress_note_result, dict) or "progress_note" not in progress_note_result:
        return ""
    
    progress_note = progress_note_result["progress_note"]
    
    # Build the formatted markdown
    formatted_sections = []
    
    # Patient Info
    patient_info = progress_note.get("patient_info", {})
    formatted_sections.append("## Patient Information")
    formatted_sections.append("")
    formatted_sections.append(f"**Patient Name:** {patient_info.get('patient_name', '')}")
    formatted_sections.append(f"**Date of Birth:** {patient_info.get('date_of_birth', '')}")
    formatted_sections.append(f"**Date of Service:** {patient_info.get('date_of_service', '')}")
    if provider := patient_info.get('provider'):
        formatted_sections.append(f"**Provider:** {provider}")
    formatted_sections.append("")
    
    # History
    if history := progress_note.get("history"):
        formatted_sections.append("## History")
        formatted_sections.append("")
        formatted_sections.append(history)
        formatted_sections.append("")
    
    # Past Medical History
    if pmh := progress_note.get("past_medical_history"):
        formatted_sections.append("## Past Medical History")
        formatted_sections.append("")
        # Convert bullet points to markdown if it's already formatted with -
        if pmh.strip().startswith('-'):
            formatted_sections.append(pmh)
        else:
            formatted_sections.append(pmh)
        formatted_sections.append("")
    
    # Medications
    if medications := progress_note.get("medications"):
        formatted_sections.append("## Medications")
        formatted_sections.append("")
        # Convert bullet points to markdown if it's already formatted with -
        if medications.strip().startswith('-'):
            formatted_sections.append(medications)
        else:
            formatted_sections.append(medications)
        formatted_sections.append("")
    
    # Allergies
    if allergies := progress_note.get("allergies"):
        formatted_sections.append("## Allergies")
        formatted_sections.append("")
        formatted_sections.append(allergies)
        formatted_sections.append("")
    
    # Physical Examination
    if physical_exam := progress_note.get("physical_examination"):
        formatted_sections.append("## Physical Examination")
        formatted_sections.append("")
        if isinstance(physical_exam, dict) and "findings" in physical_exam:
            for finding in physical_exam["findings"]:
                system = finding.get("system", "")
                findings = finding.get("findings", "")
                formatted_sections.append(f"**{system}:** {findings}")
        else:
            formatted_sections.append(str(physical_exam))
        formatted_sections.append("")
    
    # Imaging/Studies
    if imaging := progress_note.get("imaging_studies"):
        formatted_sections.append("## Imaging / Radiographs / Studies Reviewed")
        formatted_sections.append("")
        formatted_sections.append(str(imaging))
        formatted_sections.append("")
    
    # Assessment
    if assessment := progress_note.get("assessment"):
        formatted_sections.append("## Assessment")
        formatted_sections.append("")
        if isinstance(assessment, list):
            for i, item in enumerate(assessment, 1):
                formatted_sections.append(f"{i}. {item}")
        else:
            formatted_sections.append(str(assessment))
        formatted_sections.append("")
    
    # Plan
    if plan := progress_note.get("plan"):
        formatted_sections.append("## Plan")
        formatted_sections.append("")
        if isinstance(plan, list):
            for i, item in enumerate(plan, 1):
                formatted_sections.append(f"{i}. {item}")
        else:
            formatted_sections.append(str(plan))
        formatted_sections.append("")
    
    # Dictation Notes
    if dictation_notes := progress_note.get("dictation_notes"):
        formatted_sections.append("---")
        formatted_sections.append("")
        formatted_sections.append(f"*{dictation_notes}*")
    
    return "\n".join(formatted_sections)


def orchestrator_function(context: df.DurableOrchestrationContext):
    appointment_id = context.get_input()
    
    logger.debug("🎭 Progress Note Orchestrator: Starting", 
                orchestrator_instance_id=context.instance_id,
                appointment_id=str(appointment_id))

    try:
        context.set_custom_status("Starting progress note generation")
        logger.debug("🎭 Progress Note Orchestrator: About to call activity", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    activity_name="progress_note_agent_activity")
        
        progress_note_result = yield context.call_activity("progress_note_agent_activity", appointment_id)
        logger.debug("🎭 Progress Note Orchestrator: Activity completed", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    activity_result_type=type(progress_note_result).__name__)
        
        context.set_custom_status("Progress note generation completed successfully")
        logger.debug("🎭 Progress Note Orchestrator: Completed successfully", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    has_result=bool(progress_note_result))
        
        has_error = isinstance(progress_note_result, dict) and "error" in progress_note_result and "status" in progress_note_result and progress_note_result.get("status") == "failed"
        
        if has_error:
            error_msg = progress_note_result.get("error", "Unknown error")
            context.set_custom_status(f"Agent error: {error_msg}")
            logger.error("🎭 Progress Note Orchestrator: Agent returned error", 
                        orchestrator_instance_id=context.instance_id,
                        appointment_id=str(appointment_id),
                        agent_error=error_msg)
        
        # TODO: [DELETE] Format progress note as markdown before returning
        formatted_progress_note = format_progress_note_as_markdown(progress_note_result) if not has_error else ""
        
        return {
            "processed_documents": 1,
            "successful_documents": 0 if has_error else 1,
            "failed_documents": 1 if has_error else 0,
            "processing_timestamp": datetime.now().isoformat(),
            "orchestrator_instance_id": context.instance_id,
            "appointment_id": str(appointment_id),
            # TODO: [DELETE] Format progress note as markdown before returning
            "results": formatted_progress_note if formatted_progress_note else [progress_note_result],
        }
        
    except Exception as e:
        error_msg = f"Orchestration error: {str(e)}"
        context.set_custom_status(error_msg)
        logger.error("🎭 Progress Note Orchestrator: Unexpected failure", 
                    orchestrator_instance_id=context.instance_id,
                    appointment_id=str(appointment_id),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)
        
        return {
            "processed_documents": 1,
            "successful_documents": 0,
            "failed_documents": 1,
            "processing_timestamp": datetime.now().isoformat(),
            "orchestrator_instance_id": context.instance_id,
            "appointment_id": str(appointment_id),
            "error": error_msg,
            "error_type": type(e).__name__,
            "results": []
        }

main = orchestrator_function
