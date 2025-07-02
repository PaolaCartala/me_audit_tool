import azure.functions as func
import json
import logging
import asyncio
import uuid
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from models.pydantic_models import EMInput

from data.pdf_processor import process_pdf_samples

# Load environment variables
load_dotenv()

# Initialize the Azure Functions app
app = func.FunctionApp()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for tracking processing status (for demo purposes)
processing_status = {}


@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    try:
        return func.HttpResponse(
            json.dumps({
                "status": "healthy",
                "service": "E/M Coding API",
                "version": "1.0",
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({"status": "unhealthy", "error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="em_coding", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
async def em_coding_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main E/M Coding endpoint - Synchronous processing
    Accepts single document processing requests
    """
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate required fields
        required_fields = ["document_id", "date_of_service", "provider", "text"]
        missing_fields = [field for field in required_fields if field not in req_body]
        
        if missing_fields:
            return func.HttpResponse(
                json.dumps({"error": f"Missing required fields: {missing_fields}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Create EMInput object
        em_input = EMInput(**req_body)
        
        # Initialize orchestrator and process
        # Durable orchestrator removed
        # Durable orchestrator removed
        
        # Return result
        response_data = {
            "status": "completed",
            "document_id": em_input.document_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Invalid input: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Processing failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="batch_em_coding", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
async def batch_em_coding_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Batch E/M Coding endpoint - Synchronous batch processing
    Accepts multiple documents for processing
    """
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body or "documents" not in req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body with 'documents' array is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        documents = req_body["documents"]
        if not documents or len(documents) == 0:
            return func.HttpResponse(
                json.dumps({"error": "At least one document is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Limit batch size for performance
        max_batch_size = 10
        if len(documents) > max_batch_size:
            return func.HttpResponse(
                json.dumps({"error": f"Maximum batch size is {max_batch_size} documents"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Process documents
        orchestrator = EMCodingOrchestrator()
        results = []
        errors = []
        
        for i, doc in enumerate(documents):
            try:
                # Validate document structure
                required_fields = ["document_id", "date_of_service", "provider", "text"]
                missing_fields = [field for field in required_fields if field not in doc]
                
                if missing_fields:
                    errors.append({
                        "document_index": i,
                        "document_id": doc.get("document_id", f"unknown_{i}"),
                        "error": f"Missing required fields: {missing_fields}"
                    })
                    continue
                
                # Create EMInput and process
                em_input = EMInput(**doc)
                # Durable orchestrator removed
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process document {i}: {str(e)}")
                errors.append({
                    "document_index": i,
                    "document_id": doc.get("document_id", f"unknown_{i}"),
                    "error": str(e)
                })
        
        # Generate summary
        summary = orchestrator.generate_summary_report(results) if results else {}
        
        response_data = {
            "status": "completed",
            "total_documents": len(documents),
            "successful_results": len(results),
            "failed_documents": len(errors),
            "results": results,
            "errors": errors,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Batch processing failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="async_em_coding", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
async def async_em_coding_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Asynchronous E/M Coding endpoint - Returns immediately with tracking ID
    """
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Generate unique tracking ID
        tracking_id = str(uuid.uuid4())
        
        # Store initial status
        processing_status[tracking_id] = {
            "status": "started",
            "document_id": req_body.get("document_id", "unknown"),
            "created_time": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Start background processing (simplified - in production use proper async processing)
        asyncio.create_task(process_async_document(tracking_id, req_body))
        
        response_data = {
            "tracking_id": tracking_id,
            "status": "started",
            "document_id": req_body.get("document_id"),
            "message": "Document processing started. Use tracking_id to check status.",
            "status_url": f"/api/check_status/{tracking_id}"
        }
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=202,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Failed to start async processing: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to start processing: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="check_status/{tracking_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def check_status_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Check the status of asynchronous processing
    """
    try:
        tracking_id = req.route_params.get("tracking_id")
        if not tracking_id:
            return func.HttpResponse(
                json.dumps({"error": "Tracking ID is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get status from in-memory storage
        status_data = processing_status.get(tracking_id)
        
        if status_data is None:
            return func.HttpResponse(
                json.dumps({"error": "Tracking ID not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps(status_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Failed to check status: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to check status: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="test_samples", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def test_samples_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Test endpoint that processes sample PDFs
    """
    try:
        # Get limit parameter (default to 3 for testing)
        limit = int(req.params.get('limit', '3'))
        limit = min(limit, 5)  # Cap at 5 for safety
        
        # Process sample PDFs to get EMInput objects
        sample_inputs = process_pdf_samples(limit=limit)
        
        if not sample_inputs:
            return func.HttpResponse(
                json.dumps({
                    "message": "No sample PDFs found in data/samples directory",
                    "results": []
                }),
                status_code=200,
                mimetype="application/json"
            )
        
        # Process samples
        orchestrator = EMCodingOrchestrator()
        results = []
        
        for sample_input in sample_inputs:
            try:
                # Durable orchestrator removed
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process sample {sample_input.document_id}: {str(e)}")
                results.append({
                    "document_id": sample_input.document_id,
                    "status": "error",
                    "error": str(e)
                })
        
        # Generate summary
        summary = orchestrator.generate_summary_report([r for r in results if r.get("status") != "error"])
        
        response_data = {
            "message": f"Processed {len(results)} sample documents",
            "total_samples_found": len(sample_inputs),
            "successful_results": len([r for r in results if r.get("status") != "error"]),
            "results": results,
            "summary": summary
        }
        
        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Test samples error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Test samples failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


async def process_async_document(tracking_id: str, req_body: dict):
    """
    Background processing function for async requests
    """
    try:
        # Update status to processing
        processing_status[tracking_id].update({
            "status": "processing",
            "last_updated": datetime.utcnow().isoformat()
        })
        
        # Validate and create EMInput
        required_fields = ["document_id", "date_of_service", "provider", "text"]
        missing_fields = [field for field in required_fields if field not in req_body]
        
        if missing_fields:
            processing_status[tracking_id].update({
                "status": "failed",
                "error": f"Missing required fields: {missing_fields}",
                "last_updated": datetime.utcnow().isoformat()
            })
            return
        
        em_input = EMInput(**req_body)
        
        # Process document
        orchestrator = EMCodingOrchestrator()
        # Durable orchestrator removed
        
        # Update status with result
        processing_status[tracking_id].update({
            "status": "completed",
            "result": result,
            "last_updated": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Async processing failed for {tracking_id}: {str(e)}")
        processing_status[tracking_id].update({
            "status": "failed",
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat()
        })
