import os
from typing import List, Optional
from pathlib import Path
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

try:
    from utils.guidelines_cache import (
        get_em_coding_guidelines, 
        get_specific_code_requirements, 
        get_mdm_complexity_guide
    )
    
    _EM_CODING_GUIDELINES = get_em_coding_guidelines()
    _SPECIFIC_CODE_REQUIREMENTS_99212 = get_specific_code_requirements('99212')
    _SPECIFIC_CODE_REQUIREMENTS_99213 = get_specific_code_requirements('99213')
    _SPECIFIC_CODE_REQUIREMENTS_99214 = get_specific_code_requirements('99214')
    _SPECIFIC_CODE_REQUIREMENTS_99215 = get_specific_code_requirements('99215')
    _MDM_COMPLEXITY_GUIDE = get_mdm_complexity_guide()
    
    logger.debug("Full guidelines loaded and cached successfully for optimized agents")
    
except ImportError as e:
    logger.warning(f"Guidelines cache not available: {e}")
    _EM_CODING_GUIDELINES = None
    _SPECIFIC_CODE_REQUIREMENTS_99212 = None
    _SPECIFIC_CODE_REQUIREMENTS_99213 = None
    _SPECIFIC_CODE_REQUIREMENTS_99214 = None
    _SPECIFIC_CODE_REQUIREMENTS_99215 = None
    _MDM_COMPLEXITY_GUIDE = None


class OptimizedEMInput(BaseModel):
    document_id: str
    date_of_service: str
    provider: str
    text: str
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    is_new_patient: Optional[bool] = None


class OptimizedEMCodeAssignment(BaseModel):
    """Minimal response for enhancement agent - only assigned_code and justification"""
    assigned_code: str = Field(description="The most appropriate E/M code assigned (99212, 99213, 99214, or 99215)")
    justification: str = Field(description="Brief clinical justification for the assigned code based on MDM criteria")


class CodeJustification(BaseModel):
    """Structured justification for E/M code assignment"""
    supportedBy: str = Field(description="Required. Primary support statement, typically 'Supported by [level] MDM per AMA 2025 E/M guidelines.'")
    documentationSummary: List[str] = Field(description="Required. List of key documentation points supporting the code")
    mdmConsiderations: List[str] = Field(description="Required. List of Medical Decision Making considerations")
    complianceAlerts: Optional[List[str]] = Field(description="Optional. List of compliance alerts or warnings", default=None)


class ConfidenceAssessment(BaseModel):
    """Confidence assessment with score, tier, and detailed reasoning"""
    score: int = Field(description="Confidence score from 0 to 100", ge=0, le=100)
    tier: str = Field(description="Confidence tier based on score (Very High, High, Moderate, Low, Very Low)")
    mdmAssignmentReason: List[str] = Field(description="List of specific reasons supporting the MDM level assignment", default_factory=list)
    documentationEnhancementOpportunities: List[str] = Field(description="List of specific opportunities to enhance documentation quality", default_factory=list)
    score_deductions: List[str] = Field(description="Specific reasons for score reductions, each starting with '- Score reduced by X points:' format", default_factory=list)
    quick_tip: Optional[str] = Field(description="Optional short, friendly tip to help the provider improve future documentation", default=None)


class OptimizedEMAuditResult(BaseModel):
    """Optimized response schema for E/M audit result - focused output only"""
    audit_flags: List[str] = Field(description="List of compliance risks or missing statements")
    final_assigned_code: str = Field(description="Final E/M code after audit review")
    final_justification: CodeJustification = Field(description="Structured final justification after audit")
    confidence: ConfidenceAssessment = Field(description="Comprehensive confidence assessment with score, tier, and detailed reasoning")


class OptimizedEMEnhancementOutput(BaseModel):
    document_id: str
    text: str
    assigned_code: str
    justification: str
    is_new_patient: Optional[bool] = None


class OptimizedEMAuditOutput(BaseModel):
    document_id: str
    text: str
    audit_flags: List[str]
    final_assigned_code: str
    final_justification: CodeJustification
    confidence: ConfidenceAssessment
    is_new_patient: Optional[bool] = None





_optimized_em_enhancement_agent = None
_optimized_em_auditor_agent = None

@lru_cache(maxsize=None)
def get_optimized_em_enhancement_agent() -> Agent:
    """Get or create the optimized EM enhancement agent with guidelines-enhanced prompt"""
    global _optimized_em_enhancement_agent
    if _optimized_em_enhancement_agent is None:
        logger.debug("Creating optimized EM enhancement agent instance")
        
        enhanced_prompt = f"""E/M coding specialist. Analyze medical note and assign appropriate code (99212-99215).

EMBEDDED GUIDELINES:

=== E/M CODING GUIDELINES ===
{_EM_CODING_GUIDELINES}

=== SPECIFIC CODE REQUIREMENTS ===

99212 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99212}

99213 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99213}

99214 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99214}

99215 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99215}

=== MDM COMPLEXITY GUIDE ===
{_MDM_COMPLEXITY_GUIDE}

METHODOLOGY:
1. Analyze the provided medical note against the embedded AMA 2025 guidelines above
2. Assess Medical Decision Making complexity using the embedded MDM guide
3. Reference the specific code requirements for each level (99212-99215)

KEY ANALYSIS AREAS:
1. Medical Decision Making (MDM): Problems addressed, data reviewed/analyzed, risk level
2. History and Examination: Medically appropriate level
3. Medical necessity and clinical complexity

RESPONSE: Return assigned_code and clinical justification based on embedded AMA guidelines."""
        
        _optimized_em_enhancement_agent = Agent(
            model=get_optimized_azure_openai_model(), 
            # model=get_optimized_azure_openai_model(model="gpt-5-mini"), 
            result_type=OptimizedEMCodeAssignment, output_retries=1, system_prompt=enhanced_prompt
        )
        logger.debug("Optimized EM enhancement agent created successfully")
    return _optimized_em_enhancement_agent


@lru_cache(maxsize=None)
def get_optimized_em_auditor_agent() -> Agent:
    """Get or create the optimized EM auditor agent with guidelines-enhanced prompt"""
    global _optimized_em_auditor_agent
    if _optimized_em_auditor_agent is None:
        logger.debug("Creating optimized EM auditor agent instance")
        
        enhanced_audit_prompt = f"""Medical coding auditor. Review enhancement agent's code assignment and provide final audit results.

EMBEDDED GUIDELINES:

=== E/M CODING GUIDELINES ===
{_EM_CODING_GUIDELINES}

=== SPECIFIC CODE REQUIREMENTS ===

99212 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99212}

99213 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99213}

99214 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99214}

99215 Requirements:
{_SPECIFIC_CODE_REQUIREMENTS_99215}

=== MDM COMPLEXITY GUIDE ===
{_MDM_COMPLEXITY_GUIDE}

AUDIT METHODOLOGY:
1. Use the embedded AMA 2025 guidelines above to verify compliance with current standards
2. Cross-reference assigned codes with the embedded specific code requirements for accuracy
3. Validate MDM complexity assessment using the embedded MDM complexity guide
4. Identify any compliance risks or documentation gaps

AUDIT FOCUS AREAS:
1. MDM VERIFICATION: Does assigned code match documented complexity?
2. COMPLIANCE RISKS: Missing elements, upcoding/downcoding risks
3. DOCUMENTATION GAPS: What's missing to support or upgrade code?
4. CONFIDENCE ASSESSMENT: Specific deductions and improvement tips

CRITICAL COMPLIANCE CHECKS:
- Problem complexity matches MDM level claimed
- Data review is independent and documented
- Risk level matches prescriptions/procedures/decisions made
- Medical necessity clearly documented

CONFIDENCE SCORING GUIDE:
- 95-100: Bulletproof documentation, no gaps
- 85-94: Strong support, minor enhancement opportunities  
- 70-84: Good support, some missing elements
- 50-69: Moderate support, significant gaps
- <50: Weak support, major documentation issues

RESPONSE FORMAT:
- audit_flags: Specific compliance concerns
- final_assigned_code: Confirmed or adjusted code
- final_justification: Structured MDM breakdown per embedded guidelines
- confidence: Score with specific deductions and tips

Always reference the embedded AMA 2025 guidelines in your audit findings."""
        
        _optimized_em_auditor_agent = Agent(
            model=get_optimized_azure_openai_model(), 
            result_type=OptimizedEMAuditResult, output_retries=1, system_prompt=enhanced_audit_prompt
        )
        logger.debug("Optimized EM auditor agent created successfully")
    return _optimized_em_auditor_agent



