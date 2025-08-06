import logging
import json
from http import HTTPStatus

import azure.functions as func
import azure.durable_functions as df



async def main(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    try:
        appointment_id = req.params.get("appointment_id")
        logging.info(f"Extracting data for ID: {appointment_id}")

        #HERE WILL BE THE LOGIC TO EXTRACT THE DATA FROM THE ID
        # For now, we will just simulate the data extraction

        input_data = {
        "transcription": "The patient is a 70-year-old male presenting with chronic left leg pain. Symptoms have persisted for years and have not improved with recent SI joint or caudal epidural injections. Pain starts in the lower back and radiates to the left buttock, thigh, and foot. There is no pain on the right side. Patient experiences increased discomfort with walking and sitting, relieved partially by leaning forward or support. Pain is rated 6/10. He has not participated in PT recently. Currently uses naproxen. No recent imaging reviewed, but prior surgery included L4-L5 TLIF and L3-L4 lateral fusion. The patient will retrieve his MRI for review. An EMG is recommended. Physical exam shows mild tenderness in the lumbar spine, no deformity, full ROM, intact motor and reflexes with minor discrepancies.",
        "patient_name": "Kaider, Eugene J",
        "patient_id": "146205",
        "patient_date_of_birth": "1954-07-18",
        "progress_note_type": "Ortho Follow-Up",
        "patient_data": """
        "Past Medical History": "Arthritis, Diabetes, Hypertension, Hyperlipidemia, History of cancer.",
        "Medications": "Metformin, Rosuvastatin, Norvasc, Hydrochlorothiazide, Naproxen.",
        "Allergies": "NKDA." """}


        instance_id = await client.start_new("em_progress_note_orchestrator", client_input=input_data)
        logging.info(f"Orchestration started from samples with ID: {instance_id}")

        return client.create_check_status_response(req, instance_id)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate progress note", "details": str(e)}),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/json"
        )
