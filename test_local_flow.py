"""
Local Diagnostic Script for Durable Functions

This script tests the individual components locally to identify where the issue is
before deploying to Azure.
"""

import asyncio
import json
from datetime import datetime
from utils.html_processor import parse_payload_to_eminput
from models.pydantic_models import EMInput, em_enhancement_agent, em_auditor_agent


def create_test_payload():
    """Create a test payload"""
    return {
        "document": {
            "id": f"LOCAL_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "Progress Note - Local Test",
            "patientName": "Test, Patient",
            "PatientId": "LOCAL-TEST-123",
            "provider": "Dr. Local Test",
            "DateOfService": "2025-01-20 14:15:00.000",
            "CreatedBy": "Dr. Local Test",
            "creationDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "fileType": "text",
            "fileContent": {
                "encoding": "text",
                "data": """<div>
    <div style='padding: 40px 0px; font-weight: bold; font-size: 15px; font-family: Arial, Helvetica, sans-serif;'>
        <div style="text-align: center">CONFIDENTIAL</div>
        <div style="text-align: center">MEDICAL/PROGRESS REPORT</div>
        <table style="width: 100%">
            <tr><td style="width: 180px">PATIENT NAME: </td><td>Test, Patient #123</td></tr>
            <tr><td>DATE OF SERVICE: </td><td>January 20, 2025</td></tr>
        </table>
    </div>
    <div style='font-family: Arial, Helvetica, sans-serif;' class="dictation-content">
        <p><strong>CHIEF COMPLAINT:</strong></p>
        <p>Patient here for follow-up. Some issues with medications.</p>
        <p><strong>ASSESSMENT:</strong></p>
        <p>1. Diabetes - continue management</p>
        <p><strong>PLAN:</strong></p>
        <p>Continue current medications. Follow up as needed.</p>
    </div>
</div>"""
            }
        }
    }


async def test_html_parsing():
    """Test HTML parsing function"""
    print("🔧 Testing HTML parsing...")
    
    try:
        payload = create_test_payload()
        em_input = parse_payload_to_eminput(payload)
        
        print(f"✅ HTML parsing successful!")
        print(f"📄 Document ID: {em_input.document_id}")
        print(f"👤 Patient: {em_input.patient_name}")
        print(f"📝 Text length: {len(em_input.text)} characters")
        print(f"📋 Text preview: {em_input.text[:200]}...")
        
        return em_input
        
    except Exception as e:
        print(f"❌ HTML parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_enhancement_agent(em_input: EMInput):
    """Test enhancement agent"""
    print("\n🤖 Testing Enhancement Agent...")
    
    try:
        # Create enhancement prompt like in the activity
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
        
        print(f"📤 Running enhancement agent...")
        enhancement_result = await em_enhancement_agent.run(enhancement_prompt)
        
        print(f"✅ Enhancement agent successful!")
        print(f"🎯 Assigned Code: {enhancement_result.output.assigned_code}")
        print(f"📝 Justification: {enhancement_result.output.justification[:100]}...")
        
        # Create the data structure that would be passed to auditor
        enhancement_data = {
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
            "timestamp": datetime.now().isoformat()
        }
        
        return enhancement_data
        
    except Exception as e:
        print(f"❌ Enhancement agent failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_auditor_agent(enhancement_data: dict):
    """Test auditor agent"""
    print("\n🕵️ Testing Auditor Agent...")
    
    try:
        # Create auditor prompt like in the activity
        enhancement_agent_data = enhancement_data.get('enhancement_agent', {})
        
        auditor_prompt = f"""
        Patient Information:
        - Patient Name: {enhancement_data.get('patient_name')}
        - Patient ID: {enhancement_data.get('patient_id')}
        - Date of Service: {enhancement_data.get('date_of_service')}
        - Provider: {enhancement_data.get('provider')}
        
        Original Progress Note:
        {enhancement_data.get('original_text_preview', '')}
        
        Enhancement Agent Results:
        - Assigned Code: {enhancement_agent_data.get('assigned_code')}
        - Justification: {enhancement_agent_data.get('justification')}
        - Code Recommendations:
          * 99212: {enhancement_agent_data.get('code_recommendations', {}).get('code_99212', '')}
          * 99213: {enhancement_agent_data.get('code_recommendations', {}).get('code_99213', '')}
          * 99214: {enhancement_agent_data.get('code_recommendations', {}).get('code_99214', '')}
          * 99215: {enhancement_agent_data.get('code_recommendations', {}).get('code_99215', '')}
        
        Please audit this analysis for compliance and provide final recommendations.
        """
        
        print(f"📤 Running auditor agent...")
        auditor_result = await em_auditor_agent.run(auditor_prompt)
        
        print(f"✅ Auditor agent successful!")
        print(f"🎯 Final Code: {auditor_result.output.final_assigned_code}")
        print(f"🚨 Audit Flags: {len(auditor_result.output.audit_flags)} flags")
        print(f"📊 Confidence Score: {auditor_result.output.confidence.overall_score}")
        
        # Create final result structure
        final_result = {
            "document_id": enhancement_data.get('document_id'),
            "patient_name": enhancement_data.get('patient_name'),
            "patient_id": enhancement_data.get('patient_id'),
            "date_of_service": enhancement_data.get('date_of_service'),
            "provider": enhancement_data.get('provider'),
            "original_text_length": enhancement_data.get('original_text_length'),
            "original_text_preview": enhancement_data.get('original_text_preview'),
            "enhancement_agent": enhancement_data.get('enhancement_agent'),
            "auditor_agent": {
                "final_assigned_code": auditor_result.output.final_assigned_code,
                "final_justification": auditor_result.output.final_justification,
                "audit_flags": auditor_result.output.audit_flags,
                "billing_ready_note": auditor_result.output.billing_ready_note,
                "confidence": auditor_result.output.confidence.model_dump(),
                "code_evaluations": {
                    "code_99212_evaluation": auditor_result.output.code_evaluations.code_99212_evaluation,
                    "code_99213_evaluation": auditor_result.output.code_evaluations.code_99213_evaluation,
                    "code_99214_evaluation": auditor_result.output.code_evaluations.code_99214_evaluation,
                    "code_99215_evaluation": auditor_result.output.code_evaluations.code_99215_evaluation,
                }
            },
            "timestamp": datetime.now().isoformat(),
            "processing_metadata": {
                "enhancement_agent_model": "Azure OpenAI GPT-4.1 (embedded guidelines)",
                "auditor_agent_model": "Azure OpenAI GPT-4.1 (embedded guidelines)",
                "processing_time": datetime.now().isoformat(),
                "guidelines_method": "embedded_in_prompt",
                "tools_used": False
            }
        }
        
        return final_result
        
    except Exception as e:
        print(f"❌ Auditor agent failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_full_local_flow():
    """Test the complete flow locally"""
    print("🧪 LOCAL DIAGNOSTIC TEST - E/M CODING FLOW")
    print("=" * 60)
    
    # Step 1: Test HTML parsing
    em_input = await test_html_parsing()
    if not em_input:
        print("❌ Cannot proceed - HTML parsing failed")
        return
    
    # Step 2: Test enhancement agent
    enhancement_data = await test_enhancement_agent(em_input)
    if not enhancement_data:
        print("❌ Cannot proceed - Enhancement agent failed")
        return
    
    # Step 3: Test auditor agent
    final_result = await test_auditor_agent(enhancement_data)
    if not final_result:
        print("❌ Cannot proceed - Auditor agent failed")
        return
    
    # Step 4: Create final report structure
    print("\n📊 Creating final report structure...")
    
    consolidated_result = {
        "test_summary": {
            "total_documents": 1,
            "successful_documents": 1,
            "failed_documents": 0,
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "local_diagnostic_test"
        },
        "results": [final_result]
    }
    
    # Save report
    filename = f"local_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(consolidated_result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Final report structure created!")
    print(f"💾 Report saved to: {filename}")
    print(f"\n🎉 All local tests passed! The issue might be in the Azure Functions runtime.")
    
    print(f"\n📋 SUMMARY:")
    print(f"✅ HTML parsing: OK")
    print(f"✅ Enhancement agent: OK")
    print(f"✅ Auditor agent: OK")
    print(f"✅ Report generation: OK")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Deploy the updated functions to Azure")
    print(f"2. Use test_azure_functions.py to test remotely")
    print(f"3. Check Azure Function logs if issues persist")


if __name__ == "__main__":
    asyncio.run(test_full_local_flow())
