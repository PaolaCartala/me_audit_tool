import os
from typing import List, Optional
from functools import lru_cache

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv

from settings import logger
from agents.models.azure_openai_model import get_optimized_azure_openai_model

load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()


class OptimizedEMProgressNoteInput(BaseModel):
    """Input schema for optimized progress note generation"""
    transcription: str
    patient_name: str
    patient_id: str
    patient_date_of_birth: str
    date_of_service: str
    provider: str
    progress_note_type: str = "Progress Note"
    created_by: Optional[str] = None
    creation_date: Optional[str] = None


class PatientInfo(BaseModel):
    """Patient information section"""
    patient_name: str
    date_of_birth: str
    date_of_service: str
    patient_id: str
    provider: str


class PhysicalExaminationFindings(BaseModel):
    """Individual physical examination finding"""
    system: str = Field(description="Body system or area examined (e.g., 'General', 'Cardiovascular', 'Respiratory', 'Neurological')")
    findings: str = Field(description="Clinical findings for this system")


class PhysicalExamination(BaseModel):
    """Physical examination findings organized by findings list"""
    findings: List[PhysicalExaminationFindings] = Field(description="List of physical examination findings by system", default_factory=list)


class ImagingStudy(BaseModel):
    """Individual imaging study result"""
    type: str = Field(description="Type of study (e.g., 'Chest X-ray', 'MRI lumbar spine')")
    findings: str = Field(description="Key findings from the study")


class StructuredProgressNote(BaseModel):
    """Structured progress note with organized sections"""
    patient_info: PatientInfo
    history: str
    past_medical_history: Optional[str] = None
    medications: Optional[str] = None
    allergies: Optional[str] = None
    physical_examination: Optional[PhysicalExamination] = None
    imaging_studies: Optional[List[ImagingStudy]] = None
    assessment: List[str]
    plan: List[str]
    dictation_notes: Optional[str] = None


class OptimizedEMProgressNoteOutput(BaseModel):
    """Output schema for optimized progress note generation"""
    structured_note: StructuredProgressNote = Field(description="Structured progress note with organized sections")





_optimized_progress_note_agent = None

@lru_cache(maxsize=None)
def get_optimized_progress_note_agent() -> Agent:
    """Get or create the optimized progress note generator agent"""
    global _optimized_progress_note_agent
    if _optimized_progress_note_agent is None:
        logger.debug("Creating optimized progress note agent instance")
        
        progress_note_prompt = """Medical progress note specialist. Generate structured medical progress notes from transcriptions.

TASK: Generate a STRUCTURED medical progress note that organizes clinical information into clear, accessible sections.

OUTPUT REQUIREMENTS:
Return a structured progress note with the following components:
- patient_info: Patient demographics and visit information
- history: Comprehensive history based on transcription
- past_medical_history: Chronic conditions, prior surgeries (if mentioned)
- medications: Current medications (if mentioned)  
- allergies: Known allergies (if mentioned)
- physical_examination: List of examination findings by body system
- imaging_studies: List of imaging studies with findings (if mentioned)
- assessment: List of diagnostic impressions
- plan: List of treatment plan items
- dictation_notes: Voice recognition disclaimer (if applicable)

PHYSICAL EXAMINATION FORMAT:
Structure physical examination as a list of findings by system:
- findings: [
    {"system": "General", "findings": "Alert and oriented, no acute distress"},
    {"system": "Cardiovascular", "findings": "Regular rate and rhythm, no murmurs"},
    {"system": "Respiratory", "findings": "Clear to auscultation bilaterally"}
  ]

GUIDELINES:
- Extract only information mentioned in the transcription
- Use empty list for physical examination if no findings mentioned
- Create separate items for each assessment and plan point
- Include dictation disclaimer if voice recognition software was used
- Be concise but thorough with clinical terminology
- Ensure medical accuracy and proper clinical language
- Follow standard medical documentation practices

Generate structured output based on the provided patient information and transcription."""
        
        _optimized_progress_note_agent = Agent(
            model=get_optimized_azure_openai_model(),
            result_type=StructuredProgressNote, 
            output_retries=1, 
            system_prompt=progress_note_prompt
        )
        logger.debug("Optimized progress note agent created successfully")
    return _optimized_progress_note_agent
