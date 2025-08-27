"""
PDF Processing Utility for Medical Progress Notes
Extracts text from PDF files and prepares them for E/M coding analysis
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from dotenv import load_dotenv

from agents.models.pydantic_models import EMInput
from utils.patient_extractor import get_patient_from_pdf_headers
from settings import logger

# Load environment variables
load_dotenv()

# Patrón principal para buscar "Apellido, Nombre (con opcional inicial) MM/DD/YYYY #ID"
PATIENT_PATTERN = re.compile(
    r"(?P<name>[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ-]+,\s*[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ\s]+?)\s+"
    r"(?P<date>\d{2}/\d{2}/\d{4})\s+#(?P<id>\d+)",
    re.IGNORECASE
)

# Patrones de diagnóstico para patient info
DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")
ID_RE = re.compile(r"#(?P<id>\d+)")


class PDFProcessor:
    """Process PDF files containing medical progress notes"""
    
    def __init__(self):
        pass
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
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
    
    def extract_patient_info(self, pdf_path) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns: (patient_name, patient_id)
        """
        try:
            patient_name, patient_id = get_patient_from_pdf_headers(pdf_path)
            if patient_name and patient_id:
                return patient_name, patient_id
            return None, None
        
        except Exception as e:
            logger.error(f"Error extracting patient info: {str(e)}")
            return None, None
    
    def extract_metadata_from_text(self, text: str, pdf_path: str) -> Dict[str, str]:
        """Extract metadata from PDF text content using regex patterns"""
        # Initialize with filename as document_id
        metadata = {
            "document_id": Path(pdf_path).stem,
            "date_of_service": None,
            "provider": None,
            "patient_name": None,
            "patient_id": None
        }
        
        # Extract patient information from PDF file
        patient_name, patient_id = self.extract_patient_info(pdf_path)
        if patient_name:
            metadata["patient_name"] = patient_name
        if patient_id:
            metadata["patient_id"] = patient_id
        
        # Fallback: Extract patient info directly from text if not found in headers
        if not metadata["patient_name"] or not metadata["patient_id"]:
            # Pattern for "LastName, FirstName MM/DD/YYYY #ID" at the beginning of document
            patient_pattern = r'([A-Z][a-z]+,\s+[A-Z][a-z]+(?:\s+[A-Z])?)\s+\d{2}\/\d{2}\/\d{4}\s+#(\d+)'
            patient_match = re.search(patient_pattern, text)
            if patient_match:
                if not metadata["patient_name"]:
                    metadata["patient_name"] = patient_match.group(1).strip()
                if not metadata["patient_id"]:
                    metadata["patient_id"] = patient_match.group(2).strip()
        
        # Alternative pattern for patient name in "PATIENT NAME:" section
        if not metadata["patient_name"]:
            patient_name_pattern = r'PATIENT\s+NAME:\s*([A-Z][a-z]+,\s+[A-Z][a-z]+(?:\s+[A-Z])?)'
            patient_name_match = re.search(patient_name_pattern, text, re.IGNORECASE | re.MULTILINE)
            if patient_name_match:
                metadata["patient_name"] = patient_name_match.group(1).strip()
        
        # Pattern for patient ID with # symbol
        if not metadata["patient_id"]:
            patient_id_pattern = r'#(\d+)'
            patient_id_matches = re.findall(patient_id_pattern, text)
            if patient_id_matches:
                # Take the first patient ID found
                metadata["patient_id"] = patient_id_matches[0]
        
        # Extract Date of Service
        # Primary pattern for "DATE OF SERVICE:" followed by date (handles newlines)
        date_pattern = r'DATE\s+OF\s+SERVICE:[\s\n]*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
        date_match = re.search(date_pattern, text, re.IGNORECASE | re.MULTILINE)
        if date_match:
            metadata["date_of_service"] = date_match.group(1).strip()
        
        # Pattern for "DOS:" (Date of Service abbreviation)
        if not metadata["date_of_service"]:
            dos_pattern = r'DOS:\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})'
            dos_match = re.search(dos_pattern, text, re.IGNORECASE)
            if dos_match:
                metadata["date_of_service"] = dos_match.group(1).strip()
        
        # Alternative pattern for "DATE:" followed by date
        if not metadata["date_of_service"]:
            alt_date_pattern = r'DATE:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
            alt_date_match = re.search(alt_date_pattern, text, re.IGNORECASE)
            if alt_date_match:
                metadata["date_of_service"] = alt_date_match.group(1).strip()
        
        # Fallback: Find any date in various formats
        if not metadata["date_of_service"]:
            # First try month name format
            general_date_pattern = r'([A-Za-z]+\s+\d{1,2},\s+\d{4})'
            general_date_matches = re.findall(general_date_pattern, text)
            if general_date_matches:
                # Take the first date found that looks like a service date
                metadata["date_of_service"] = general_date_matches[0].strip()
            else:
                # Try numeric date format as last resort
                numeric_date_pattern = r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
                numeric_date_matches = re.findall(numeric_date_pattern, text)
                if numeric_date_matches:
                    # Filter out dates that look like birth dates (older dates)
                    # and take the most recent looking date
                    recent_dates = [d for d in numeric_date_matches if '2024' in d or '2025' in d]
                    if recent_dates:
                        metadata["date_of_service"] = recent_dates[0].strip()
                    elif numeric_date_matches:
                        metadata["date_of_service"] = numeric_date_matches[0].strip()
        
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
        
        # Pattern for provider name followed by credentials (DPM, MD, etc.) at end of document
        if not metadata["provider"]:
            provider_credential_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*,?\s+(?:MD|DPM|DO|PA-C|NP))'
            provider_credential_matches = re.findall(provider_credential_pattern, text)
            if provider_credential_matches:
                # Take the last match as it's likely the signing provider
                metadata["provider"] = provider_credential_matches[-1].strip()
        
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
            logger.warning(f"Could not extract date of service from text for {pdf_path}")
        
        # If provider not found, use placeholder
        if not metadata["provider"]:
            metadata["provider"] = "Unknown Provider"
            logger.warning(f"Could not extract provider from text for {pdf_path}")
        
        # If patient_name not found, use placeholder
        if not metadata["patient_name"]:
            metadata["patient_name"] = "Unknown Patient"
            logger.warning(f"Could not extract patient name from text for {pdf_path}")
        
        # If patient_id not found, use placeholder
        if not metadata["patient_id"]:
            metadata["patient_id"] = "0000"
            logger.warning(f"Could not extract patient ID from text for {pdf_path}")

        if not metadata["date_of_service"] or metadata["date_of_service"] == "2024-01-01" or not metadata["provider"] or not metadata["patient_name"] or not metadata["patient_id"]:
            logger.warning(f"Missing metadata in {pdf_path}: {metadata}")
            logger.debug(f"Text preview for debugging: {text[:500]}...")
        
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
                text=text,
                patient_name=metadata.get("patient_name"),
                patient_id=metadata.get("patient_id")
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
    processor = PDFProcessor()
    return processor.process_sample_pdfs(sample_dir, limit)
