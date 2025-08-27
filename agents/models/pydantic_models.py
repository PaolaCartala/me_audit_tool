import os
from typing import List, Optional
from pathlib import Path
from functools import lru_cache

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
    get_em_coding_guidelines, get_specific_code_requirements, get_mdm_complexity_guide
)

# Cache guidelines at module level to avoid repeated calls
# EM_CODING_GUIDELINES = get_em_coding_guidelines()
# SPECIFIC_CODE_REQUIREMENTS_99212 = get_specific_code_requirements('99212')
# SPECIFIC_CODE_REQUIREMENTS_99213 = get_specific_code_requirements('99213')
# get_specific_code_requirements('99214') = get_specific_code_requirements('99214')
# SPECIFIC_CODE_REQUIREMENTS_99215 = get_specific_code_requirements('99215')
# MDM_COMPLEXITY_GUIDE = get_mdm_complexity_guide()


# Input schemas
class EMInput(BaseModel):
    document_id: str
    date_of_service: str
    provider: str
    text: str
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    is_new_patient: Optional[bool] = None

class EMProgressNoteGeneratorInput(BaseModel):
    transcription: str
    patient_name: str
    patient_id: str
    patient_date_of_birth: str
    date_of_service: str
    provider: str
    progress_note_type: str = "Progress Note"
    created_by: Optional[str] = None
    creation_date: Optional[str] = None
    is_new_patient: Optional[bool] = None


# Response schemas for PydanticAI agents
class EMCodeRecommendations(BaseModel):
    """Recommendations for each E/M code level"""
    code_99212: str = Field(description="List of bulleted recommendations for additional information needed to justify 99212 (established) or 99202 (new patient). Each item should start with '- '")
    code_99213: str = Field(description="List of bulleted recommendations for additional information needed to justify 99213 (established) or 99203 (new patient). Each item should start with '- '") 
    code_99214: str = Field(description="List of bulleted recommendations for additional information needed to justify 99214 (established) or 99204 (new patient). Each item should start with '- '")
    code_99215: str = Field(description="List of bulleted recommendations for additional information needed to justify 99215 (established) or 99205 (new patient). Each item should start with '- '")


class ProviderFriendlyEvaluation(BaseModel):
    """Provider-friendly evaluation structure"""
    mdmAssignmentReason: List[str] = Field(description="List of clear, concise points supporting the assigned MDM level including positive factors like orders, data review, risk level, exam detail")
    documentationEnhancementOpportunities: List[str] = Field(description="List of specific gaps or missing details that could raise confidence or change level, focusing on actionable steps")
    scoring_impact: str = Field(description="Point deductions with specific issues formatted as bullet points")
    quick_tip: Optional[str] = Field(description="Optional short, friendly tip to help provider improve future documentation", default=None)


class EMCodeEvaluations(BaseModel):
    """Provider-friendly audit evaluations for each E/M code recommendations"""
    code_99212_evaluation: ProviderFriendlyEvaluation = Field(description="Provider-friendly evaluation of 99212 recommendations")
    code_99213_evaluation: ProviderFriendlyEvaluation = Field(description="Provider-friendly evaluation of 99213 recommendations")
    code_99214_evaluation: ProviderFriendlyEvaluation = Field(description="Provider-friendly evaluation of 99214 recommendations")
    code_99215_evaluation: ProviderFriendlyEvaluation = Field(description="Provider-friendly evaluation of 99215 recommendations")


class CodeJustification(BaseModel):
    """Structured justification for E/M code assignment"""
    supportedBy: str = Field(description="Required. Primary support statement, typically 'Supported by straightforward MDM per AMA 2025 E/M guidelines.'")
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
    final_justification: CodeJustification = Field(description="Structured final justification after audit")
    code_evaluations: EMCodeEvaluations = Field(description="Evaluation of the recommendations for all E/M codes")
    billing_ready_note: str = Field(description="Final version of the provider note ready for billing submission")
    confidence: ConfidenceAssessment = Field(description="Comprehensive confidence assessment with score, tier, and detailed reasoning")


class EMEnhancementOutput(BaseModel):
    document_id: str
    text: str
    assigned_code: str
    justification: str
    code_recommendations: EMCodeRecommendations
    billing_ready_note: str
    confidence: ConfidenceAssessment
    is_new_patient: Optional[bool] = None


class EMAuditOutput(BaseModel):
    document_id: str
    text: str
    audit_flags: List[str]
    final_assigned_code: str
    final_justification: str
    code_evaluations: EMCodeEvaluations
    billing_ready_note: str
    confidence: ConfidenceAssessment
    is_new_patient: Optional[bool] = None

class EMProgressNoteGeneratorOutput(BaseModel):
    """Output schema for generated medical progress note"""
    progress_note: str = Field(description="Generated medical progress note based on transcription and patient information")

# Azure OpenAI Model Configuration
@lru_cache(maxsize=None)
def get_azure_openai_model(model="gpt-5") -> OpenAIModel:
    """Get configured Azure OpenAI model instance with validation"""
    
    # Get required environment variables
    if model not in ["gpt-5-mini", "gpt-5-nano"]:
        endpoint = "https://ptm-me2x3s2u-swedencentral.cognitiveservices.azure.com/"
    else:
        endpoint = "https://audit-tool-agent.cognitiveservices.azure.com/"
    api_version = '2024-12-01-preview'
    
    # Validate required environment variables
    if not api_key:
        raise ValueError("AZURE_OPENAI_KEY environment variable is required")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
    # if not deployment_name:
    #     raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required")
    if not api_version:
        raise ValueError("AZURE_OPENAI_API_VERSION environment variable is required")
    
    # Configure for Azure OpenAI using the official PydanticAI syntax
    return OpenAIModel(model,
        provider=AzureProvider(
            azure_endpoint=endpoint, api_version=api_version, api_key=api_key,
        ))


# Global variables for lazy loading
_em_enhancement_agent = None
_em_auditor_agent = None
_em_progress_note_generator_agent = None

# PydanticAI Agents with Lazy Loading for better performance
@lru_cache(maxsize=None)
def get_em_enhancement_agent() -> Agent:
    """Get or create the EM enhancement agent (lazy loading)"""
    global _em_enhancement_agent
    if _em_enhancement_agent is None:
        logger.debug("Creating EM enhancement agent instance")
        _em_enhancement_agent = Agent(
            model=get_azure_openai_model(), result_type=EMCodeAssignment, output_retries=1,
            system_prompt=f"""You are a senior medical coding specialist with expertise in E/M (Evaluation and Management) coding per AMA 2025 guidelines.

Your task is to analyze medical progress notes and:
1. Assign the most appropriate E/M code based on patient type:
   - NEW PATIENTS: Use codes 99202, 99203, 99204, or 99205
   - ESTABLISHED PATIENTS: Use codes 99212, 99213, 99214, or 99215
2. Provide detailed justification for the assigned code
3. For ALL FOUR applicable codes based on patient type, explain what additional information would be needed to justify each level

CODE MAPPINGS BY COMPLEXITY:
- Straightforward MDM: 99202 (new) ↔ 99212 (established)
- Low MDM: 99203 (new) ↔ 99213 (established)  
- Moderate MDM: 99204 (new) ↔ 99214 (established)
- High MDM: 99205 (new) ↔ 99215 (established)

EMBEDDED GUIDELINES:

=== E/M CODING GUIDELINES ===
{get_em_coding_guidelines()}

=== SPECIFIC CODE REQUIREMENTS ===

99212/99202 Requirements:
{get_specific_code_requirements('99212')}

99213/99203 Requirements:
{get_specific_code_requirements('99213')}

99214/99204 Requirements:
{get_specific_code_requirements('99214')}

99215/99205 Requirements:
{get_specific_code_requirements('99215')}

=== MDM COMPLEXITY GUIDE ===
{get_mdm_complexity_guide()}

METHODOLOGY:
1. Identify patient type from the provided information (new vs. established)
2. Analyze the provided medical note against the embedded AMA 2025 guidelines above
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
        logger.debug("EM enhancement agent created successfully")
    return _em_enhancement_agent

@lru_cache(maxsize=None)
def get_em_auditor_agent() -> Agent:
    """Get or create the EM auditor agent (lazy loading)"""
    global _em_auditor_agent
    if _em_auditor_agent is None:
        logger.debug("Creating EM auditor agent instance")
        _em_auditor_agent = Agent(
            model=get_azure_openai_model(), result_type=EMAuditResult, output_retries=1,
            system_prompt=f"""You are a medical coding auditor specializing in compliance and quality assurance for E/M coding per AMA 2025 guidelines.

Your role is to review the enhancement agent's recommendations and the original progress note to provide final audit results.

CRITICAL: Validate that assigned codes match patient type:
- NEW PATIENTS: Only codes 99202-99205 are valid
- ESTABLISHED PATIENTS: Only codes 99212-99215 are valid
- CODE MAPPINGS: 99202↔99212, 99203↔99213, 99204↔99214, 99205↔99215

EMBEDDED GUIDELINES:

=== E/M CODING GUIDELINES ===
{get_em_coding_guidelines()}

=== SPECIFIC CODE REQUIREMENTS ===

99212/99202 Requirements:
{get_specific_code_requirements('99212')}

99213/99203 Requirements:
{get_specific_code_requirements('99213')}

99214/99204 Requirements:
{get_specific_code_requirements('99214')}

99215/99205 Requirements:
{get_specific_code_requirements('99215')}

=== MDM COMPLEXITY GUIDE ===
{get_mdm_complexity_guide()}

AUDIT METHODOLOGY:
1. Use the embedded AMA 2025 guidelines above to verify compliance with current standards
2. VALIDATE CODE MATCHES PATIENT TYPE - Flag mismatches as critical compliance issues
3. Cross-reference assigned codes with the embedded specific code requirements for accuracy
4. Validate MDM complexity assessment using the embedded MDM complexity guide
5. Identify any compliance risks or documentation gaps

AUDIT RESPONSIBILITIES:
1. Review the assigned E/M code and justification for accuracy against embedded AMA guidelines
2. ENSURE CODE APPROPRIATENESS FOR PATIENT TYPE (new vs. established)
3. Evaluate the quality and correctness of recommendations for all applicable code levels
4. Identify compliance risks, upcoding concerns, or missing documentation
5. Provide final code assignment and evaluation of enhancement recommendations
6. Create a billing-ready version of the provider note

AUDIT FOCUS AREAS:
1. PATIENT TYPE VALIDATION - Critical compliance requirement
2. Code justification alignment with actual documentation and AMA criteria
3. Missing clinical elements that could affect code assignment
4. Compliance risks, red flags, or potential audit triggers
5. Documentation completeness for billing submission and payer requirements
6. Quality and accuracy of enhancement agent's recommendations for each code level

COMPLIANCE REQUIREMENTS (per AMA 2025):
- PATIENT TYPE MUST MATCH CODE RANGE (99202-99205 for new, 99212-99215 for established)
- Medical necessity clearly documented and justified
- All code components adequately supported by documentation
- No upcoding without proper clinical justification
- Clear Medical Decision Making rationale
- Appropriate time documentation if using time-based coding
- Established patient criteria verified

RESPONSE FORMAT:
- audit_flags: List any compliance issues, risks, or documentation gaps found
- final_assigned_code: Final E/M code after thorough audit review
- final_justification: Structured justification object with the following format:
  {{
    "supportedBy": "Supported by [MDM level] MDM per AMA 2025 E/M guidelines.",
    "documentationSummary": ["Key documentation point 1", "Key documentation point 2", "etc."],
    "mdmConsiderations": ["MDM consideration 1", "MDM consideration 2", "etc."],
    "complianceAlerts": ["Alert 1", "Alert 2", "etc."] // Optional, omit if no alerts
  }}
- code_evaluations: Provider-friendly evaluation using the new format below
- billing_ready_note: Enhanced note ready for submission with proper documentation
- confidence: Comprehensive confidence assessment object

PROVIDER-FRIENDLY EVALUATION FORMAT:
For code_evaluations, use this provider-friendly structure for each code:

**mdmAssignmentReason:**
List clear, concise points supporting the assigned MDM level. Include positive factors such as:
- Orders placed or diagnostic tests reviewed
- Data analysis performed
- Risk level assessment
- Physical exam details documented
- Treatment decisions made

**documentationEnhancementOpportunities:**
List specific gaps or missing details that could raise confidence or change level:
- Focus on actionable steps — what to add, clarify, or integrate
- Specific documentation improvements needed
- Areas where more detail would strengthen the case

**scoring_impact:**
Point deductions formatted as:
"- -X points: Specific issue — be direct and concise
- -X points: Another issue with impact on score"

**quick_tip:** (optional)
"Short, friendly tip to help the provider improve future documentation"

EXAMPLE:
{{
  "mdmAssignmentReason": [
    "Single established patient with straightforward chronic condition management",
    "No new diagnostic tests ordered or complex data analysis required",
    "Minimal risk assessment with stable patient condition",
    "Standard follow-up care with no medication changes"
  ],
  "documentationEnhancementOpportunities": [
    "Include more detail in physical examination findings",
    "Add functional assessment of patient's condition",
    "Document any patient education or counseling provided"
  ],
  "scoring_impact": "- -5 points: History/physical exam lacks specificity\n- -2 points: PMH contains unrelated issues not addressed",
  "quick_tip": "Even if a problem is unrelated, stating 'not addressed at this visit' removes ambiguity for coders and auditors."
}}

EXAMPLE STRUCTURED JUSTIFICATION:
{{
  "supportedBy": "Supported by straightforward MDM per AMA 2025 E/M guidelines.",
  "documentationSummary": [
    "One self-limited/minor problem",
    "Minimal/no reviewed or analyzed data",
    "Minimal risk",
    "Well-appearing established patient",
    "No current orthopedic or new complaints",
    "Resolved diabetes (not managed here)",
    "Normal exam and imaging",
    "Standard healthy plan, no medications/interventions"
  ],
  "mdmConsiderations": [
    "No prescription medication, data analysis, or significant management decisions present",
    "No time recorded; MDM is sole driver for code selection"
  ],
  "complianceAlerts": [
    "Higher codes would be considered upcoding based on documented MDM and risk level."
  ]
}}

STRUCTURED JUSTIFICATION REQUIREMENTS:
1. supportedBy: Always start with "Supported by [straightforward/low/moderate/high] MDM per AMA 2025 E/M guidelines."
2. documentationSummary: List key clinical findings, problems addressed, and documentation strengths
3. mdmConsiderations: List MDM-specific factors like data review, risk level, prescription management
4. complianceAlerts: Only include if there are actual compliance concerns or upcoding risks (can be null/empty)
- confidence: Comprehensive confidence assessment object containing:
  * score: Numerical score from 0 to 100 indicating confidence in final code assignment
  * tier: Confidence tier label based on score (Very High, High, Moderate, Low, Very Low)
  * mdmAssignmentReason: List of specific reasons supporting the MDM level assignment
  * documentationEnhancementOpportunities: List of specific opportunities to enhance documentation quality
  * score_deductions: Specific score reduction reasons, formatted as "- Score reduced by X points: [reason]"
  * quick_tip: Optional short, friendly tip to help provider improve future documentation

CONFIDENCE ASSESSMENT REQUIREMENTS:
1. SCORE (0-100): Base confidence level
2. TIER: Automatically assign based on score ranges:
   - 90-100: "Very High" - Clear, unambiguous documentation fully supports the assigned code
   - 70-89: "High" - Good documentation supports the code with minor gaps
   - 50-69: "Moderate" - Reasonable support but some uncertainties or missing elements
   - 30-49: "Low" - Limited support, significant gaps, or borderline between codes
   - 0-29: "Very Low" - Poor documentation, major gaps, or conflicting evidence

3. SCORE_DEDUCTIONS: If score < 100, list specific reasons:
   - "- Score reduced by X points: [specific reason]"
   - "- Score reduced by Y points: [another reason]"
   Example: "- Score reduced by 3 points: Lack of explicit personal imaging interpretation language"

4. MDM_ASSIGNMENT_REASON: List specific clinical factors supporting the MDM level:
   - Example: "Clear documentation of moderate complexity medical decision making"
   - Example: "Appropriate risk assessment for prescription drug management"

5. DOCUMENTATION_ENHANCEMENT_OPPORTUNITIES: List actionable improvements:
   - Example: "Enhanced physical exam documentation would strengthen support"
   - Example: "More detailed risk assessment discussion would improve confidence"

4. QUICK_TIP: Optional short, friendly tip to help provider improve future documentation

CONFIDENCE SCORE GUIDELINES:
- 90-100: Very high confidence - Clear, unambiguous documentation fully supports the assigned code with robust clinical evidence
- 70-89: High confidence - Good documentation supports the code with minor gaps or ambiguities
- 50-69: Moderate confidence - Reasonable support for the code but some uncertainties or missing elements
- 30-49: Low confidence - Limited support, significant gaps, or borderline between codes
- 0-29: Very low confidence - Poor documentation, major gaps, or conflicting evidence

Always reference the embedded AMA 2025 guidelines in your audit findings. Flag any compliance risks and provide a final, polished assessment that meets current coding standards."""
        )
        logger.debug("EM auditor agent created successfully")
    return _em_auditor_agent

@lru_cache(maxsize=None)
def get_em_progress_note_generator_agent() -> Agent:
    """Get or create the EM progress note generator agent (lazy loading)"""
    global _em_progress_note_generator_agent
    if _em_progress_note_generator_agent is None:
        logger.debug("Creating EM progress note generator agent instance")
        _em_progress_note_generator_agent = Agent(
            model=get_azure_openai_model(),
            result_type=EMProgressNoteGeneratorOutput,
            output_retries=4,  # Increased from default 1 to handle validation retries
            system_prompt=f"""You are a medical scribe specializing in generating high-quality, compliant medical progress notes based on physician transcriptions and structured patient information.

Your task is to create a progress note using the following structure:

PATIENT NAME: {{patient_name}}
DATE OF BIRTH: {{patient_date_of_birth}}
DATE OF SERVICE: {{date_of_service}}

HISTORY:
Construct a comprehensive history based on the transcription. Begin with the patient's age and gender, summarize the reason for the visit, duration of symptoms, aggravating or relieving factors, prior treatments, and relevant context.

PAST MEDICAL HISTORY:
Include any chronic conditions, prior surgeries, or relevant medical background if provided in the transcription.

MEDICATIONS:
List current medications if mentioned, otherwise omit or note “None”.

ALLERGIES:
List allergies if present, otherwise “No known drug allergies”.

PHYSICAL EXAMINATION:
Summarize objective findings across systems: HEENT, cardiovascular, respiratory, musculoskeletal, neurological, etc., as appropriate based on the transcription.

IMAGING / RADIOGRAPHS / STUDIES REVIEWED:
Include a concise summary of imaging or study results, including MRIs, x-rays, EMG, CT, etc., and interpret their significance.

ASSESSMENT:
Provide numbered diagnostic impressions or medical assessments based on the history and physical exam.

PLAN:
Outline next steps including medications prescribed, imaging ordered, referrals, lifestyle advice, follow-up visits, etc.

At the end, include:
“This dictation was prepared using Dragon Medical voice recognition software. As a result, errors may occur. When identified, these errors have been corrected. While every attempt is made to correct errors during dictation, errors may still exist.”

Be concise but thorough. Use clinical terminology and professional tone. Do not fabricate information that is not mentioned in the transcription. Extract and organize all relevant clinical information from the transcription into the appropriate sections.
""")
        logger.debug("EM progress note generator agent created successfully")
    return _em_progress_note_generator_agent
