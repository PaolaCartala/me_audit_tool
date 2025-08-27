"""
PDF Processing Utility for Medical Progress Notes
Extracts text from PDF files and prepares them for E/M coding analysis
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import fitz  # PyMuPDF
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

from agents.models.pydantic_models import EMInput
from settings import logger

# Load environment variables
load_dotenv()


class PDFProcessor:
    """Process PDF files containing medical progress notes"""
    
    def __init__(self, use_form_recognizer: bool = False):
        self.use_form_recognizer = use_form_recognizer
        if use_form_recognizer:
            self._init_form_recognizer()
    
    def _init_form_recognizer(self):
        """Initialize Azure Form Recognizer client if configured"""
        endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
        key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
        
        if endpoint and key:
            self.document_client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
        else:
            logger.warning("Azure Form Recognizer not configured, falling back to PyMuPDF")
            self.use_form_recognizer = False
    
    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF (fallback method)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def extract_text_form_recognizer(self, pdf_path: str) -> str:
        """Extract text from PDF using Azure Form Recognizer"""
        try:
            with open(pdf_path, "rb") as f:
                poller = self.document_client.begin_analyze_document(
                    "prebuilt-layout", f
                )
            result = poller.result()
            
            # Combine all text content
            text = ""
            for page in result.pages:
                for line in page.lines:
                    text += line.content + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error with Form Recognizer for {pdf_path}: {str(e)}")
            # Fallback to PyMuPDF
            return self.extract_text_pymupdf(pdf_path)
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using the configured method"""
        if self.use_form_recognizer and hasattr(self, 'document_client'):
            return self.extract_text_form_recognizer(pdf_path)
        else:
            return self.extract_text_pymupdf(pdf_path)
    
    def extract_metadata_from_text(self, text: str, filename: str) -> Dict[str, str]:
        """Extract metadata from PDF text content using regex patterns"""
        # Initialize with filename as document_id
        metadata = {
            "document_id": Path(filename).stem,
            "date_of_service": None,
            "provider": None
        }
        
        # Extract Date of Service
        # Pattern for "Date of Service" or "DATE OF SERVICE" followed by various date formats
        # Matches formats like "June 25, 2025", "06/25/2025", "06-25-2025", etc.
        date_pattern = r'(?:date\s+of\s+service|DATE\s+OF\s+SERVICE)[:\s]*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
        date_match = re.search(date_pattern, text, re.IGNORECASE)
        if date_match:
            # Keep the date as found in the text without normalization
            metadata["date_of_service"] = date_match.group(1).strip()
        
        # Alternative pattern for "DATE:" followed by date
        if not metadata["date_of_service"]:
            alt_date_pattern = r'DATE:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
            alt_date_match = re.search(alt_date_pattern, text, re.IGNORECASE)
            if alt_date_match:
                metadata["date_of_service"] = alt_date_match.group(1).strip()
        
        # Extract Provider from electronic signature
        # Pattern for "Electronically signed by [Provider Name] on Date"
        provider_pattern = r'Electronically\s+signed\s+by\s+([^,\n]+(?:,\s*[A-Z]+)?)\s+on\s+Date'
        provider_match = re.search(provider_pattern, text, re.IGNORECASE)
        if provider_match:
            metadata["provider"] = provider_match.group(1).strip()
        
        # Alternative pattern for "Electronically Signed By: [Name], Date:"
        if not metadata["provider"]:
            alt_provider_pattern = r'Electronically\s+Signed\s+By:\s*([^,\n]+(?:,\s*[A-Z\s]+)?),\s*Date:'
            alt_provider_match = re.search(alt_provider_pattern, text, re.IGNORECASE)
            if alt_provider_match:
                metadata["provider"] = alt_provider_match.group(1).strip()
        
        # Fallback patterns if the main patterns don't match
        if not metadata["provider"]:
            # Alternative pattern for "signed by [name]"
            fallback_provider_pattern = r'signed\s+by\s+([^,\n]+(?:,\s*[A-Z]+)?)'
            fallback_match = re.search(fallback_provider_pattern, text, re.IGNORECASE)
            if fallback_match:
                metadata["provider"] = fallback_match.group(1).strip()
        
        # If date_of_service not found, use placeholder
        if not metadata["date_of_service"]:
            metadata["date_of_service"] = "2024-01-01"
            logger.warning(f"Could not extract date of service from text for {filename}")
        
        # If provider not found, use placeholder
        if not metadata["provider"]:
            metadata["provider"] = "Unknown Provider"
            logger.warning(f"Could not extract provider from text for {filename}")
        
        return metadata
    
    def extract_metadata_from_filename(self, pdf_path: str) -> Dict[str, str]:
        """Extract document_id from PDF filename"""
        filename = Path(pdf_path).stem
        
        # Only extract document_id from filename
        # Other metadata should be extracted from text content
        return {
            "document_id": filename
        }
    
    def process_pdf_to_em_input(self, pdf_path: str) -> Optional[EMInput]:
        """Process a single PDF and convert to EMInput format"""
        try:
            # Extract text content
            text = self.extract_text(pdf_path)
            if not text:
                logger.warning(f"No text extracted from {pdf_path}")
                return None
            
            # Extract metadata from text content
            metadata = self.extract_metadata_from_text(text, pdf_path)
            
            return EMInput(
                document_id=metadata["document_id"],
                date_of_service=metadata["date_of_service"],
                provider=metadata["provider"],
                text=text
            )
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return None
    
    def process_sample_pdfs(self, sample_dir: str, limit: int = 10) -> List[EMInput]:
        """Process multiple PDF samples for testing"""
        sample_path = Path(sample_dir)
        pdf_files = list(sample_path.glob("*.pdf"))[:limit]
        
        logger.debug(f"Processing {len(pdf_files)} PDF files from {sample_dir}")
        
        results = []
        for pdf_file in pdf_files:
            em_input = self.process_pdf_to_em_input(str(pdf_file))
            if em_input:
                results.append(em_input)
        
        logger.debug(f"Successfully processed {len(results)} PDFs")
        return results


# Convenience function
def process_pdf_samples(sample_dir: str = "data/samples", limit: int = 10) -> List[EMInput]:
    """Process PDF samples for testing"""
    processor = PDFProcessor(use_form_recognizer=False)  # Start with PyMuPDF
    return processor.process_sample_pdfs(sample_dir, limit)
