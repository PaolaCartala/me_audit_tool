"""
Azure Durable Functions Diagnostic and Test Script

This script tests the E/M coding durable functions with detailed logging
and error handling to identify where the process gets stuck.
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any


class DurableFunctionsTester:
    def __init__(self, function_app_url: str):
        self.function_app_url = function_app_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Azure-Functions-Tester/1.0'
        })

    def create_test_payload(self, doc_type: str = "problematic") -> Dict[str, Any]:
        """Create test payload with different documentation quality levels"""
        
        if doc_type == "good":
            # High-quality documentation
            html_content = """<div>
    <div style='padding: 40px 0px; font-weight: bold; font-size: 15px; font-family: Arial, Helvetica, sans-serif;'>
        <div style="text-align: center">CONFIDENTIAL</div>
        <div style="text-align: center">MEDICAL/PROGRESS REPORT</div>
        <table style="width: 100%">
            <tr><td style="width: 180px">PATIENT NAME: </td><td>Johnson, Robert #123456789</td></tr>
            <tr><td>DATE OF BIRTH: </td><td>March 15, 1965</td></tr>
            <tr><td>DATE OF SERVICE: </td><td>January 15, 2025</td></tr>
        </table>
    </div>
    <div style='font-family: Arial, Helvetica, sans-serif;' class="dictation-content">
        <p><strong>CHIEF COMPLAINT:</strong></p>
        <p>Follow-up for hypertension and diabetes mellitus type 2. Patient reports worsening fatigue and occasional chest discomfort.</p>
        <p><strong>HISTORY OF PRESENT ILLNESS:</strong></p>
        <p>59-year-old male with established hypertension and diabetes presents for routine follow-up. Over the past 2 weeks, patient reports increased fatigue, especially in the afternoons. Blood pressure readings at home have been elevated, ranging from 150-160/90-95. Blood sugars have been running higher than usual, 180-220 fasting.</p>
        <p><strong>PHYSICAL EXAMINATION:</strong></p>
        <p><strong>Vital Signs:</strong> BP 156/92, HR 78, RR 16, O2 sat 98% on room air, Weight 210 lbs</p>
        <p><strong>General:</strong> Well-appearing male in no acute distress</p>
        <p><strong>Cardiovascular:</strong> Regular rate and rhythm, no murmurs, rubs, or gallops</p>
        <p><strong>ASSESSMENT AND PLAN:</strong></p>
        <p><strong>1. Hypertension - uncontrolled</strong><br/>- Increase lisinopril to 20mg daily<br/>- Recheck BP in 2 weeks</p>
        <p><strong>TIME:</strong></p>
        <p>Total time spent with patient: 35 minutes, with more than half spent in counseling.</p>
    </div>
</div>"""
        else:
            # Problematic documentation (should trigger audit flags)
            html_content = """<div>
    <div style='padding: 40px 0px; font-weight: bold; font-size: 15px; font-family: Arial, Helvetica, sans-serif;'>
        <div style="text-align: center">CONFIDENTIAL</div>
        <div style="text-align: center">MEDICAL/PROGRESS REPORT</div>
        <table style="width: 100%">
            <tr><td style="width: 180px">PATIENT NAME: </td><td>Williams, Sarah #987654321</td></tr>
            <tr><td>DATE OF BIRTH: </td><td>June 8, 1980</td></tr>
            <tr><td>DATE OF SERVICE: </td><td>January 20, 2025</td></tr>
        </table>
    </div>
    <div style='font-family: Arial, Helvetica, sans-serif;' class="dictation-content">
        <p><strong>CHIEF COMPLAINT:</strong></p>
        <p>Patient here for follow-up. Some issues with medications.</p>
        <p><strong>HISTORY OF PRESENT ILLNESS:</strong></p>
        <p>Patient is doing okay. Has some complaints. Taking medications most of the time.</p>
        <p><strong>PHYSICAL EXAMINATION:</strong></p>
        <p><strong>Vital Signs:</strong> BP elevated, other vitals stable</p>
        <p><strong>General:</strong> Patient appears well</p>
        <p><strong>ASSESSMENT:</strong></p>
        <p>1. Diabetes - continue management<br/>2. Hypertension - adjust as needed</p>
        <p><strong>PLAN:</strong></p>
        <p>Continue current medications. Follow up as needed.</p>
    </div>
</div>"""

        return {
            "document": {
                "id": f"TEST_{doc_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": f"Progress Note - Test {doc_type.title()} Documentation",
                "patientName": "Johnson, Robert" if doc_type == "good" else "Williams, Sarah",
                "PatientId": f"TEST-{doc_type.upper()}-{datetime.now().strftime('%H%M%S')}",
                "provider": "Dr. Test Provider",
                "DateOfService": "2025-01-20 14:15:00.000",
                "CreatedBy": "Dr. Test Provider",
                "creationDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "fileType": "text",
                "fileContent": {
                    "encoding": "text",
                    "data": html_content
                }
            }
        }

    def start_orchestration(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Start the durable function orchestration"""
        print("🚀 Starting orchestration...")
        start_url = f"{self.function_app_url}/api/orchestrations"
        
        print(f"📤 POST {start_url}")
        print(f"📄 Document ID: {payload['document']['id']}")
        print(f"👤 Patient: {payload['document']['patientName']}")
        
        try:
            response = self.session.post(start_url, json=payload, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")
            
            if response.status_code != 202:
                print(f"❌ Failed to start orchestration")
                print(f"📄 Response Text: {response.text}")
                return None
            
            response_data = response.json()
            print(f"✅ Orchestration started successfully!")
            print(f"🆔 Instance ID: {response_data.get('id')}")
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error starting orchestration: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"📄 Response text: {response.text}")
            return None

    def poll_orchestration_status(self, status_uri: str, max_wait_time: int = 600) -> Optional[Dict[str, Any]]:
        """Poll orchestration status until completion or timeout"""
        print(f"\n⏳ Polling orchestration status (max {max_wait_time} seconds)...")
        print(f"🔗 Status URI: {status_uri}")
        
        start_time = time.time()
        poll_count = 0
        last_status = None
        
        while True:
            poll_count += 1
            elapsed_time = time.time() - start_time
            
            try:
                print(f"\n📊 Poll #{poll_count} (elapsed: {elapsed_time:.1f}s)")
                status_response = self.session.get(status_uri, timeout=15)
                
                if status_response.status_code != 200:
                    print(f"⚠️ Status check returned {status_response.status_code}: {status_response.text}")
                    time.sleep(5)
                    continue
                
                status_data = status_response.json()
                runtime_status = status_data.get("runtimeStatus")
                
                # Only print status change
                if runtime_status != last_status:
                    print(f"📈 Status: {last_status} → {runtime_status}")
                    last_status = runtime_status
                    
                    # Print additional info for debugging
                    if "customStatus" in status_data:
                        print(f"📋 Custom Status: {status_data['customStatus']}")
                    
                    if "history" in status_data:
                        print(f"📚 History entries: {len(status_data['history'])}")
                        # Print last few history entries
                        for entry in status_data['history'][-3:]:
                            print(f"   📝 {entry.get('EventType', 'Unknown')}: {entry.get('Name', 'N/A')}")
                
                # Check terminal states
                if runtime_status == "Completed":
                    print(f"✅ Orchestration completed! (Total time: {elapsed_time:.1f}s)")
                    return status_data
                elif runtime_status in ["Failed", "Canceled", "Terminated"]:
                    print(f"❌ Orchestration failed with status: {runtime_status}")
                    print(f"📄 Full status data: {json.dumps(status_data, indent=2)}")
                    return status_data
                elif elapsed_time > max_wait_time:
                    print(f"⏰ Timeout: Orchestration did not complete within {max_wait_time} seconds")
                    print(f"📊 Final status: {runtime_status}")
                    print(f"📄 Final status data: {json.dumps(status_data, indent=2)}")
                    return None
                
                # Wait before next poll (progressive backoff)
                wait_time = min(10, 2 + poll_count * 0.5)
                time.sleep(wait_time)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error checking status: {e}")
                time.sleep(5)
                continue
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error in status: {e}")
                print(f"📄 Response text: {status_response.text}")
                time.sleep(5)
                continue

    def download_json_report(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Download the JSON report"""
        print(f"\n📥 Downloading JSON report for instance: {instance_id}")
        download_url = f"{self.function_app_url}/api/reports/json/{instance_id}"
        
        try:
            download_response = self.session.get(download_url, timeout=30)
            
            if download_response.status_code != 200:
                print(f"❌ Failed to download report: {download_response.status_code}")
                print(f"📄 Response: {download_response.text}")
                return None
            
            report_data = download_response.json()
            print(f"✅ Report downloaded successfully!")
            
            return report_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error downloading report: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON report: {e}")
            return None

    def analyze_report(self, report_data: Dict[str, Any]) -> None:
        """Analyze and display the report results"""
        print(f"\n📊 REPORT ANALYSIS")
        print("=" * 60)
        
        test_summary = report_data.get("test_summary", {})
        print(f"📈 Total documents: {test_summary.get('total_documents', 'N/A')}")
        print(f"✅ Successful: {test_summary.get('successful_documents', 'N/A')}")
        print(f"❌ Failed: {test_summary.get('failed_documents', 'N/A')}")
        print(f"⏰ Timestamp: {test_summary.get('test_timestamp', 'N/A')}")
        
        results = report_data.get("results", [])
        if not results:
            print("❌ No results found in report")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n📄 DOCUMENT {i}")
            print("-" * 40)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue
            
            print(f"🆔 Document ID: {result.get('document_id', 'N/A')}")
            print(f"👤 Patient: {result.get('patient_name', 'N/A')}")
            print(f"📅 Date of Service: {result.get('date_of_service', 'N/A')}")
            print(f"👨‍⚕️ Provider: {result.get('provider', 'N/A')}")
            
            # Enhancement agent results
            enhancement = result.get("enhancement_agent", {})
            if enhancement:
                print(f"\n🤖 Enhancement Agent:")
                print(f"   🎯 Assigned Code: {enhancement.get('assigned_code', 'N/A')}")
                justification = enhancement.get('justification', '')
                print(f"   📝 Justification: {justification[:100]}{'...' if len(justification) > 100 else ''}")
            
            # Auditor agent results
            auditor = result.get("auditor_agent", {})
            if auditor:
                print(f"\n🕵️ Auditor Agent:")
                print(f"   🎯 Final Code: {auditor.get('final_assigned_code', 'N/A')}")
                audit_flags = auditor.get('audit_flags', [])
                print(f"   🚨 Audit Flags: {len(audit_flags)}")
                
                confidence = auditor.get("confidence", {})
                if confidence:
                    print(f"   📊 Confidence Score: {confidence.get('overall_score', 'N/A')}")
                
                # Show first few audit flags
                for j, flag in enumerate(audit_flags[:3], 1):
                    print(f"      {j}. {flag}")
                if len(audit_flags) > 3:
                    print(f"      ... and {len(audit_flags) - 3} more flags")

    def test_health_endpoint(self) -> bool:
        """Test the health endpoint to verify function app is running"""
        print("🏥 Testing health endpoint...")
        health_url = f"{self.function_app_url}/api/health"
        
        try:
            response = self.session.get(health_url, timeout=10)
            if response.status_code == 200:
                print("✅ Health endpoint responded successfully")
                return True
            else:
                print(f"⚠️ Health endpoint returned {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health endpoint failed: {e}")
            return False

    def run_full_test(self, doc_type: str = "problematic", max_wait_time: int = 600) -> None:
        """Run the complete test flow"""
        print("🧪 AZURE DURABLE FUNCTIONS E/M CODING TEST")
        print("=" * 60)
        print(f"🔗 Function App: {self.function_app_url}")
        print(f"📋 Document Type: {doc_type}")
        print(f"⏰ Max Wait Time: {max_wait_time} seconds")
        print(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test health endpoint first
        if not self.test_health_endpoint():
            print("❌ Cannot proceed - health endpoint failed")
            return
        
        # Create test payload
        payload = self.create_test_payload(doc_type)
        
        # Start orchestration
        orchestration_data = self.start_orchestration(payload)
        if not orchestration_data:
            print("❌ Cannot proceed - orchestration failed to start")
            return
        
        instance_id = orchestration_data.get("id")
        status_uri = orchestration_data.get("statusQueryGetUri")
        
        if not status_uri:
            print("❌ Cannot proceed - no status URI returned")
            return
        
        # Poll for completion
        final_status = self.poll_orchestration_status(status_uri, max_wait_time)
        if not final_status:
            print("❌ Test failed - orchestration did not complete")
            return
        
        if final_status.get("runtimeStatus") != "Completed":
            print(f"❌ Test failed - orchestration ended with status: {final_status.get('runtimeStatus')}")
            return
        
        # Download and analyze report
        report_data = self.download_json_report(instance_id)
        if not report_data:
            print("❌ Test failed - could not download report")
            return
        
        self.analyze_report(report_data)
        
        # Save report locally
        filename = f"test_report_{doc_type}_{instance_id[:8]}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report saved to: {filename}")
        print(f"🎉 Test completed successfully!")
        print(f"🕐 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    # UPDATE THIS WITH YOUR FUNCTION APP URL
    FUNCTION_APP_URL = "https://audit-tool-g0bvdmfwgqc7gagu.eastus-01.azurewebsites.net"
    
    if FUNCTION_APP_URL == "https://your-function-app.azurewebsites.net":
        print("⚠️ Please update FUNCTION_APP_URL with your deployed function app URL")
        return
    
    tester = DurableFunctionsTester(FUNCTION_APP_URL)
    
    # Test with problematic documentation (should trigger audit flags)
    tester.run_full_test(doc_type="problematic", max_wait_time=600)
    
    print("\n" + "="*60)
    input("Press Enter to test with good documentation...")
    
    # Test with good documentation (should have high confidence)
    tester.run_full_test(doc_type="good", max_wait_time=600)


if __name__ == "__main__":
    main()
