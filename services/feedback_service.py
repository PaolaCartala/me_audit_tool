"""Service for handling user feedback storage in Azure Tables."""

from typing import Dict, Any, Optional
from datetime import datetime

from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError, AzureError

from agents.models.feedback_models import UserFeedbackRequest, UserFeedbackEntity
from constants import azure_config
from settings import logger


class FeedbackStorageService:
    """Service for storing user feedback in Azure Tables."""
    
    def __init__(self):
        """Initialize the service with Azure Tables connection."""
        # self.connection_string = azure_config.storage_connection_string
        self.table_name = azure_config.feedback_table_name
        
        self.table_service_client = TableServiceClient.from_connection_string(
            conn_str=self.connection_string
        )
        self.table_client = self.table_service_client.get_table_client(self.table_name)
        
        # Ensure table exists
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """Ensure the feedback table exists, create if not."""
        try:
            self.table_service_client.create_table(self.table_name)
            logger.debug(
                "Created feedback table",
                table_name=self.table_name,
                function=f"{__name__}.{self.__class__.__name__}._ensure_table_exists"
            )
        except ResourceExistsError:
            logger.debug(
                "Feedback table already exists",
                table_name=self.table_name,
                function=f"{__name__}.{self.__class__.__name__}._ensure_table_exists"
            )
        except Exception as e:
            logger.error(
                "Failed to ensure feedback table exists",
                table_name=self.table_name,
                error=str(e),
                function=f"{__name__}.{self.__class__.__name__}._ensure_table_exists",
                exc_info=True
            )
            raise
    
    def store_feedback(self, feedback_request: UserFeedbackRequest) -> Dict[str, str]:
        """
        Store user feedback in Azure Tables.
        
        Args:
            feedback_request: The feedback data from the user
            
        Returns:
            Dict containing the partition_key and row_key of the stored entity
            
        Raises:
            AzureError: If there's an error storing the feedback
        """
        try:
            # Convert request to entity with partitioning strategy
            entity = UserFeedbackEntity.from_request(feedback_request)
            
            # Convert to Azure Table entity format
            azure_entity = entity.to_azure_entity()
            
            # Store in Azure Tables
            result = self.table_client.create_entity(entity=azure_entity)
            
            logger.debug(
                "Successfully stored user feedback",
                partition_key=entity.partition_key,
                row_key=entity.row_key,
                user_id=feedback_request.user_id,
                suggested_em_code=feedback_request.suggested_em_code,
                user_action=feedback_request.user_action,
                function=f"{__name__}.{self.__class__.__name__}.store_feedback"
            )
            
            return {
                "partition_key": entity.partition_key,
                "row_key": entity.row_key,
                "status": "success",
                "message": "Feedback stored successfully"
            }
            
        except AzureError as e:
            logger.error(
                "Azure error while storing feedback",
                error=str(e),
                user_id=feedback_request.user_id,
                suggested_em_code=feedback_request.suggested_em_code,
                function=f"{__name__}.{self.__class__.__name__}.store_feedback",
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error while storing feedback",
                error=str(e),
                user_id=feedback_request.user_id,
                suggested_em_code=feedback_request.suggested_em_code,
                function=f"{__name__}.{self.__class__.__name__}.store_feedback",
                exc_info=True
            )
            raise
    
    def get_feedback_by_user(
        self, 
        user_id: str, 
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve feedback entries for a specific user.
        
        Args:
            user_id: The user ID to query feedback for
            limit: Optional limit on number of results
            
        Returns:
            Dict containing feedback entries and metadata
        """
        try:
            # Query by partition key (user_id)
            filter_query = f"PartitionKey eq '{user_id}'"
            
            entities = list(self.table_client.query_entities(
                query_filter=filter_query,
                results_per_page=limit
            ))
            
            logger.debug(
                "Retrieved user feedback",
                user_id=user_id,
                count=len(entities),
                function=f"{__name__}.{self.__class__.__name__}.get_feedback_by_user"
            )
            
            return {
                "user_id": user_id,
                "count": len(entities),
                "feedback_entries": entities
            }
            
        except Exception as e:
            logger.error(
                "Error retrieving user feedback",
                user_id=user_id,
                error=str(e),
                function=f"{__name__}.{self.__class__.__name__}.get_feedback_by_user",
                exc_info=True
            )
            raise
    
    def get_feedback_by_em_code(
        self, 
        em_code: str, 
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve feedback entries for a specific EM code across all users.
        
        Args:
            em_code: The EM code to query feedback for
            limit: Optional limit on number of results
            
        Returns:
            Dict containing feedback entries and metadata
        """
        try:
            # Query by SuggestedEmCode field
            filter_query = f"SuggestedEmCode eq '{em_code}'"
            
            entities = list(self.table_client.query_entities(
                query_filter=filter_query,
                results_per_page=limit
            ))
            
            logger.debug(
                "Retrieved EM code feedback",
                em_code=em_code,
                count=len(entities),
                function=f"{__name__}.{self.__class__.__name__}.get_feedback_by_em_code"
            )
            
            return {
                "em_code": em_code,
                "count": len(entities),
                "feedback_entries": entities
            }
            
        except Exception as e:
            logger.error(
                "Error retrieving EM code feedback",
                em_code=em_code,
                error=str(e),
                function=f"{__name__}.{self.__class__.__name__}.get_feedback_by_em_code",
                exc_info=True
            )
            raise
