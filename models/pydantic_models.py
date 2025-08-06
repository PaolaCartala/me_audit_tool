import os
from typing import List, Optional
from pathlib import Path

# import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider
from dotenv import load_dotenv

from settings import logger

# Load environment variables from .env file
load_dotenv()

# logfire.configure()
# logfire.instrument_pydantic_ai()

# Load guidelines directly into memory for better performance (no tools)
from utils.guidelines_cache import (
    get_em_coding_guidelines,
    get_specific_code_requirements,
    get_mdm_complexity_guide
)

# Cache guidelines at module level to avoid repeated calls
EM_CODING_GUIDELINES = get_em_coding_guidelines()
SPECIFIC_CODE_REQUIREMENTS_99212 = get_specific_code_requirements('99212')
SPECIFIC_CODE_REQUIREMENTS_99213 = get_specific_code_requirements('99213')
SPECIFIC_CODE_REQUIREMENTS_99214 = get_specific_code_requirements('99214')
SPECIFIC_CODE_REQUIREMENTS_99215 = get_specific_code_requirements('99215')
MDM_COMPLEXITY_GUIDE = get_mdm_complexity_guide()


# Input schemas
class EMInput(BaseModel):
    document_id: str
    date_of_service: str
    provider: str
    text: str
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None

class EMProgressNoteGeneratorInput(BaseModel):
    transcription: str
    patient_name: str
    patient_id: str
    patient_date_of_birth: str
    progress_note_type: str
    patient_data: str


# Response schemas for PydanticAI agents
class EMCodeRecommendations(BaseModel):
    """Recommendations for each E/M code level"""
    code_99212: str = Field(description="List of bulleted recommendations for additional information needed to justify 99212. Each item should start with '- '")
    code_99213: str = Field(description="List of bulleted recommendations for additional information needed to justify 99213. Each item should start with '- '") 
    code_99214: str = Field(description="List of bulleted recommendations for additional information needed to justify 99214. Each item should start with '- '")
    code_99215: str = Field(description="List of bulleted recommendations for additional information needed to justify 99215. Each item should start with '- '")


class EMCodeEvaluations(BaseModel):
    """Audit evaluations for each E/M code recommendations"""
    code_99212_evaluation: str = Field(description="Evaluation of whether the 99212 recommendations are correct, complete, and appropriate")
    code_99213_evaluation: str = Field(description="Evaluation of whether the 99213 recommendations are correct, complete, and appropriate")
    code_99214_evaluation: str = Field(description="Evaluation of whether the 99214 recommendations are correct, complete, and appropriate")
    code_99215_evaluation: str = Field(description="Evaluation of whether the 99215 recommendations are correct, complete, and appropriate")


class ConfidenceAssessment(BaseModel):
    """Confidence assessment with score, tier, and detailed reasoning"""
    score: int = Field(description="Confidence score from 0 to 100", ge=0, le=100)
    tier: str = Field(description="Confidence tier based on score (Very High, High, Moderate, Low, Very Low)")
    reasoning: str = Field(description="Detailed bulleted explanation of confidence factors")
    score_deductions: List[str] = Field(description="Specific reasons why the score is not 100, each starting with '- '", default_factory=list)


class EMCodeAssignment(BaseModel):
    """Response schema for E/M code assignment with recommendations for all levels"""
    document_text: str = Field(description="The full text of the medical progress note being analyzed")
    assigned_code: str = Field(description="The most appropriate E/M code assigned (99212, 99213, 99214, or 99215)")
    justification: str = Field(description="Detailed clinical justification for the assigned code")
    code_recommendations: EMCodeRecommendations = Field(description="Recommendations for all E/M code levels")


class EMAuditResult(BaseModel):
    """Response schema for E/M audit result"""
    audit_flags: List[str] = Field(description="List of compliance risks or missing statements")
    final_assigned_code: str = Field(description="Final E/M code after audit review")
    final_justification: str = Field(description="Final justification after audit")
    code_evaluations: EMCodeEvaluations = Field(description="Evaluation of the recommendations for all E/M codes")
    billing_ready_note: str = Field(description="Final version of the provider note ready for billing submission")
    confidence: ConfidenceAssessment = Field(description="Comprehensive confidence assessment with score, tier, and detailed reasoning")


class EMEnhancementOutput(BaseModel):
    document_id: str
    text: str
    assigned_code: str
    justification: str
    code_recommendations: EMCodeRecommendations


class EMAuditOutput(BaseModel):
    document_id: str
    text: str
    audit_flags: List[str]
    final_assigned_code: str
    final_justification: str
    code_evaluations: EMCodeEvaluations
    billing_ready_note: str
    confidence: ConfidenceAssessment

class EMProgressNoteGeneratorOutput(BaseModel):
    """Output schema for generated medical progress note"""
    progress_note: str = Field(description="Generated medical progress note based on transcription and patient information")

# Azure OpenAI Model Configuration
def get_azure_openai_model() -> OpenAIModel:
    """Get configured Azure OpenAI model instance with validation"""
    
    # Get required environment variables
    api_key = ""
    # os.getenv("AZURE_OPENAI_KEY")
    endpoint = "https://audit-tool-agent.cognitiveservices.azure.com/"
    # os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    
    # Validate required environment variables
    if not api_key:
        raise ValueError("AZURE_OPENAI_KEY environment variable is required")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
    if not deployment_name:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required")
    if not api_version:
        raise ValueError("AZURE_OPENAI_API_VERSION environment variable is required")
    
    # Configure for Azure OpenAI using the official PydanticAI syntax
    return OpenAIModel(
        deployment_name,
        provider=AzureProvider(
            azure_endpoint=endpoint,
            api_version=api_version,
            api_key=api_key,
        ),
    )


# PydanticAI Agents with Embedded Guidelines (No Tools for better performance)
em_enhancement_agent = Agent(
    model=get_azure_openai_model(),
    result_type=EMCodeAssignment,
    system_prompt=f"""You are a senior medical coding specialist with expertise in E/M (Evaluation and Management) coding per AMA 2025 guidelines.

Your task is to analyze medical progress notes and:
1. Assign the most appropriate E/M code (99212, 99213, 99214, or 99215)
2. Provide detailed justification for the assigned code
3. For ALL FOUR codes (99212, 99213, 99214, 99215), explain what additional information would be needed to justify each level

EMBEDDED GUIDELINES:

=== E/M CODING GUIDELINES ===
{EM_CODING_GUIDELINES}

=== SPECIFIC CODE REQUIREMENTS ===

99212 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99212}

99213 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99213}

99214 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99214}

99215 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99215}

=== MDM COMPLEXITY GUIDE ===
{MDM_COMPLEXITY_GUIDE}

METHODOLOGY:
1. Analyze the provided medical note against the embedded AMA 2025 guidelines above
2. Assess Medical Decision Making complexity using the embedded MDM guide
3. Evaluate total time and medical necessity based on embedded requirements
4. Reference the specific code requirements for each level (99212-99215)

KEY ANALYSIS AREAS:
1. Medical Decision Making (MDM): Problems addressed, data reviewed/analyzed, risk level
2. Total Time: Face-to-face and non-face-to-face time on date of encounter
3. History and Examination: Medically appropriate level (extent doesn't determine code level)

RESPONSE FORMAT:
- assigned_code: The best code for current documentation based on AMA guidelines
- justification: Detailed clinical justification referencing specific AMA criteria from embedded guidelines
- code_recommendations: For each code level (99212-99215), provide bulleted lists starting with "- "

IMPORTANT: Each recommendation item MUST start with "- " (hyphen symbol followed by space) to create proper bulleted lists.

Always reference the embedded AMA guidelines when making coding decisions. Focus on identifying gaps and opportunities for appropriate coding enhancement based on clinical complexity and official standards."""
)

em_auditor_agent = Agent(
    model=get_azure_openai_model(),
    result_type=EMAuditResult,
    system_prompt=f"""You are a medical coding auditor specializing in compliance and quality assurance for E/M coding per AMA 2025 guidelines.

Your role is to review the enhancement agent's recommendations and the original progress note to provide final audit results.

EMBEDDED GUIDELINES:

=== E/M CODING GUIDELINES ===
{EM_CODING_GUIDELINES}

=== SPECIFIC CODE REQUIREMENTS ===

99212 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99212}

99213 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99213}

99214 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99214}

99215 Requirements:
{SPECIFIC_CODE_REQUIREMENTS_99215}

=== MDM COMPLEXITY GUIDE ===
{MDM_COMPLEXITY_GUIDE}

AUDIT METHODOLOGY:
1. Use the embedded AMA 2025 guidelines above to verify compliance with current standards
2. Cross-reference assigned codes with the embedded specific code requirements for accuracy
3. Validate MDM complexity assessment using the embedded MDM complexity guide
4. Identify any compliance risks or documentation gaps

AUDIT RESPONSIBILITIES:
1. Review the assigned E/M code and justification for accuracy against embedded AMA guidelines
2. Evaluate the quality and correctness of recommendations for all code levels (99212-99215)
3. Identify compliance risks, upcoding concerns, or missing documentation
4. Provide final code assignment and evaluation of enhancement recommendations
5. Create a billing-ready version of the provider note

AUDIT FOCUS AREAS:
1. Code justification alignment with actual documentation and AMA criteria
2. Missing clinical elements that could affect code assignment
3. Compliance risks, red flags, or potential audit triggers
4. Documentation completeness for billing submission and payer requirements
5. Quality and accuracy of enhancement agent's recommendations for each code level

COMPLIANCE REQUIREMENTS (per AMA 2025):
- Medical necessity clearly documented and justified
- All code components adequately supported by documentation
- No upcoding without proper clinical justification
- Clear Medical Decision Making rationale
- Appropriate time documentation if using time-based coding
- Established patient criteria verified

RESPONSE FORMAT:
- audit_flags: List any compliance issues, risks, or documentation gaps found
- final_assigned_code: Final E/M code after thorough audit review
- final_justification: Updated justification referencing specific AMA criteria from embedded guidelines
- code_evaluations: Evaluation of the enhancement agent's recommendations for each E/M code (99212-99215), assessing their correctness, completeness, and appropriateness
- billing_ready_note: Enhanced note ready for submission with proper documentation
- confidence: Comprehensive confidence assessment object containing:
  * score: Numerical score from 0 to 100 indicating confidence in final code assignment
  * tier: Confidence tier label based on score (Very High, High, Moderate, Low, Very Low)
  * reasoning: Bulleted explanation with factors that INCREASE and DECREASE confidence, each bullet starting with "- "
  * score_deductions: Specific reasons why score is not 100, each starting with "- " (empty list if score is 100)

CONFIDENCE ASSESSMENT REQUIREMENTS:
1. SCORE (0-100): Base confidence level
2. TIER: Automatically assign based on score ranges:
   - 90-100: "Very High" - Clear, unambiguous documentation fully supports the assigned code
   - 70-89: "High" - Good documentation supports the code with minor gaps
   - 50-69: "Moderate" - Reasonable support but some uncertainties or missing elements
   - 30-49: "Low" - Limited support, significant gaps, or borderline between codes
   - 0-29: "Very Low" - Poor documentation, major gaps, or conflicting evidence

3. REASONING: Structure as bulleted lists:
   - "FACTORS INCREASING CONFIDENCE:"
   - "- [specific factor 1]"
   - "- [specific factor 2]"
   - "FACTORS DECREASING CONFIDENCE:"
   - "- [specific factor 1]"
   - "- [specific factor 2]"

4. SCORE_DEDUCTIONS: If score < 100, list specific reasons:
   - "- Score reduced by X points: [specific reason]"
   - "- Score reduced by Y points: [another reason]"
   Example: "- Score reduced by 2 points: External data review not explicitly documented"

CONFIDENCE SCORE GUIDELINES:
- 90-100: Very high confidence - Clear, unambiguous documentation fully supports the assigned code with robust clinical evidence
- 70-89: High confidence - Good documentation supports the code with minor gaps or ambiguities
- 50-69: Moderate confidence - Reasonable support for the code but some uncertainties or missing elements
- 30-49: Low confidence - Limited support, significant gaps, or borderline between codes
- 0-29: Very low confidence - Poor documentation, major gaps, or conflicting evidence

Always reference the embedded AMA 2025 guidelines in your audit findings. Flag any compliance risks and provide a final, polished assessment that meets current coding standards."""
)


em_progress_note_generator_agent = Agent(
    model=get_azure_openai_model(),
    result_type=EMProgressNoteGeneratorOutput,
    system_prompt=f"""You are a medical scribe specializing in generating high-quality, compliant medical progress notes based on physician transcriptions and structured patient information.

Your task is to create a progress note using the following structure:

PATIENT NAME: {{patient_name}}
DATE OF BIRTH: {{patient_date_of_birth}}
DATE OF SERVICE: {{date_of_service}}

HISTORY:
Construct a comprehensive history based on the transcription. Begin with the patient's age and gender, summarize the reason for the visit, duration of symptoms, aggravating or relieving factors, prior treatments, and relevant context.

PAST MEDICAL HISTORY:
Include any chronic conditions, prior surgeries, or relevant medical background if provided in the patient_data or transcription.

MEDICATIONS:
List current medications if mentioned, otherwise omit or note “None”.

ALLERGIES:
List allergies if present, otherwise “No known drug allergies”.

PHYSICAL EXAMINATION:
Summarize objective findings across systems: HEENT, cardiovascular, respiratory, musculoskeletal, neurological, etc., as appropriate based on the transcription.

IMAGING / RADIOGRAPHS / STUDIES REVIEWED:
Include a concise summary of imaging or study results, including MRIs, x-rays, EMG, CT, etc., and interpret their significance.

IMPRESSIONS:
Provide numbered diagnostic impressions or medical assessments based on the history and physical exam.

PLAN:
Outline next steps including medications prescribed, imaging ordered, referrals, lifestyle advice, follow-up visits, etc.

At the end, include:
“This dictation was prepared using Dragon Medical voice recognition software. As a result, errors may occur. When identified, these errors have been corrected. While every attempt is made to correct errors during dictation, errors may still exist.”

Be concise but thorough. Use clinical terminology and professional tone. Do not fabricate information that is not mentioned in the transcription or patient data.
"""
)