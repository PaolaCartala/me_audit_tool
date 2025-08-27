"""Azure Function for retrieving user feedback analytics."""

import json
from typing import Dict, Any, Optional
from http import HTTPStatus

import azure.functions as func
from azure.core.exceptions import AzureError

from services.feedback_service import FeedbackStorageService
from settings import logger


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Retrieve feedback analytics for optimization purposes.
    
    Query parameters:
    - user_id: Get feedback for specific user
    - em_code: Get feedback for specific EM code
    - limit: Limit number of results (optional)
    """
    logger.debug(
        "Received feedback analytics request",
        method=req.method,
        url=req.url,
        function=f"{__name__}.main"
    )
    
    # Validate HTTP method
    if req.method != "GET":
        return func.HttpResponse(
            json.dumps({"error": "Only GET method is allowed"}),
            status_code=HTTPStatus.METHOD_NOT_ALLOWED.value,
            headers={"Content-Type": "application/json"}
        )
    
    try:
        # Parse query parameters
        user_id = req.params.get("user_id")
        em_code = req.params.get("em_code") 
        limit_param = req.params.get("limit")
        
        # Parse limit parameter
        limit: Optional[int] = None
        if limit_param:
            try:
                limit = int(limit_param)
                if limit <= 0:
                    raise ValueError("Limit must be positive")
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid limit parameter"}),
                    status_code=HTTPStatus.BAD_REQUEST.value,
                    headers={"Content-Type": "application/json"}
                )
        
        # Validate that either user_id or em_code is provided
        if not user_id and not em_code:
            return func.HttpResponse(
                json.dumps({
                    "error": "Either user_id or em_code query parameter is required"
                }),
                status_code=HTTPStatus.BAD_REQUEST.value,
                headers={"Content-Type": "application/json"}
            )
        
        # Initialize storage service
        storage_service = FeedbackStorageService()
        
        try:
            if user_id:
                # Get feedback by user
                result = storage_service.get_feedback_by_user(user_id, limit)
                logger.debug(
                    "Retrieved user feedback analytics",
                    user_id=user_id,
                    count=result["count"],
                    function=f"{__name__}.main"
                )
            else:
                # Get feedback by EM code
                result = storage_service.get_feedback_by_em_code(em_code, limit)
                logger.debug(
                    "Retrieved EM code feedback analytics", 
                    em_code=em_code,
                    count=result["count"],
                    function=f"{__name__}.main"
                )
            
            return func.HttpResponse(
                json.dumps(result, default=str),  # default=str to handle datetime serialization
                status_code=HTTPStatus.OK.value,
                headers={"Content-Type": "application/json"}
            )
            
        except AzureError as e:
            logger.error(
                "Azure storage error during feedback retrieval",
                error=str(e),
                user_id=user_id,
                em_code=em_code,
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
                "Unexpected error during feedback retrieval",
                error=str(e),
                user_id=user_id,
                em_code=em_code,
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
            "Critical error in feedback analytics endpoint",
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
