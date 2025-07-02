import os
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Input schemas
class EMInput(BaseModel):
    document_id: str
    date_of_service: str
    provider: str
    text: str


# Response schemas for PydanticAI agents
class EMCodeRecommendations(BaseModel):
    """Recommendations for each E/M code level"""
    code_99212: str = Field(description="Recommendations for additional information needed to justify 99212")
    code_99213: str = Field(description="Recommendations for additional information needed to justify 99213") 
    code_99214: str = Field(description="Recommendations for additional information needed to justify 99214")
    code_99215: str = Field(description="Recommendations for additional information needed to justify 99215")


class EMCodeAssignment(BaseModel):
    """Response schema for E/M code assignment with recommendations for all levels"""
    assigned_code: str = Field(description="The most appropriate E/M code assigned (99212, 99213, 99214, or 99215)")
    justification: str = Field(description="Detailed clinical justification for the assigned code")
    code_recommendations: EMCodeRecommendations = Field(description="Recommendations for all E/M code levels")


class EMAuditResult(BaseModel):
    """Response schema for E/M audit result"""
    audit_flags: List[str] = Field(description="List of compliance risks or missing statements")
    final_assigned_code: str = Field(description="Final E/M code after audit review")
    final_justification: str = Field(description="Final justification after audit")
    final_code_recommendations: EMCodeRecommendations = Field(description="Final recommendations for all E/M codes after audit")
    billing_ready_note: str = Field(description="Final version of the provider note ready for billing submission")


class EMEnhancementOutput(BaseModel):
    document_id: str
    assigned_code: str
    justification: str
    code_recommendations: EMCodeRecommendations


class EMAuditOutput(BaseModel):
    document_id: str
    audit_flags: List[str]
    final_assigned_code: str
    final_justification: str
    final_code_recommendations: EMCodeRecommendations
    billing_ready_note: str


class EMAuditResult(BaseModel):
    """Response schema for E/M audit result"""
    audit_flags: List[str] = Field(description="List of compliance risks or missing statements")
    final_assigned_code: str = Field(description="Final E/M code after audit review")
    final_justification: str = Field(description="Final justification after audit")
    final_code_recommendations: EMCodeRecommendations = Field(description="Final recommendations for all E/M codes after audit")
    billing_ready_note: str = Field(description="Final version of the provider note ready for billing submission")


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


# PydanticAI Agents
em_enhancement_agent = Agent(
    model=get_azure_openai_model(),
    result_type=EMCodeAssignment,
    system_prompt="""You are a senior medical coding specialist with expertise in E/M (Evaluation and Management) coding per AMA 2024 guidelines.

Your task is to analyze medical progress notes and:
1. Assign the most appropriate E/M code (99212, 99213, 99214, or 99215)
2. Provide detailed justification for the assigned code
3. For ALL FOUR codes (99212, 99213, 99214, 99215), explain what additional information would be needed to justify each level

CODING GUIDELINES:
- 99212: Problem focused visit, straightforward medical decision making (2 of 3 key components)
- 99213: Expanded problem focused, low complexity medical decision making (2 of 3 key components)  
- 99214: Detailed visit, moderate complexity medical decision making (2 of 3 key components)
- 99215: Comprehensive visit, high complexity medical decision making (2 of 3 key components)

KEY COMPONENTS TO EVALUATE:
1. History: Chief complaint, HPI, ROS, PFSH
2. Examination: Constitutional, affected body areas/organ systems
3. Medical Decision Making: Problems addressed, data reviewed, risk level

RESPONSE FORMAT:
- assigned_code: The best code for current documentation
- justification: Why this code fits the current documentation
- code_recommendations: For each code level (99212-99215), specify what additional documentation would be needed

Focus on identifying gaps and opportunities for appropriate coding enhancement based on clinical complexity."""
)

em_auditor_agent = Agent(
    model=get_azure_openai_model(),
    result_type=EMAuditResult,
    system_prompt="""You are a medical coding auditor specializing in compliance and quality assurance for E/M coding.

Your role is to review the enhancement agent's recommendations and the original progress note to provide final audit results.

AUDIT RESPONSIBILITIES:
1. Review the assigned E/M code and justification for accuracy
2. Evaluate the recommendations for all code levels (99212-99215)
3. Identify compliance risks or missing documentation
4. Provide final code assignment and recommendations
5. Create a billing-ready version of the provider note

AUDIT FOCUS AREAS:
1. Code justification alignment with actual documentation
2. Missing clinical elements that could affect code assignment
3. Compliance risks or red flags
4. Documentation completeness for billing submission

COMPLIANCE REQUIREMENTS:
- Medical necessity clearly documented
- All code components adequately supported
- No upcoding without proper justification
- Clear clinical decision making rationale

RESPONSE FORMAT:
- audit_flags: List any compliance issues found
- final_assigned_code: Final E/M code after audit review
- final_justification: Updated justification if needed
- final_code_recommendations: Refined recommendations for all codes
- billing_ready_note: Enhanced note ready for submission

Flag any compliance risks and provide a final, polished assessment."""
)
