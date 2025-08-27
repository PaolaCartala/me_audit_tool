"""Constants and configuration settings for the EM Audit Tool."""

import os
from enum import Enum
from typing import Optional

from settings import logger


class EnvironmentVariable(Enum):
    """Environment variable names used throughout the application."""
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = "AZURE_OPENAI_ENDPOINT"
    AZURE_OPENAI_KEY = "AZURE_OPENAI_KEY"
    AZURE_OPENAI_DEPLOYMENT_NAME = "AZURE_OPENAI_DEPLOYMENT_NAME"
    AZURE_OPENAI_API_VERSION = "AZURE_OPENAI_API_VERSION"
    
    # Azure Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING = "AZURE_STORAGE_CONNECTION_STRING"
    FEEDBACK_TABLE_NAME = "FEEDBACK_TABLE_NAME"


class DefaultValue(Enum):
    """Default values for configuration settings."""
    
    FEEDBACK_TABLE_NAME = "UserFeedback"


class ConfigurationManager:
    """Centralized configuration manager for environment variables."""
    
    @staticmethod
    def get_env_var(env_var: EnvironmentVariable, default: Optional[str] = None) -> str:
        """
        Get environment variable value with optional default.
        
        Args:
            env_var: Environment variable enum
            default: Optional default value if env var is not set
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required environment variable is not set
        """
        value = os.getenv(env_var.value, default)
        
        if value is None:
            logger.error(
                "Required environment variable not set",
                env_var=env_var.value,
                function=f"{__name__}.ConfigurationManager.get_env_var"
            )
            raise ValueError(f"Environment variable {env_var.value} is required but not set")
        
        logger.debug(
            "Retrieved environment variable",
            env_var=env_var.value,
            has_value=bool(value),
            function=f"{__name__}.ConfigurationManager.get_env_var"
        )
        
        return value
    
    @staticmethod
    def get_optional_env_var(env_var: EnvironmentVariable, default: str) -> str:
        """
        Get optional environment variable with default value.
        
        Args:
            env_var: Environment variable enum
            default: Default value to use if env var is not set
            
        Returns:
            Environment variable value or default
        """
        value = os.getenv(env_var.value, default)
        
        logger.debug(
            "Retrieved optional environment variable",
            env_var=env_var.value,
            using_default=value == default,
            function=f"{__name__}.ConfigurationManager.get_optional_env_var"
        )
        
        return value


class AzureConfig:
    """Azure-specific configuration settings."""
    
    @property
    def openai_endpoint(self) -> str:
        """Get Azure OpenAI endpoint."""
        return ConfigurationManager.get_env_var(EnvironmentVariable.AZURE_OPENAI_ENDPOINT)
    
    @property
    def openai_key(self) -> str:
        """Get Azure OpenAI API key."""
        return ConfigurationManager.get_env_var(EnvironmentVariable.AZURE_OPENAI_KEY)
    
    @property
    def openai_deployment_name(self) -> str:
        """Get Azure OpenAI deployment name."""
        return ConfigurationManager.get_env_var(EnvironmentVariable.AZURE_OPENAI_DEPLOYMENT_NAME)
    
    @property
    def openai_api_version(self) -> str:
        """Get Azure OpenAI API version."""
        return ConfigurationManager.get_optional_env_var(
            EnvironmentVariable.AZURE_OPENAI_API_VERSION,
            DefaultValue.AZURE_OPENAI_API_VERSION.value
        )
    
    @property
    def storage_connection_string(self) -> str:
        """Get Azure Storage connection string."""
        return ConfigurationManager.get_env_var(EnvironmentVariable.AZURE_STORAGE_CONNECTION_STRING)
    
    @property
    def feedback_table_name(self) -> str:
        """Get feedback table name."""
        return ConfigurationManager.get_optional_env_var(
            EnvironmentVariable.FEEDBACK_TABLE_NAME,
            DefaultValue.FEEDBACK_TABLE_NAME.value
        )


class UserAction(Enum):
    """Possible user actions for feedback."""
    
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# Global configuration instance
azure_config = AzureConfig()
