import os
from typing import List, Optional
from pathlib import Path

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider
from dotenv import load_dotenv

from settings import logger

# Load environment variables from .env file
load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

# Guidelines Tools for PydanticAI Agents
def get_em_coding_guidelines() -> str:
    """
    Get comprehensive E/M coding guidelines from AMA 2025 standards.
    
    This tool provides detailed guidelines for Evaluation and Management (E/M) coding
    including specific criteria for codes 99212-99215, Medical Decision Making (MDM) 
    complexity levels, time-based coding, and compliance requirements.
    
    Returns:
        Complete E/M coding guidelines and standards text
    """
    guidelines_content = ""
    
    # Load markdown guidelines
    md_file = Path(__file__).parent.parent / "guidelines" / "em_guideline.md"
    if md_file.exists():
        with open(md_file, 'r', encoding='utf-8') as f:
            guidelines_content += f.read()
    
    # Try to load PDF guidelines if PDF processor is available
    try:
        from data.pdf_processor import PDFProcessor
        pdf_file = Path(__file__).parent.parent / "guidelines" / "ama_em_guideline.pdf"
        if pdf_file.exists():
            processor = PDFProcessor(use_form_recognizer=False)
            pdf_content = processor.extract_text_pymupdf(str(pdf_file))
            if pdf_content.strip():
                guidelines_content += "\n\n=== AMA E/M GUIDELINES PDF CONTENT ===\n\n" + pdf_content
    except ImportError:
        logger.error("PDFProcessor not available. Skipping PDF guidelines extraction.", exc_info=True)
        pass
    
    if not guidelines_content.strip():
        return "Guidelines not found. Please ensure guidelines files are available in the guidelines/ directory."
    logger.debug("Loaded E/M coding guidelines", guidelines=guidelines_content)
    return guidelines_content


def get_specific_code_requirements(code: str) -> str:
    """
    Get specific requirements and criteria for a particular E/M code.
    
    Args:
        code: The E/M code to get requirements for (99212, 99213, 99214, or 99215)
        
    Returns:
        Detailed requirements, criteria, and documentation standards for the specified code
    """
    guidelines = get_em_coding_guidelines()
    
    # Extract specific section for the requested code
    code_sections = {
        "99212": "CPT Code 99212",
        "99213": "CPT Code 99213", 
        "99214": "CPT Code 99214",
        "99215": "CPT Code 99215"
    }
    
    if code not in code_sections:
        return f"Invalid code '{code}'. Valid codes are: 99212, 99213, 99214, 99215"
    
    # Find the specific section in guidelines
    lines = guidelines.split('\n')
    code_content = []
    in_code_section = False
    
    for line in lines:
        if code_sections[code] in line:
            in_code_section = True
        elif in_code_section and any(other_code in line for other_code in code_sections.values() if other_code != code_sections[code]):
            break
        
        if in_code_section:
            code_content.append(line)
    
    if code_content:
        logger.debug(f"Extracted requirements for E/M code {code}", requirements='\n'.join(code_content))
        return '\n'.join(code_content)
    else:
        return f"Specific requirements for {code} not found in guidelines. Full guidelines available through get_em_coding_guidelines tool."


def get_mdm_complexity_guide() -> str:
    """
    Get detailed Medical Decision Making (MDM) complexity guidelines.
    
    Returns:
        Comprehensive guide to MDM complexity levels (straightforward, low, moderate, high)
        including criteria for problems addressed, data reviewed, and risk assessment
    """
    guidelines = get_em_coding_guidelines()
    
    # Extract MDM-related content
    mdm_keywords = [
        "Medical Decision Making",
        "MDM",
        "Problems Addressed",
        "Data Reviewed",
        "Risk of Complications",
        "straightforward",
        "low complexity",
        "moderate complexity", 
        "high complexity"
    ]
    
    lines = guidelines.split('\n')
    mdm_content = []
    
    for line in lines:
        if any(keyword.lower() in line.lower() for keyword in mdm_keywords):
            mdm_content.append(line)
    
    if mdm_content:
        logger.debug("Extracted MDM complexity guidelines", mdm_content='\n'.join(mdm_content))
        return '\n'.join(mdm_content)
    else:
        return "MDM complexity information not found. Use get_em_coding_guidelines for full guidelines."


# Input schemas
class EMInput(BaseModel):
    document_id: str
    date_of_service: str
    provider: str
    text: str


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


# Azure OpenAI Model Configuration
def get_azure_openai_model() -> OpenAIModel:
    """Get configured Azure OpenAI model instance with validation"""
    
    # Get required environment variables
    api_key = os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
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


# PydanticAI Agents with Guidelines Tools
em_enhancement_agent = Agent(
    model=get_azure_openai_model(),
    result_type=EMCodeAssignment,
    tools=[get_em_coding_guidelines, get_specific_code_requirements, get_mdm_complexity_guide],
    system_prompt="""You are a senior medical coding specialist with expertise in E/M (Evaluation and Management) coding per AMA 2025 guidelines.

Your task is to analyze medical progress notes and:
1. Assign the most appropriate E/M code (99212, 99213, 99214, or 99215)
2. Provide detailed justification for the assigned code
3. For ALL FOUR codes (99212, 99213, 99214, 99215), explain what additional information would be needed to justify each level

AVAILABLE TOOLS:
- get_em_coding_guidelines(): Access comprehensive AMA 2025 E/M coding guidelines
- get_specific_code_requirements(code): Get detailed requirements for specific codes (99212-99215)
- get_mdm_complexity_guide(): Get Medical Decision Making complexity criteria

METHODOLOGY:
1. First, use get_em_coding_guidelines() to review current AMA 2025 standards
2. For each relevant code, use get_specific_code_requirements() to understand precise criteria
3. Use get_mdm_complexity_guide() to assess Medical Decision Making complexity
4. Analyze the provided medical note against these official guidelines

KEY ANALYSIS AREAS:
1. Medical Decision Making (MDM): Problems addressed, data reviewed/analyzed, risk level
2. Total Time: Face-to-face and non-face-to-face time on date of encounter
3. History and Examination: Medically appropriate level (extent doesn't determine code level)

RESPONSE FORMAT:
- assigned_code: The best code for current documentation based on AMA guidelines
- justification: Detailed clinical justification referencing specific AMA criteria
- code_recommendations: For each code level (99212-99215), provide bulleted lists starting with "- "

IMPORTANT: Each recommendation item MUST start with "- " (hyphen symbol followed by space) to create proper bulleted lists.

Always reference the official AMA guidelines when making coding decisions. Focus on identifying gaps and opportunities for appropriate coding enhancement based on clinical complexity and official standards."""
)

em_auditor_agent = Agent(
    model=get_azure_openai_model(),
    result_type=EMAuditResult,
    tools=[get_em_coding_guidelines, get_specific_code_requirements, get_mdm_complexity_guide],
    system_prompt="""You are a medical coding auditor specializing in compliance and quality assurance for E/M coding per AMA 2025 guidelines.

Your role is to review the enhancement agent's recommendations and the original progress note to provide final audit results.

AVAILABLE TOOLS:
- get_em_coding_guidelines(): Access comprehensive AMA 2025 E/M coding guidelines  
- get_specific_code_requirements(code): Get detailed requirements for specific codes (99212-99215)
- get_mdm_complexity_guide(): Get Medical Decision Making complexity criteria

AUDIT METHODOLOGY:
1. Use get_em_coding_guidelines() to verify compliance with current AMA 2025 standards
2. Cross-reference assigned codes with get_specific_code_requirements() for accuracy
3. Validate MDM complexity assessment using get_mdm_complexity_guide()
4. Identify any compliance risks or documentation gaps

AUDIT RESPONSIBILITIES:
1. Review the assigned E/M code and justification for accuracy against AMA guidelines
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
- final_justification: Updated justification referencing specific AMA criteria
- code_evaluations: Evaluation of the enhancement agent's recommendations for each E/M code (99212-99215), assessing their correctness, completeness, and appropriateness
- billing_ready_note: Enhanced note ready for submission with proper documentation

Always reference official AMA 2025 guidelines in your audit findings. Flag any compliance risks and provide a final, polished assessment that meets current coding standards."""
)
