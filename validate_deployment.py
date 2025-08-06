"""
Pre-deployment Validation Script

This script validates the local environment and dependencies before deploying
to Azure Functions.
"""

import os
import sys
import json
import asyncio
from pathlib import Path


def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False


def check_required_files():
    """Check required files exist"""
    print("\n📁 Checking required files...")
    
    required_files = [
        "requirements.txt",
        "host.json",
        "function_app.py",
        "models/pydantic_models.py",
        "utils/html_processor.py",
        "settings.py",
        "start_orchestration_from_body/__init__.py",
        "em_coding_orchestrator/__init__.py",
        "enhancement_agent_activity/__init__.py",
        "auditor_agent_activity/__init__.py",
        "download_json_report/__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0


def check_environment_variables():
    """Check environment variables"""
    print("\n🔧 Checking environment variables...")
    
    required_env_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if os.getenv(var):
            print(f"✅ {var} - Set")
        else:
            print(f"❌ {var} - NOT SET")
            missing_vars.append(var)
    
    return len(missing_vars) == 0


def check_host_json():
    """Check host.json configuration"""
    print("\n⚙️ Checking host.json...")
    
    try:
        with open("host.json", "r") as f:
            host_config = json.load(f)
        
        # Check extensions
        extensions = host_config.get("extensions", {})
        if "durableTask" in extensions:
            print("✅ durableTask extension configured")
        else:
            print("❌ durableTask extension missing")
            return False
        
        # Check function timeout
        function_timeout = host_config.get("functionTimeout", "00:05:00")
        print(f"⏰ Function timeout: {function_timeout}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading host.json: {e}")
        return False


def check_requirements():
    """Check requirements.txt"""
    print("\n📦 Checking requirements.txt...")
    
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        required_packages = [
            "azure-functions",
            "azure-durable-functions",
            "pydantic",
            "beautifulsoup4",
            "python-dotenv"
        ]
        
        missing_packages = []
        for package in required_packages:
            if package.lower() in requirements.lower():
                print(f"✅ {package}")
            else:
                print(f"❌ {package} - Missing from requirements.txt")
                missing_packages.append(package)
        
        return len(missing_packages) == 0
        
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False


async def test_local_imports():
    """Test that all imports work locally"""
    print("\n🔍 Testing local imports...")
    
    try:
        print("   Testing azure.functions...")
        import azure.functions as func
        print("   ✅ azure.functions")
        
        print("   Testing azure.durable_functions...")
        import azure.durable_functions as df
        print("   ✅ azure.durable_functions")
        
        print("   Testing pydantic models...")
        from models.pydantic_models import EMInput, em_enhancement_agent, em_auditor_agent
        print("   ✅ pydantic models")
        
        print("   Testing html processor...")
        from utils.html_processor import parse_payload_to_eminput
        print("   ✅ html processor")
        
        print("   Testing settings...")
        from settings import logger
        print("   ✅ settings")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False


def check_function_structure():
    """Check function structure"""
    print("\n🏗️ Checking function structure...")
    
    function_dirs = [
        "start_orchestration_from_body",
        "em_coding_orchestrator", 
        "enhancement_agent_activity",
        "auditor_agent_activity",
        "download_json_report",
        "excel_export_activity",
        "health"
    ]
    
    all_good = True
    for func_dir in function_dirs:
        init_file = Path(func_dir) / "__init__.py"
        function_file = Path(func_dir) / "function.json"
        
        if init_file.exists():
            print(f"✅ {func_dir}/__init__.py")
        else:
            print(f"❌ {func_dir}/__init__.py - MISSING")
            all_good = False
        
        if function_file.exists():
            print(f"✅ {func_dir}/function.json")
        else:
            print(f"⚠️ {func_dir}/function.json - May be missing (check if needed)")
    
    return all_good


async def main():
    """Run all validation checks"""
    print("🔍 PRE-DEPLOYMENT VALIDATION")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Required Files", check_required_files()),
        ("Environment Variables", check_environment_variables()),
        ("host.json", check_host_json()),
        ("requirements.txt", check_requirements()),
        ("Local Imports", await test_local_imports()),
        ("Function Structure", check_function_structure())
    ]
    
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("✅ Ready for deployment to Azure!")
        print("\nNext steps:")
        print("1. Run: func azure functionapp publish <your-function-app-name>")
        print("2. Test with: python test_simple.py")
    else:
        print("\n❌ Some validation checks failed!")
        print("Please fix the issues above before deploying.")
        
        # Suggest fixes
        print("\n💡 Common fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Set environment variables in .env file")
        print("- Check Azure OpenAI credentials")


if __name__ == "__main__":
    asyncio.run(main())
