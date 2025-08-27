"""Azure Function for handling user feedback submissions."""

import json
from typing import Dict, Any
from http import HTTPStatus

import azure.functions as func
from azure.core.exceptions import AzureError
from pydantic import ValidationError

from agents.models.feedback_models import UserFeedbackRequest
from services.feedback_service import FeedbackStorageService
from constants import UserAction
from settings import logger


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle user feedback submission to Azure Tables.
    
    Expected JSON payload:
    {
        "suggestedEmCode": "string",
        "currentEmCode": "string", 
        "finalEmCode": "string",
        "userAction": "string (accepted/rejected)",
        "rejectReason": "string (optional)",
        "userId": "string (MKO GUID)",
        "confidenceScore": "number",
        "rawAgentResult": "object"
    }
    
    Note: userActionTimestamp is auto-generated server-side for consistency.
    """
    logger.debug(
        "Received user feedback request",
        method=req.method,
        url=req.url,
        function=f"{__name__}.main"
    )
    
    # Validate HTTP method
    if req.method != "POST":
        return func.HttpResponse(
            json.dumps({"error": "Only POST method is allowed"}),
            status_code=HTTPStatus.METHOD_NOT_ALLOWED.value,
            headers={"Content-Type": "application/json"}
        )
    
    try:
        # Parse request body
        try:
            request_data = req.get_json()
            if not request_data:
                raise ValueError("Empty request body")
        except ValueError as e:
            logger.error(
                "Invalid JSON in request body",
                error=str(e),
                function=f"{__name__}.main"
            )
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=HTTPStatus.BAD_REQUEST.value,
                headers={"Content-Type": "application/json"}
            )
        
        # Convert camelCase keys to snake_case for Pydantic model
        snake_case_data = {
            "suggested_em_code": request_data.get("suggestedEmCode"),
            "current_em_code": request_data.get("currentEmCode"),
            "final_em_code": request_data.get("finalEmCode"),
            "user_action": request_data.get("userAction"),
            # userActionTimestamp will be auto-generated when creating entity
            "reject_reason": request_data.get("rejectReason"),
            "user_id": request_data.get("userId"),
            "confidence_score": request_data.get("confidenceScore"),
            "raw_agent_result": request_data.get("rawAgentResult")
        }
        
        # Validate request data with Pydantic
        try:
            feedback_request = UserFeedbackRequest(**snake_case_data)
        except ValidationError as e:
            logger.error(
                "Validation error in feedback request",
                errors=e.errors(),
                function=f"{__name__}.main"
            )
            return func.HttpResponse(
                json.dumps({
                    "error": "Validation failed",
                    "details": e.errors()
                }),
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
                headers={"Content-Type": "application/json"}
            )
        
        # Initialize storage service and store feedback
        try:
            storage_service = FeedbackStorageService()
            result = storage_service.store_feedback(feedback_request)
            
            logger.debug(
                "Successfully processed feedback submission",
                user_id=feedback_request.user_id,
                suggested_em_code=feedback_request.suggested_em_code,
                user_action=feedback_request.user_action,
                partition_key=result["partition_key"],
                row_key=result["row_key"],
                function=f"{__name__}.main"
            )
            
            return func.HttpResponse(
                json.dumps(result),
                status_code=HTTPStatus.CREATED.value,
                headers={"Content-Type": "application/json"}
            )
            
        except AzureError as e:
            logger.error(
                "Azure storage error during feedback submission",
                error=str(e),
                user_id=feedback_request.user_id,
                function=f"{__name__}.main",
                exc_info=True
            )
            return func.HttpResponse(
                json.dumps({
                    "error": "Storage service unavailable",
                    "message": "Please try again later"
                }),
                status_code=HTTPStatus.SERVICE_UNAVAILABLE.value,
                headers={"Content-Type": "application/json"}
            )
        
        except Exception as e:
            logger.error(
                "Unexpected error during feedback submission",
                error=str(e),
                user_id=feedback_request.user_id,
                function=f"{__name__}.main",
                exc_info=True
            )
            return func.HttpResponse(
                json.dumps({
                    "error": "Internal server error",
                    "message": "An unexpected error occurred"
                }),
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                headers={"Content-Type": "application/json"}
            )
    
    except Exception as e:
        logger.error(
            "Critical error in feedback endpoint",
            error=str(e),
            function=f"{__name__}.main",
            exc_info=True
        )
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "message": "A critical error occurred"
            }),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            headers={"Content-Type": "application/json"}
        )
