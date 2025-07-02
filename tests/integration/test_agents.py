import os
import glob

import pytest
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from subagents.em_enhancement_agent import main as run_enhancement
from subagents.em_auditor_agent import main as run_auditor
from settings import logger


# Ruta a tus samples
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "samples")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Usa Azure Form Recognizer para extraer todo el texto de un PDF."""
    endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
    key      = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
    client   = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

    poller = client.begin_analyze_document("prebuilt-document", pdf_path)
    result = poller.result()

    # Concatenar párrafos
    full_text = "\n".join([p.content for page in result.pages for p in page.lines])
    return full_text

@pytest.mark.integration
def test_enhancement_and_audit_pipeline():
    # Selecciona 10 PDFs aleatorios o los primeros 10
    sample_files = glob.glob(os.path.join(SAMPLES_DIR, "*.pdf"))[:10]
    assert len(sample_files) == 10, "Necesitas al menos 10 PDFs en data/samples/"

    for pdf in sample_files:
        # 1) Extrae texto y metadatos (date/provider fijos o extraídos aquí)
        text = extract_text_from_pdf(pdf)
        payload = {
            "document_id": os.path.basename(pdf).replace(".pdf",""),
            "date_of_service": "2025-06-20",  # o parsea de filename si lo incluyes ahí
            "provider": "Dr. Ejemplo",
            "text": text
        }

        # 2) Llama al agente Stage D
        enh_out = run_enhancement(payload)
        assert enh_out["document_id"] == payload["document_id"]
        assert enh_out["code"] in {"99212","99213","99214","99215"}
        assert "History" in enh_out["justifications"]

        # 3) Llama al agente Stage E usando la salida anterior
        audit_input = {
            "document_id": enh_out["document_id"],
            "code": enh_out["code"],
            "justifications": enh_out["justifications"]
        }
        audit_out = run_auditor(audit_input)
        assert audit_out["document_id"] == payload["document_id"]
        assert isinstance(audit_out["audit_flags"], list)
        assert "final_note" in audit_out and len(audit_out["final_note"]) > 0

        # 4) (Opcional) imprime resumen rapido
        logger.info(f"{payload['document_id']}: {enh_out['code']} → flags: {audit_out['audit_flags']}")
