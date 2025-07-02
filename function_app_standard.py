import azure.functions as func
import json
import logging
import asyncio
from typing import List, Dict, Any
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


@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    try:
        return func.HttpResponse(
            json.dumps({
                "status": "healthy",
                "service": "E/M Coding API (Standard Functions)",
                "version": "2.0"
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
    Main E/M Coding endpoint - Standard implementation without Durable Functions
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
        
        # Initialize orchestrator
        # Durable orchestrator removed
        
        # Process document
        # Durable orchestrator removed
        
        return func.HttpResponse(
            json.dumps({
                "status": "completed",
                "document_id": req_body.get("document_id"),
                "result": None  # Durable orchestrator removed
            }, default=str),
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
    Batch E/M Coding endpoint - Standard implementation
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
        
        # Validate and create EMInput objects
        em_inputs = []
        validation_errors = []
        
        for i, doc in enumerate(documents):
            try:
                required_fields = ["document_id", "date_of_service", "provider", "text"]
                missing_fields = [field for field in required_fields if field not in doc]
                
                if missing_fields:
                    validation_errors.append(f"Document {i}: Missing fields {missing_fields}")
                    continue
                
                em_input = EMInput(**doc)
                em_inputs.append(em_input)
                
            except Exception as e:
                validation_errors.append(f"Document {i}: {str(e)}")
        
        if validation_errors:
            return func.HttpResponse(
                json.dumps({"error": "Validation errors", "details": validation_errors}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Initialize orchestrator
        orchestrator = EMCodingOrchestrator()
        
        # Process documents in batch
        # Durable orchestrator removed
        
        return func.HttpResponse(
            json.dumps({
                "status": "completed",
                "total_documents": len(documents),
                "processed_documents": 0,  # Durable orchestrator removed
                "results": []  # Durable orchestrator removed
            }, default=str),
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


@app.route(route="test_samples", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def test_samples_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Test endpoint that processes sample PDFs
    """
    try:
        # Get limit parameter (default to 3 for testing)
        limit = int(req.params.get('limit', '3'))
        limit = min(limit, 5)  # Cap at 5 for testing
        
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
        
        # Initialize orchestrator
        orchestrator = EMCodingOrchestrator()
        
        # Process samples
        # Durable orchestrator removed
        
        response_data = {
            "message": "Processed 0 sample documents (Durable orchestrator removed)",
            "total_samples_found": len(sample_inputs),
            "processed_count": 0,
            "results": []
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


@app.route(route="excel_export", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
async def excel_export_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Excel export endpoint - Processes documents and returns data in Excel format
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
        em_inputs = [EMInput(**doc) for doc in documents]
        
        # Initialize orchestrator
        orchestrator = EMCodingOrchestrator()
        
        # Process documents and generate Excel data
        # Durable orchestrator removed
        # Durable orchestrator removed
        
        return func.HttpResponse(
            json.dumps({
                "status": "completed",
                "excel_data": None,  # Durable orchestrator removed
                "total_documents": len(documents)
            }, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Excel export error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Excel export failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
