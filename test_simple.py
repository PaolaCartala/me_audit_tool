"""
Simple Azure Functions Test Script

Test the E/M coding durable functions with minimal complexity.
Update FUNCTION_APP_URL with your deployed function app URL.
"""

import requests
import json
import time
from datetime import datetime


# UPDATE THIS WITH YOUR DEPLOYED FUNCTION APP URL
FUNCTION_APP_URL = "https://your-function-app.azurewebsites.net"


def create_simple_test_payload():
    """Create a simple test payload"""
    return {
        "document": {
            "id": f"SIMPLE_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "Simple Test Note",
            "patientName": "Test, Patient",
            "PatientId": "TEST-123",
            "provider": "Dr. Test",
            "DateOfService": "2025-01-06 12:00:00.000",
            "CreatedBy": "Dr. Test",
            "creationDate": "2025-01-06 12:00:00.000",
            "fileType": "text",
            "fileContent": {
                "encoding": "text",
                "data": """<div>
<p><strong>CHIEF COMPLAINT:</strong></p>
<p>Follow-up visit for diabetes and hypertension.</p>

<p><strong>HISTORY OF PRESENT ILLNESS:</strong></p>
<p>Patient is a 65-year-old male with type 2 diabetes and hypertension. Blood sugars have been well controlled on metformin. Blood pressure readings at home average 130/80. Patient reports feeling well with no specific complaints today.</p>

<p><strong>PHYSICAL EXAMINATION:</strong></p>
<p><strong>Vital Signs:</strong> BP 132/78, HR 72, Weight 180 lbs</p>
<p><strong>General:</strong> Well-appearing male in no distress</p>
<p><strong>Cardiovascular:</strong> Regular rate and rhythm, no murmurs</p>

<p><strong>ASSESSMENT AND PLAN:</strong></p>
<p><strong>1. Type 2 Diabetes Mellitus - well controlled</strong><br/>
- Continue metformin 1000mg twice daily<br/>
- Recheck HbA1c in 3 months</p>

<p><strong>2. Hypertension - well controlled</strong><br/>
- Continue lisinopril 10mg daily<br/>
- Continue home monitoring</p>

<p><strong>TIME:</strong> 25 minutes face-to-face</p>
</div>"""
            }
        }
    }


def test_health():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{FUNCTION_APP_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.text}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def start_orchestration(payload):
    """Start the orchestration"""
    print(f"\n🚀 Starting orchestration...")
    print(f"📄 Document ID: {payload['document']['id']}")
    
    try:
        response = requests.post(
            f"{FUNCTION_APP_URL}/api/orchestrations",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 202:
            data = response.json()
            instance_id = data.get("id")
            status_uri = data.get("statusQueryGetUri")
            print(f"✅ Orchestration started!")
            print(f"🆔 Instance ID: {instance_id}")
            return instance_id, status_uri
        else:
            print(f"❌ Failed to start: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error starting orchestration: {e}")
        return None, None


def wait_for_completion(status_uri, max_wait=300):
    """Wait for orchestration to complete"""
    print(f"\n⏳ Waiting for completion (max {max_wait} seconds)...")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(status_uri, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get("runtimeStatus")
                
                if status != last_status:
                    print(f"📈 Status: {status}")
                    last_status = status
                
                if status == "Completed":
                    print(f"✅ Completed! Total time: {time.time() - start_time:.1f}s")
                    return data
                elif status in ["Failed", "Canceled", "Terminated"]:
                    print(f"❌ Failed with status: {status}")
                    print(f"📄 Details: {json.dumps(data, indent=2)}")
                    return data
            
            time.sleep(5)
            
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
            time.sleep(5)
    
    print(f"⏰ Timeout after {max_wait} seconds")
    return None


def download_report(instance_id):
    """Download the JSON report"""
    print(f"\n📥 Downloading report for {instance_id}...")
    
    try:
        response = requests.get(
            f"{FUNCTION_APP_URL}/api/reports/json/{instance_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            report = response.json()
            print(f"✅ Report downloaded successfully!")
            
            # Save to file
            filename = f"test_report_{instance_id[:8]}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"💾 Saved to: {filename}")
            
            # Show summary
            summary = report.get("test_summary", {})
            print(f"\n📊 Summary:")
            print(f"   Documents: {summary.get('total_documents')}")
            print(f"   Successful: {summary.get('successful_documents')}")
            print(f"   Failed: {summary.get('failed_documents')}")
            
            results = report.get("results", [])
            if results and "error" not in results[0]:
                result = results[0]
                enhancement = result.get("enhancement_agent", {})
                auditor = result.get("auditor_agent", {})
                
                print(f"\n📋 Results:")
                print(f"   Enhancement Code: {enhancement.get('assigned_code')}")
                print(f"   Final Code: {auditor.get('final_assigned_code')}")
                print(f"   Audit Flags: {len(auditor.get('audit_flags', []))}")
                print(f"   Confidence: {auditor.get('confidence', {}).get('overall_score', 'N/A')}")
            
            return report
        else:
            print(f"❌ Download failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None


def main():
    print("🧪 SIMPLE AZURE FUNCTIONS TEST")
    print("=" * 50)
    
    if FUNCTION_APP_URL == "https://your-function-app.azurewebsites.net":
        print("⚠️ Please update FUNCTION_APP_URL in the script!")
        return
    
    print(f"🔗 Function App: {FUNCTION_APP_URL}")
    
    # Test health
    if not test_health():
        print("❌ Cannot proceed - health check failed")
        return
    
    # Create payload and start orchestration
    payload = create_simple_test_payload()
    instance_id, status_uri = start_orchestration(payload)
    
    if not instance_id:
        print("❌ Cannot proceed - orchestration failed to start")
        return
    
    # Wait for completion
    final_status = wait_for_completion(status_uri, max_wait=300)
    
    if not final_status:
        print("❌ Test failed - timeout or error")
        return
    
    if final_status.get("runtimeStatus") != "Completed":
        print("❌ Test failed - orchestration did not complete successfully")
        return
    
    # Download report
    report = download_report(instance_id)
    
    if report:
        print(f"\n🎉 Test completed successfully!")
    else:
        print(f"\n❌ Test failed - could not download report")


if __name__ == "__main__":
    main()
