import os
from functools import lru_cache

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=None)
def get_optimized_azure_openai_model(model="gpt-5") -> OpenAIModel:
    """Get configured Azure OpenAI model instance with optimized settings"""
    
    if model not in ["gpt-5-mini", "gpt-5-nano"]:
        endpoint = "https://ptm-me2x3s2u-swedencentral.cognitiveservices.azure.com/"
    else:
        endpoint = "https://audit-tool-agent.cognitiveservices.azure.com/"
    api_version = '2024-12-01-preview'
    
    if not api_key:
        raise ValueError("AZURE_OPENAI_KEY environment variable is required")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
    if not api_version:
        raise ValueError("AZURE_OPENAI_API_VERSION environment variable is required")
    
    return OpenAIModel(
        model,
        provider=AzureProvider(
            azure_endpoint=endpoint, 
            api_version=api_version, 
            api_key=api_key
        )
    )