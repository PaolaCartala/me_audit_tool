"""Pydantic models for user feedback data."""

from datetime import datetime
from typing import Any, Dict, Optional, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from constants import UserAction


class UserFeedbackRequest(BaseModel):
    """Model for incoming user feedback request."""
    
    suggested_em_code: str = Field(..., description="The EM code suggested by the system")
    current_em_code: str = Field(..., description="The current EM code")
    final_em_code: str = Field(..., description="The final EM code chosen")
    user_action: Literal["accepted", "rejected"] = Field(..., description="User action: accepted or rejected")
    reject_reason: Optional[str] = Field(None, description="Reason for rejection if applicable")
    user_id: str = Field(..., description="MKO GUID of the user")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the suggestion")
    raw_agent_result: Dict[str, Any] = Field(..., description="Full JSON result from agent")
    
    @field_validator('user_action')
    @classmethod
    def validate_user_action(cls, v: str) -> str:
        """Validate user action against allowed values."""
        if v not in [UserAction.ACCEPTED.value, UserAction.REJECTED.value]:
            raise ValueError(f"user_action must be either '{UserAction.ACCEPTED.value}' or '{UserAction.REJECTED.value}'")
        return v
    
    @field_validator('reject_reason')
    @classmethod
    def validate_reject_reason(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate reject_reason is provided when user_action is rejected."""
        if info.data and 'user_action' in info.data:
            user_action = info.data['user_action']
            if user_action == UserAction.REJECTED.value and not v:
                raise ValueError("reject_reason is required when user_action is 'rejected'")
        return v


class UserFeedbackEntity(BaseModel):
    """Model for Azure Table entity with partitioning keys."""
    
    # Azure Table keys
    partition_key: str = Field(..., description="Partition key for Azure Tables")
    row_key: str = Field(..., description="Row key for Azure Tables")
    
    # Feedback data
    suggested_em_code: str
    current_em_code: str
    final_em_code: str
    user_action: str
    user_action_timestamp: datetime
    reject_reason: Optional[str]
    user_id: str
    confidence_score: float
    raw_agent_result: Dict[str, Any]
    
    # System timestamp
    system_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_request(cls, request: UserFeedbackRequest) -> "UserFeedbackEntity":
        """Create entity from request with appropriate partitioning strategy."""
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        unique_id = str(uuid4())[:8]
        
        # Generate timestamp when creating entity
        user_action_timestamp = datetime.utcnow()
        
        return cls(
            # Partitioning strategy: user-based partitions
            partition_key=request.user_id,
            row_key=f"{timestamp_str}_{request.suggested_em_code}_{unique_id}",
            
            # Data fields
            suggested_em_code=request.suggested_em_code,
            current_em_code=request.current_em_code,
            final_em_code=request.final_em_code,
            user_action=request.user_action,
            user_action_timestamp=user_action_timestamp,
            reject_reason=request.reject_reason,
            user_id=request.user_id,
            confidence_score=request.confidence_score,
            raw_agent_result=request.raw_agent_result,
        )
    
    def to_azure_entity(self) -> Dict[str, Any]:
        """Convert to Azure Table entity format."""
        entity = {
            "PartitionKey": self.partition_key,
            "RowKey": self.row_key,
            "SuggestedEmCode": self.suggested_em_code,
            "CurrentEmCode": self.current_em_code,
            "FinalEmCode": self.final_em_code,
            "UserAction": self.user_action,
            "UserActionTimestamp": self.user_action_timestamp.isoformat(),
            "RejectReason": self.reject_reason or "",
            "UserId": self.user_id,
            "ConfidenceScore": self.confidence_score,
            "RawAgentResult": str(self.raw_agent_result),
            "SystemTimestamp": self.system_timestamp.isoformat(),
        }
        return entity
