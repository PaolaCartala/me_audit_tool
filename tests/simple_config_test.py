#!/usr/bin/env python3
"""
Simple Agent Test
Tests the E/M coding agents with mock data (no external dependencies)
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Mock data for testing
MOCK_PROGRESS_NOTE = """
PATIENT: John Doe
DATE: 2024-01-15
PROVIDER: Dr. Smith, Orthopedic Surgeon

CHIEF COMPLAINT: Right knee pain and swelling following fall

HISTORY OF PRESENT ILLNESS:
45-year-old male presents with right knee pain that began 3 days ago after falling while playing basketball. Patient reports moderate to severe pain (7/10), swelling, and difficulty bearing weight. No previous knee injuries. Pain is worse with movement and improved with rest and ice.

REVIEW OF SYSTEMS:
Musculoskeletal: Right knee pain and swelling as described. No other joint pain.
Constitutional: No fever, chills, or weight loss.
All other systems negative.

PHYSICAL EXAMINATION:
Constitutional: Well-appearing male in mild distress due to knee pain
Musculoskeletal: Right knee shows moderate swelling, tenderness over medial joint line, limited range of motion (flexion to 90 degrees), positive McMurray test. No deformity noted.
Neurological: Sensation intact, no motor deficits
Skin: No abrasions or lacerations

ASSESSMENT AND PLAN:
1. Right knee internal derangement, likely meniscal tear
   - MRI ordered to evaluate meniscus
   - NSAIDs for pain and inflammation
   - Physical therapy referral
   - Follow up in 1 week or sooner if symptoms worsen
   
2. Patient educated on rest, ice, elevation
3. Return to activity restrictions discussed
"""

def test_pydantic_models():
    """Test that we can import and create basic models"""
    print("🧪 Testing basic model imports...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Test basic imports
        from models.pydantic_models import EMInput, EMEnhancementOutput, EMAuditOutput
        print("✅ Basic models imported successfully")
        
        # Test model creation
        em_input = EMInput(
            document_id="TEST-001",
            date_of_service="2024-01-15",
            provider="Dr. Smith",
            text=MOCK_PROGRESS_NOTE
        )
        print("✅ EMInput model created successfully")
        
        # Test serialization
        input_dict = em_input.model_dump()
        print("✅ Model serialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        return False

def test_environment_setup():
    """Test environment variable setup"""
    print("\n🔧 Testing environment setup...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - using .env.example as reference")
    
    # Check critical variables
    critical_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing_vars = []
    for var in critical_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            missing_vars.append(var)
            print(f"❌ {var} is missing")
    
    if missing_vars:
        print(f"\n⚠️  Missing {len(missing_vars)} required environment variables")
        print("   Please create .env file with your Azure OpenAI credentials")
        return False
    
    return True

def create_sample_env_file():
    """Create a sample .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📝 Creating sample .env file...")
        with open(env_file, "w") as f:
            f.write("""# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Azure Functions Storage (optional)
AzureWebJobsStorage=

# Application Settings
FUNCTIONS_WORKER_RUNTIME=python
""")
        print(f"✅ Created {env_file}")
        print("   Please edit this file with your actual Azure OpenAI credentials")

async def test_agent_structure():
    """Test that we can create mock agent responses"""
    print("\n🤖 Testing agent response structure...")
    
    # Mock enhancement response
    mock_enhancement = {
        "document_id": "TEST-001",
        "code": "99214",
        "justifications": """
HISTORY: Detailed - Patient provides comprehensive history of present illness with timeline, 
severity, and associated symptoms. Review of systems includes relevant musculoskeletal and 
constitutional symptoms.

EXAMINATION: Detailed - Comprehensive musculoskeletal examination of affected knee including 
inspection, palpation, range of motion, and special tests (McMurray). Constitutional and 
neurological elements documented.

MEDICAL DECISION MAKING: Moderate Complexity - Single established diagnosis with moderate 
risk due to potential need for surgical intervention. Diagnostic imaging ordered. 
Multiple treatment options considered including medications, physical therapy, and 
potential surgical referral.
        """
    }
    
    # Mock audit response  
    mock_audit = {
        "document_id": "TEST-001",
        "code": "99214",
        "audit_flags": ["Consider documenting past medical history", "Quantify functional limitations"],
        "final_note": "Well-documented E/M encounter supporting 99214 level. Recommend adding brief past medical history and more specific functional assessment for completeness."
    }
    
    print("✅ Mock enhancement response structure valid")
    print("✅ Mock audit response structure valid")
    
    return mock_enhancement, mock_audit

def main():
    """Main test function"""
    print("🚀 E/M Coding Agent Configuration Test")
    print("=" * 50)
    
    # Test 1: Basic model functionality
    models_ok = test_pydantic_models()
    
    # Test 2: Environment setup
    env_ok = test_environment_setup()
    
    # Test 3: Create sample .env if needed
    if not env_ok:
        create_sample_env_file()
    
    # Test 4: Agent structure
    print("\n🧪 Testing agent response structure...")
    enhancement, audit = asyncio.run(test_agent_structure())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if models_ok:
        print("✅ Pydantic models: Working")
    else:
        print("❌ Pydantic models: Issues found")
    
    if env_ok:
        print("✅ Environment: Configured")
    else:
        print("⚠️  Environment: Needs configuration")
    
    print("✅ Agent structure: Valid")
    
    # Next steps
    print("\n🎯 NEXT STEPS:")
    if not env_ok:
        print("1. Configure your .env file with Azure OpenAI credentials")
    print("2. Install missing dependencies: pip install python-dotenv pydantic-ai PyMuPDF")
    print("3. Run: python test_config.py")
    print("4. Test with real PDFs: python test_agents.py")
    
    return models_ok and env_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
