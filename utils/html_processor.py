from models.pydantic_models import EMInput 
from bs4 import BeautifulSoup
from settings import logger


def parse_payload_to_eminput(payload: dict) -> EMInput:
    document = payload["document"]
    
    # Extract plain text from the HTML content
    html_content = document.get("fileContent", {}).get("data", "")
    soup = BeautifulSoup(html_content, "html.parser")
    readable_text = soup.get_text(separator="\n", strip=True)
    logger.debug(f"Extracted text: {readable_text[:100]}...")  # Log first 100 characters for debugging

    # Assemble EMInput object
    em_input = EMInput(
        document_id=document["id"],
        date_of_service=document["DateOfService"],
        provider=document["provider"],
        text=readable_text,
        patient_name=document.get("patientName"),
        patient_id=document.get("PatientId")
    )

    return em_input