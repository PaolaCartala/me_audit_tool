#!/usr/bin/env python3
"""
Simple test runner for E/M Coding Agents
Tests the basic functionality without complex dependencies
"""
import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sample test data
SAMPLE_PROGRESS_NOTE = """
CHIEF COMPLAINT: Right knee pain

HISTORY OF PRESENT ILLNESS:
The patient is a 45-year-old male who presents with a 3-week history of right knee pain. 
The pain began after a fall while playing basketball. The pain is described as a dull ache, 
rated 6/10 in severity, and is worse with weight bearing and climbing stairs. 
The patient denies any locking, giving way, or significant swelling.

PAST MEDICAL HISTORY: Hypertension, controlled on lisinopril
MEDICATIONS: Lisinopril 10mg daily
ALLERGIES: No known drug allergies

PHYSICAL EXAMINATION:
Vital signs: BP 130/80, HR 72, T 98.6°F
Right knee: Mild effusion present, tenderness over medial joint line, 
negative McMurray test, stable to varus/valgus stress, full range of motion

ASSESSMENT AND PLAN:
Right knee medial meniscus tear, probable
- MRI of right knee to confirm diagnosis
- Physical therapy referral
- NSAIDs for pain management
- Follow up in 2 weeks or sooner if symptoms worsen
"""

async def test_enhancement_agent():
    """Test the E/M Enhancement Agent"""
    print("Testing E/M Enhancement Agent...")
    
    try:
        from models.pydantic_models import em_enhancement_agent
        
        user_prompt = f"""
        Document ID: TEST-001
        Date of Service: 2024-01-15
        Provider: Dr. Test Provider
        
        Medical Progress Note:
        {SAMPLE_PROGRESS_NOTE}
        
        Please analyze this orthopedic progress note and assign the most appropriate E/M code (99212, 99213, 99214, or 99215) with detailed justifications.
        """
        
        result = await em_enhancement_agent.run(user_prompt)
        
        print("✅ Enhancement Agent Result:")
        print(f"Code: {result.data.code}")
        print(f"Justifications: {result.data.justifications[:200]}...")
        
        return result.data
        
    except Exception as e:
        print(f"❌ Enhancement Agent Error: {str(e)}")
        return None


async def test_auditor_agent(enhancement_result):
    """Test the E/M Auditor Agent"""
    print("\nTesting E/M Auditor Agent...")
    
    if not enhancement_result:
        print("❌ Cannot test auditor - no enhancement result")
        return None
    
    try:
        from models.pydantic_models import em_auditor_agent
        
        user_prompt = f"""
        Document ID: TEST-001
        Assigned E/M Code: {enhancement_result.code}
        
        Code Justifications:
        {enhancement_result.justifications}
        
        Please audit this enhanced E/M coding assignment for compliance and create the final provider note ready for billing submission.
        """
        
        result = await em_auditor_agent.run(user_prompt)
        
        print("✅ Auditor Agent Result:")
        print(f"Audit Flags: {result.data.audit_flags}")
        print(f"Final Note: {result.data.final_note[:200]}...")
        
        return result.data
        
    except Exception as e:
        print(f"❌ Auditor Agent Error: {str(e)}")
        return None


async def run_full_test():
    """Run the complete test sequence"""
    print("🚀 Starting E/M Coding Agent Tests")
    print("=" * 50)
    
    # Test Enhancement Agent
    enhancement_result = await test_enhancement_agent()
    
    # Test Auditor Agent
    audit_result = await test_auditor_agent(enhancement_result)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if enhancement_result and audit_result:
        print("✅ Both agents completed successfully")
        print(f"Final E/M Code: {enhancement_result.code}")
        print(f"Audit Status: {'Clean' if not audit_result.audit_flags else 'Has flags'}")
        
        # Save results
        results = {
            "test_document": "TEST-001",
            "enhancement": {
                "code": enhancement_result.code,
                "justifications": enhancement_result.justifications
            },
            "audit": {
                "flags": audit_result.audit_flags,
                "final_note": audit_result.final_note
            }
        }
        
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("📁 Results saved to test_results.json")
        
    else:
        print("❌ One or more agents failed")
        print("Check your Azure OpenAI configuration in local.settings.json")


def check_config():
    """Check if the basic configuration is in place"""
    print("🔧 Checking configuration...")
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please configure these in local.settings.json")
        return False
    
    print("✅ Configuration looks good")
    return True


if __name__ == "__main__":
    # Check configuration first
    if not check_config():
        print("\n💡 To configure:")
        print("1. Update local.settings.json with your Azure OpenAI credentials")
        print("2. Make sure you have Azure Functions Core Tools installed")
        print("3. Run: func start")
        sys.exit(1)
    
    # Run the tests
    asyncio.run(run_full_test())
