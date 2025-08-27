"""
Quick Test Script for E/M Coding Agents

This script tests the enhanced confidence scoring system with two different scenarios:

SCENARIO 1: High-quality documentation (payload)
- Comprehensive medical progress note
- Complete history, physical exam, assessment & plan
- Clear time documentation
- Expected: High confidence score (80-95%), minimal audit flags

SCENARIO 2: Poor-quality documentation (payload_with_flags) 
- Vague and incomplete documentation
- Missing critical details
- Unclear medical decision making
- Expected: Low confidence score (30-60%), multiple audit flags

To switch between scenarios, follow the instructions in the test_quick() function.
"""
import asyncio
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from utils.pdf_processor import PDFProcessor
from utils.html_processor import parse_payload_to_eminput
from agents.models.pydantic_models import EMInput, get_em_enhancement_agent, get_em_auditor_agent
from settings import logger

# Load environment variables
load_dotenv()


async def test_quick():
    """Quick test"""
    logger.debug("Starting Quick E/M Coding Test")
    
    # Initialize PDF processor
    #logger.debug("📁 Initializing PDF processor...")
    #pdf_processor = PDFProcessor()
    
    # Get sample directory
    #sample_dir = Path("data/samples")
    # sample_dir = Path("data/500_data")
    #if not sample_dir.exists():
    #    logger.error(f"❌ Sample directory not found: {sample_dir}")
    #    return
    
    # Create completed directory if it doesn't exist
    #completed_dir = Path("data/completed")
    #completed_dir.mkdir(exist_ok=True)
    #logger.debug(f"📁 Completed directory ready: {completed_dir}")
    
    # Process only 10 PDFs for quick test
    #logger.debug("📄 Processing sample PDFs...")
    # em_inputs = pdf_processor.process_sample_pdfs(str(sample_dir), limit=5)
    # em_inputs = pdf_processor.process_sample_pdfs(str(sample_dir), limit=3)
    
    # TEST PAYLOAD 1: Comprehensive documentation (High confidence, minimal flags)
    # This payload contains well-documented medical progress note with:
    # - Complete history and physical examination
    # - Clear assessment and plan
    # - Proper time documentation
    # - Expected result: High confidence score (80-95%), few or no audit flags
    # payload  = {
    #     "document": {
    #         "id": f"FDE075FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    #         "title": "Progress Note - Dr. Smith",
    #         "patientName": "Johnson, Robert",
    #         "PatientId": "1EB3B84E-D185-4155-84B8-BA439D1A8380",
    #         "provider": "Dr. Michael Smith",
    #         "DateOfService": "2025-01-15 10:30:00.000",
    #         "CreatedBy": "Dr. Michael Smith",
    #         "creationDate": "2025-01-15 11:45:13.370",
    #         "fileType": "text",
    #         "fileContent": {
    #         "encoding": "text",
    #         "data": "<div>\n    <div style='padding: 40px 0px; font-weight: bold; font-size: 15px; font-family: Arial, Helvetica, sans-serif;'>\n        <div style=\"text-align: center\">CONFIDENTIAL</div>\n        <div style=\"text-align: center\">MEDICAL/PROGRESS REPORT</div>\n\n        <table style=\"width: 100%\">\n            <tr>\n                <td style=\"width: 180px\">PATIENT NAME: </td>\n                <td>Johnson, Robert #123456789</td>\n            </tr>\n            <tr><td>&nbsp;</td></tr>\n            <tr>\n                <td>DATE OF BIRTH: </td>\n                <td>March 15, 1965</td>\n            </tr>\n            <tr><td>&nbsp;</td></tr>\n            <tr>\n                <td>DATE OF SERVICE: </td>\n                <td>January 15, 2025</td>\n            </tr>\n        </table>\n    </div>\n\n    <div style='font-family: Arial, Helvetica, sans-serif;' class=\"dictation-content\">\n        <p class=\"single-spacing\"><strong>CHIEF COMPLAINT:</strong></p>\n<p>Follow-up for hypertension and diabetes mellitus type 2. Patient reports worsening fatigue and occasional chest discomfort.</p>\n\n<p class=\"single-spacing\"><strong>HISTORY OF PRESENT ILLNESS:</strong></p>\n<p>59-year-old male with established hypertension and diabetes presents for routine follow-up. Over the past 2 weeks, patient reports increased fatigue, especially in the afternoons. Blood pressure readings at home have been elevated, ranging from 150-160/90-95. Blood sugars have been running higher than usual, 180-220 fasting. Patient admits to dietary indiscretions during the holidays. Reports occasional chest tightness with exertion, lasting 2-3 minutes, resolving with rest. No shortness of breath, palpitations, or diaphoresis. Current medications include metformin 1000mg BID, lisinopril 10mg daily, and atorvastatin 40mg daily. Patient has been compliant with medications.</p>\n\n<p class=\"single-spacing\"><strong>PAST MEDICAL HISTORY:</strong></p>\n<p>1. Hypertension - diagnosed 2018<br/>2. Type 2 diabetes mellitus - diagnosed 2020<br/>3. Hyperlipidemia - diagnosed 2019<br/>4. No prior hospitalizations</p>\n\n<p class=\"single-spacing\"><strong>MEDICATIONS:</strong></p>\n<p>1. Metformin 1000mg twice daily<br/>2. Lisinopril 10mg daily<br/>3. Atorvastatin 40mg daily</p>\n\n<p class=\"single-spacing\"><strong>ALLERGIES:</strong></p>\n<p>Penicillin - rash</p>\n\n<p class=\"single-spacing\"><strong>SOCIAL HISTORY:</strong></p>\n<p>Former smoker, quit 5 years ago. Occasional alcohol use. Works as accountant, sedentary lifestyle.</p>\n\n<p class=\"single-spacing\"><strong>PHYSICAL EXAMINATION:</strong></p>\n<p><strong>Vital Signs:</strong> BP 156/92, HR 78, RR 16, O2 sat 98% on room air, Weight 210 lbs, BMI 30.1</p>\n<p><strong>General:</strong> Well-appearing male in no acute distress</p>\n<p><strong>HEENT:</strong> Pupils equal, round, reactive to light. No fundoscopic abnormalities noted.</p>\n<p><strong>Cardiovascular:</strong> Regular rate and rhythm, no murmurs, rubs, or gallops. No peripheral edema.</p>\n<p><strong>Respiratory:</strong> Lungs clear to auscultation bilaterally, no wheezes or rales.</p>\n<p><strong>Abdomen:</strong> Soft, non-tender, no organomegaly.</p>\n<p><strong>Extremities:</strong> No pedal edema, pedal pulses intact bilaterally.</p>\n\n<p class=\"single-spacing\"><strong>ASSESSMENT AND PLAN:</strong></p>\n<p><strong>1. Hypertension - uncontrolled</strong><br/>\n- Current home readings elevated despite medication<br/>\n- Increase lisinopril to 20mg daily<br/>\n- Patient counseled on low sodium diet<br/>\n- Recheck BP in 2 weeks</p>\n\n<p><strong>2. Type 2 diabetes mellitus - poorly controlled</strong><br/>\n- HbA1c elevated, fasting glucose >180<br/>\n- Increase metformin to 1500mg BID<br/>\n- Referred to nutritionist for dietary counseling<br/>\n- Recheck HbA1c in 3 months</p>\n\n<p><strong>3. Chest discomfort - atypical chest pain</strong><br/>\n- Symptoms concerning for possible cardiac etiology<br/>\n- Ordered stress test and EKG<br/>\n- Patient advised to seek immediate care if symptoms worsen<br/>\n- Consider cardiology referral pending stress test results</p>\n\n<p><strong>4. Hyperlipidemia</strong><br/>\n- Continue atorvastatin 40mg daily<br/>\n- Recheck lipid panel in 3 months</p>\n\n<p class=\"single-spacing\"><strong>PATIENT EDUCATION:</strong></p>\n<p>Discussed importance of medication compliance, dietary modifications, and regular exercise. Patient understands need for close follow-up given uncontrolled diabetes and hypertension.</p>\n\n<p class=\"single-spacing\"><strong>TIME:</strong></p>\n<p>Total time spent with patient: 35 minutes, with more than half spent in counseling and coordination of care.</p>\n\n<p>&nbsp;</p><br/><br/><p>This dictation was prepared using Dragon Medical voice recognition software.  As a result, errors may occur.  When identified, these errors have been corrected.  While every attempt is made to correct errors during dictation, errors may still exist.</p>\n    </div>\n\n    <style>\n        .dictation-content strong{\n            font-size: 16px;\n            margin-right: 5px;\n        }\n    </style>\n</div>"
    #         }
    #     }
    # }
    
    # TEST PAYLOAD 2: Problematic documentation (Low confidence, multiple flags)
    # This payload contains poorly documented medical progress note with:
    # - Vague and incomplete history
    # - Missing specific medication details
    # - Incomplete physical examination
    # - No time documentation
    # - Unclear medical decision making
    # - Expected result: Low confidence score (30-60%), multiple audit flags
    # To use this payload: comment out the current payload above and uncomment this one
    # Alternative payload for testing audit flags (uncomment to test problematic documentation)
    payload = {
        "document": {
            "id": f"AUDIT_FLAGS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "Progress Note - Dr. Johnson",
            "patientName": "Williams, Sarah",
            "PatientId": "2FB4C95F-E296-4266-95C9-CB549E2B9491",
            "provider": "Dr. Jennifer Johnson",
            "DateOfService": "2025-01-20 14:15:00.000",
            "CreatedBy": "Dr. Jennifer Johnson",
            "creationDate": "2025-01-20 15:30:45.120",
            "fileType": "text",
            "fileContent": {
                "encoding": "text",
                "data": "<div>\n    <div style='padding: 40px 0px; font-weight: bold; font-size: 15px; font-family: Arial, Helvetica, sans-serif;'>\n        <div style=\"text-align: center\">CONFIDENTIAL</div>\n        <div style=\"text-align: center\">MEDICAL/PROGRESS REPORT</div>\n\n        <table style=\"width: 100%\">\n            <tr>\n                <td style=\"width: 180px\">PATIENT NAME: </td>\n                <td>Williams, Sarah #987654321</td>\n            </tr>\n            <tr><td>&nbsp;</td></tr>\n            <tr>\n                <td>DATE OF BIRTH: </td>\n                <td>June 8, 1980</td>\n            </tr>\n            <tr><td>&nbsp;</td></tr>\n            <tr>\n                <td>DATE OF SERVICE: </td>\n                <td>January 20, 2025</td>\n            </tr>\n        </table>\n    </div>\n\n    <div style='font-family: Arial, Helvetica, sans-serif;' class=\"dictation-content\">\n        <p class=\"single-spacing\"><strong>CHIEF COMPLAINT:</strong></p>\n<p>Patient here for follow-up. Some issues with medications.</p>\n\n<p class=\"single-spacing\"><strong>HISTORY OF PRESENT ILLNESS:</strong></p>\n<p>Patient is doing okay. Has some complaints. Taking medications most of the time. Blood pressure seems fine. Sugar levels variable. Had some tests done recently but results not available yet. Patient reports feeling tired sometimes. No major complaints today.</p>\n\n<p class=\"single-spacing\"><strong>PAST MEDICAL HISTORY:</strong></p>\n<p>Diabetes and high blood pressure. Maybe some other things.</p>\n\n<p class=\"single-spacing\"><strong>MEDICATIONS:</strong></p>\n<p>Patient takes several medications. Details not available at this time.</p>\n\n<p class=\"single-spacing\"><strong>ALLERGIES:</strong></p>\n<p>Patient mentions something about allergies but not sure what exactly.</p>\n\n<p class=\"single-spacing\"><strong>SOCIAL HISTORY:</strong></p>\n<p>Occasional smoker. Social drinking.</p>\n\n<p class=\"single-spacing\"><strong>PHYSICAL EXAMINATION:</strong></p>\n<p><strong>Vital Signs:</strong> BP elevated, other vitals stable</p>\n<p><strong>General:</strong> Patient appears well</p>\n<p><strong>Other systems:</strong> Examination largely normal</p>\n\n<p class=\"single-spacing\"><strong>ASSESSMENT:</strong></p>\n<p>1. Diabetes - continue management<br/>\n2. Hypertension - adjust as needed<br/>\n3. Patient education provided</p>\n\n<p class=\"single-spacing\"><strong>PLAN:</strong></p>\n<p>Continue current medications. Follow up as needed. Patient to call if problems. Will review test results when available.</p>\n\n<p>&nbsp;</p><br/><br/><p>This dictation was prepared using Dragon Medical voice recognition software.  As a result, errors may occur.  When identified, these errors have been corrected.  While every attempt is made to correct errors during dictation, errors may still exist.</p>\n    </div>\n\n    <style>\n        .dictation-content strong{\n            font-size: 16px;\n            margin-right: 5px;\n        }\n    </style>\n</div>"
            }
        }
    }

    em_inputs: List[EMInput] = []
    em_input = parse_payload_to_eminput(payload)
    em_inputs.append(em_input)
    if not em_inputs:
        logger.error("❌ No PDFs were successfully processed")
        return
    
    logger.debug(f"📊 Processing {len(em_inputs)} documents through agents...")
    
    # Start timing the processing
    start_time = time.time()
    
    # Process all available documents
    all_results = []
    
    for i, em_input in enumerate(em_inputs, 1):
        logger.debug(f"Processing document {i}/{len(em_inputs)}: {em_input.document_id}")
        logger.debug(f"👤 Patient: {em_input.patient_name} (ID: {em_input.patient_id})")
        logger.debug(f"📅 Date of Service: {em_input.date_of_service}")
        logger.debug(f"🏥 Provider: {em_input.provider}")
        logger.debug(f"📝 Text preview (first 300 chars): {em_input.text[:300]}...")
        
        try:
            # Stage 1: Enhancement Agent
            logger.debug("🤖 Running Enhancement Agent...")
            
            enhancement_prompt = f"""
            Document ID: {em_input.document_id}
            Patient Name: {em_input.patient_name}
            Patient ID: {em_input.patient_id}
            Date of Service: {em_input.date_of_service}
            Provider: {em_input.provider}
            
            Progress Note:
            {em_input.text}
            
            Please analyze this progress note and assign the most appropriate E/M code with justifications.
            """
            
            logger.debug("🧠 Enhancement Agent: Processing...")
            enhancement_agent = get_em_enhancement_agent()
            enhancement_result = await enhancement_agent.run(enhancement_prompt)
            
            logger.debug("✅ Enhancement Agent completed!")
            logger.debug(f"🎯 Assigned Code: {enhancement_result.output.assigned_code}")
            logger.debug(f"📋 Justification: {enhancement_result.output.justification[:100]}...")
            
            logger.debug("📊 Code Recommendations:")
            logger.debug(f"  • 99212: {enhancement_result.output.code_recommendations.code_99212[:50]}...")
            logger.debug(f"  • 99213: {enhancement_result.output.code_recommendations.code_99213[:50]}...")
            logger.debug(f"  • 99214: {enhancement_result.output.code_recommendations.code_99214[:50]}...")
            logger.debug(f"  • 99215: {enhancement_result.output.code_recommendations.code_99215[:50]}...")
            
            # Stage 2: Auditor Agent
            logger.debug("\n🕵️ Running Auditor Agent...")
            
            auditor_prompt = f"""
            Patient Information:
            - Patient Name: {em_input.patient_name}
            - Patient ID: {em_input.patient_id}
            - Date of Service: {em_input.date_of_service}
            - Provider: {em_input.provider}
            
            Original Progress Note:
            {em_input.text}
            
            Enhancement Agent Results:
            - Assigned Code: {enhancement_result.output.assigned_code}
            - Justification: {enhancement_result.output.justification}
            - Code Recommendations:
              * 99212: {enhancement_result.output.code_recommendations.code_99212}
              * 99213: {enhancement_result.output.code_recommendations.code_99213}
              * 99214: {enhancement_result.output.code_recommendations.code_99214}
              * 99215: {enhancement_result.output.code_recommendations.code_99215}
            
            Please audit this analysis for compliance and provide final recommendations.
            """
            
            # logger.debug("🧠 Auditor Agent: Processing...")
            auditor_agent = get_em_auditor_agent()
            auditor_result = await auditor_agent.run(auditor_prompt)
            
            logger.debug("✅ Auditor Agent completed!")
            logger.debug(f"🎯 Final Code: {auditor_result.output.final_assigned_code}")
            logger.debug(f"🚨 Audit Flags: {len(auditor_result.output.audit_flags)} flags")
            logger.debug(f"📝 Final Justification Summary: {auditor_result.output.final_justification.supportedBy}")
            logger.debug(f"📋 Documentation Points: {len(auditor_result.output.final_justification.documentationSummary)}")
            logger.debug(f"⚠️  Compliance Alerts: {len(auditor_result.output.final_justification.complianceAlerts or [])}")
            
            # Create JSON output for this document
            document_result = {
                "document_id": em_input.document_id,
                "patient_name": em_input.patient_name,
                "patient_id": em_input.patient_id,
                "date_of_service": em_input.date_of_service,
                "provider": em_input.provider,
                "original_text_length": len(em_input.text),
                "original_text_preview": em_input.text,
                "enhancement_agent": {
                    "assigned_code": enhancement_result.output.assigned_code,
                    "justification": enhancement_result.output.justification,
                    "code_recommendations": {
                        "code_99212": enhancement_result.output.code_recommendations.code_99212,
                        "code_99213": enhancement_result.output.code_recommendations.code_99213,
                        "code_99214": enhancement_result.output.code_recommendations.code_99214,
                        "code_99215": enhancement_result.output.code_recommendations.code_99215,
                    }
                },
                "auditor_agent": {
                    "final_assigned_code": auditor_result.output.final_assigned_code,
                    "final_justification": auditor_result.output.final_justification.model_dump(),
                    "audit_flags": auditor_result.output.audit_flags,
                    "billing_ready_note": auditor_result.output.billing_ready_note,
                    "confidence": auditor_result.output.confidence.model_dump(),
                    "code_evaluations": {
                        "code_99212_evaluation": auditor_result.output.code_evaluations.code_99212_evaluation.model_dump(),
                        "code_99213_evaluation": auditor_result.output.code_evaluations.code_99213_evaluation.model_dump(),
                        "code_99214_evaluation": auditor_result.output.code_evaluations.code_99214_evaluation.model_dump(),
                        "code_99215_evaluation": auditor_result.output.code_evaluations.code_99215_evaluation.model_dump(),
                    }
                },
                "timestamp": datetime.now().isoformat(),
                "processing_metadata": {
                    "enhancement_agent_model": "Azure OpenAI GPT-5 (embedded guidelines)",
                    "auditor_agent_model": "Azure OpenAI GPT-5 (embedded guidelines)",
                    "processing_time": datetime.now().isoformat(),
                    "guidelines_method": "embedded_in_prompt",
                    "tools_used": False
                }
            }
            
            # Save individual document result
            output_filename = f"result_{em_input.document_id}.json"
            with open(f'test_results/{output_filename}', "w", encoding="utf-8") as f:
                json.dump(document_result, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Document result saved to: {output_filename}")
            
            # Move processed file to completed directory
            # if em_input.document_id and Path(f"data/samples/{em_input.document_id}.pdf").exists():
            #     try:
            #         source_file = Path(f"data/samples/{em_input.document_id}.pdf")
            #         destination_file = completed_dir / source_file.name
            #         if destination_file.exists():
            #             stem = destination_file.stem
            #             suffix = destination_file.suffix
            #             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            #             destination_file = completed_dir / f"{stem}_{timestamp}{suffix}"
                    
            #         shutil.move(str(source_file), str(destination_file))
            #         logger.debug(f"📁 File moved to: {destination_file}")
            #     except Exception as move_error:
            #         logger.warning(f"⚠️ Could not move file {em_input.document_id}: {str(move_error)}")
            # else:
            #     logger.debug(f"📄 No file path available for {em_input.document_id}, skipping file move")
            
            all_results.append(document_result)
            logger.debug(f"✅ Document {i}/{len(em_inputs)} completed successfully!")
            logger.debug("-" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error processing document {em_input.document_id}: {str(e)}")
            import traceback
            logger.error(f"� Traceback: {traceback.format_exc()}")
            
            # Add error result
            error_result = {
                "document_id": em_input.document_id,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            all_results.append(error_result)
    
    # Calculate processing time
    end_time = time.time()
    total_processing_time = end_time - start_time
    avg_time_per_document = total_processing_time / len(em_inputs)
    
    logger.debug(f"Total processing time: {total_processing_time:.2f} seconds")
    logger.debug(f"Average time per document: {avg_time_per_document:.2f} seconds")
    
    # Save consolidated results
    consolidated_filename = f"test_results_consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    consolidated_result = {
        "test_summary": {
            "total_documents": len(em_inputs),
            "successful_documents": len([r for r in all_results if "error" not in r]),
            "failed_documents": len([r for r in all_results if "error" in r]),
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "test_sequential_embedded_guidelines",
            "total_processing_time_seconds": total_processing_time,
            "average_time_per_document": avg_time_per_document
        },
        "results": all_results
    }
    
    with open(f'test_results/{consolidated_filename}', "w", encoding="utf-8") as f:
        json.dump(consolidated_result, f, indent=2, ensure_ascii=False)
    
    logger.debug(f"💾 Consolidated results saved to: {consolidated_filename}")
    
    # Print summary
    logger.debug("\n" + "="*80)
    logger.debug("📊 TEST SUMMARY")
    logger.debug("="*80)
    logger.debug(f"✅ Total documents processed: {len(em_inputs)}")
    logger.debug(f"✅ Successful: {consolidated_result['test_summary']['successful_documents']}")
    logger.debug(f"❌ Failed: {consolidated_result['test_summary']['failed_documents']}")
    logger.debug(f"⚡ Total processing time: {total_processing_time:.2f} seconds")
    logger.debug(f"📊 Average time per document: {avg_time_per_document:.2f} seconds")
    
    # Show sample result structure
    if all_results and "error" not in all_results[0]:
        logger.debug("\n📄 SAMPLE RESULT STRUCTURE:")
        logger.debug("=" * 80)
        sample_result = all_results[0].copy()
        # Truncate long fields for display
        if "original_text_preview" in sample_result:
            sample_result["original_text_preview"] = sample_result["original_text_preview"]
        for agent in ["enhancement_agent", "auditor_agent"]:
            if agent in sample_result:
                if "justification" in sample_result[agent]:
                    sample_result[agent]["justification"] = sample_result[agent]["justification"]
                if "final_justification" in sample_result[agent]:
                    # final_justification is now an object, keep as is for structure display
                    pass
                if "billing_ready_note" in sample_result[agent]:
                    sample_result[agent]["billing_ready_note"] = sample_result[agent]["billing_ready_note"]
                if "code_recommendations" in sample_result[agent]:
                    for code in sample_result[agent]["code_recommendations"]:
                        sample_result[agent]["code_recommendations"][code] = sample_result[agent]["code_recommendations"][code]
                if "code_evaluations" in sample_result[agent]:
                    # code_evaluations are now objects, keep as is for structure display
                    pass
        
        logger.debug(json.dumps(sample_result, indent=2, ensure_ascii=False))
        logger.debug("=" * 80)
    
    logger.debug("Test completed successfully!")


def main():
    """Main entry point"""
    try:
        asyncio.run(test_quick())
    except KeyboardInterrupt:
        logger.error("⏹️ Test interrupted by user")
    except Exception as e:
        logger.error(f"💥 Test failed with error: {str(e)}")


if __name__ == "__main__":
    main()
